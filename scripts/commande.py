from flask import Flask, request, jsonify
import xmlrpc.client
import re
import json

app = Flask("Beer manager")

# Détails connexion odoo
odoo_url = "http://localhost:8069"  # serv odoo
db_name = "postgres2"               # Nom de la base de données
username = "mm"                     # Nom d'utilisateur
password = "SIE1"                   # Mot de passe

# Connexion via XML-RPC à Odoo
common = xmlrpc.client.ServerProxy(f"{odoo_url}/xmlrpc/2/common")
models = xmlrpc.client.ServerProxy(f"{odoo_url}/xmlrpc/2/object")

# Authentification
try:
    uid = common.authenticate(db_name, username, password, {})
    if not uid:
        print("Authentication failed!")
        exit(1)
    print(f"Authenticated! User ID: {uid}")
except Exception as e:
    print(f"Failed to authenticate: {e}")
    exit(1)

def jmap2dict(jmap: str) -> dict:
    s = re.sub(r"([a-zA-Z_é0-9]*)",r"'\1'", jmap)
    s = re.sub(r"\]","}", s)
    s = re.sub(r"\[","{", s)
    print(s)
    return json.load(s)

@app.route('/test', methods=['GET'])
def test():
    return jsonify({'message': 'Test endpoint is working!'})


@app.route('/', methods=['POST'])
def commander_bieres():
    try:
        # Parsing du JSON brut envoyé dans le body
        raw = request.get_data(as_text=True)
        data = parse_custom_string_to_json(raw)
        data = json.loads(data)

        table_id = data.get('idtable')
        bieres = data.get('bieres', [])

        if not table_id or not isinstance(bieres, list):
            return jsonify({'error': 'Requête invalide'}), 400

        # Compter les bières
        compteur = {}
        for biere in bieres:
            nom = biere.get('persistenceId_string')
            if nom:
                compteur[nom] = compteur.get(nom, 0) + 1

        total = 0.0
        order_lines = []

        for nom_biere, quantite in compteur.items():
            product_data = models.execute_kw(
                db_name, uid, password,
                'product.product', 'search_read',
                [[['name', '=', nom_biere]]],
                {'fields': ['id', 'lst_price'], 'limit': 1}
            )

            if not product_data:
                return jsonify({'error': f"Produit '{nom_biere}' introuvable"}), 404

            product = product_data[0]
            product_id = product['id']
            prix_unitaire = product['lst_price']

            total += prix_unitaire * quantite

            order_lines.append([0, 0, {
                'product_id': product_id,
                'qty': quantite,
                'price_unit': prix_unitaire
            }])


        ensure_pos_config_has_sequence(session_id=3)
        # Création de la commande POS
        order_id = models.execute_kw(
            db_name, uid, password,
            'pos.order', 'create',
            [{
                'session_id': 3,
                'table_id': table_id,
                'lines': order_lines,
                'amount_total': total,
                'amount_tax': 0.0,
                'amount_paid': total,
                'amount_due': 0.0,
                'amount_return': 0.0,
                'partner_id': False,
                'pricelist_id': 1,
                'state': 'paid',
                'company_id': 1
            }]
        )

        return jsonify({'success': True, 'order_id': order_id})

    except Exception as e:
        print(f"Erreur lors de la commande : {e}")
        return jsonify({'error': 'Erreur lors de la commande'}), 500

if __name__ == '__main__':
    app.run(debug=True)
    # print("Requête reçue !")
    # print("Headers:", dict(request.headers))
    # print("JSON brut :", request.get_data(as_text=True))
    # try:
        
    #     print("Données JSON :", data)
    #     return {"status": "ok"}, 200
    # except Exception as e:
    #     print("Erreur lors du parsing JSON :", e)
    #     return {"status": "error", "message": str(e)}, 400





def parse_custom_string_to_json(input_str):
    # Étape 1 : Entourer les clés de guillemets
    input_str = re.sub(r'(\w+):', r'"\1":', input_str)

    # Étape 2 : Entourer les valeurs non numériques ni null de guillemets (comme "brune")
    input_str = re.sub(r':\s*([a-zA-Z_]+)(?=[,\]\}])', r': "\1"', input_str)

    # Étape 3 : Remplacer les champs vides par null
    input_str = re.sub(r':\s*(?=[,\]\}])', r': null', input_str)

    # Étape 4 : Corriger les doubles crochets [[...]] => [{...}]
    input_str = re.sub(r'\[\s*\[', '[{', input_str)
    input_str = re.sub(r'\]\s*\]', '}]', input_str)

    # Étape 5 : Ajouter les accolades extérieures si c’est un objet global
    if input_str.startswith('[') and input_str.endswith(']'):
        input_str = '{' + input_str[1:-1] + '}'

    try:
        parsed_json = json.loads(input_str)
        return json.dumps(parsed_json, indent=2)
    except json.JSONDecodeError as e:
        return f"Données JSON : Erreur lors de la conversion en JSON : {e}\nString traitée : {input_str}"
    


def ensure_pos_config_has_sequence(session_id):
    # Lire la session
    session_data = models.execute_kw(
        db_name, uid, password,
        'pos.session', 'read',
        [[session_id]],
        {'fields': ['config_id']}
    )

    if not session_data or not session_data[0].get('config_id'):
        raise Exception("La session POS n'est pas liée à une configuration.")

    config_id = session_data[0]['config_id'][0]
    print(f"→ Configuration trouvée : ID {config_id}")

    # Lire la configuration POS
    config_data = models.execute_kw(
        db_name, uid, password,
        'pos.config', 'read',
        [[config_id]],
        {'fields': ['sequence_id']}
    )

    sequence_id = config_data[0]['sequence_id'][0] if config_data[0]['sequence_id'] else None

    if sequence_id:
        print(f"→ Séquence existante : ID {sequence_id} ✅")
        return

    print("⚠️  Aucune séquence liée à la configuration. Création d'une séquence...")

    # Créer une séquence
    sequence_id = models.execute_kw(
        db_name, uid, password,
        'ir.sequence', 'create',
        [{
            'name': 'Séquence PdV Auto',
            'implementation': 'no_gap',
            'prefix': 'POS/',
            'padding': 4,
            'number_next': 1,
            'number_increment': 1
        }]
    )

    print(f"→ Séquence créée avec ID {sequence_id} 🎉")

    # Lier la séquence à la configuration
    models.execute_kw(
        db_name, uid, password,
        'pos.config', 'write',
        [[config_id], {'sequence_id': sequence_id}]
    )

    print("→ Séquence liée à la configuration POS avec succès ✅")

if __name__ == "__main__":
    # Assurez-vous que la fonction est appelée avec un ID de session valide
    ensure_pos_config_has_sequence(session_id=3)
    app.run(debug=True)