from flask import Flask, request, jsonify
import xmlrpc.client
import re
import json
import random

app = Flask("Beer manager")

# Détails connexion Odoo, définis lors de la creation d'odoo et dans le docker compose
odoo_url = "http://localhost:8069"
db_name = "postgres2"
username = "mm"
password = "SIE1"

# Connexion XML-RPC, récupérée depuis l'exemple du cours
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


@app.route('/', methods=['POST']) # pas de route spécifique étant donné qu'il n'y en a qu'une seule
def ajouter_bieres():

    raw = request.get_data(as_text=True)
    data = parse_custom_string_to_json(raw)
    print(f"Received data before : {raw}")
    print(f"Received data: {data}")
    try:
        data = json.loads(data)
    except json.JSONDecodeError as e:
        return jsonify({'error': f'Erreur de parsing JSON : {e}'}), 400

    table_id = data.get('idtable')
    bieres = data.get('bieres', [])

    if not table_id or not bieres:
        return jsonify({'error': 'ID table ou bières manquants'}), 400

    try:
        # Session POS active
        session_ids = models.execute_kw(db_name, uid, password,
            'pos.session', 'search',
            [[['state', '=', 'opened']]],
            {'limit': 1})
        
        if not session_ids:
            return jsonify({'error': 'Aucune session POS ouverte'}), 500

        session_id = session_ids[0]

        # Vérifier la commande POS liée à la table
        order_ids = models.execute_kw(db_name, uid, password,
            'pos.order', 'search',
            [[
                ['table_id', '=', table_id],
                ['session_id', '=', session_id],
                ['state', '=', 'draft']
            ]],
            {'limit': 1})

        # Si aucune commande existante, en créer une nouvelle
        if not order_ids:
            reference = generate_odoo_pos_reference()
            order_id = models.execute_kw(db_name, uid, password,
                'pos.order', 'create',
                [{
                    'session_id': session_id,
                    'table_id': table_id,
                    'amount_tax': 0.0,
                    'amount_total': 0.0,
                    'amount_paid': 0.0,
                    'amount_return': 0.0,
                    'pos_reference': reference
                }])
        else:
            order_id = order_ids[0]

        # Ajouter les bières avec product.product
        for biere in bieres:
            name = biere.get('persistenceId_string')
            if not name:
                continue

            product_ids = models.execute_kw(db_name, uid, password,
                'product.product', 'search',
                [[['name', 'ilike', name]]], {'limit': 1})
            
            if not product_ids:
                return jsonify({'error': f'Produit "{name}" introuvable'}), 400

            product_id = product_ids[0]

            # lire infos produit pour le prix et les taxes
            product_data = models.execute_kw(db_name, uid, password,
                'product.product', 'read',
                [product_id], {'fields': ['lst_price', 'taxes_id']})

            price_unit = product_data[0]['lst_price']
            taxes = product_data[0].get('taxes_id', [])

            # ajouter ligne de commande point de vente
            models.execute_kw(db_name, uid, password,
                'pos.order.line', 'create',
                [{
                    'order_id': order_id,
                    'product_id': product_id,
                    'qty': 1.0,
                    'price_unit': price_unit,
                    'tax_ids': [(6, 0, taxes)],
                    'price_subtotal': price_unit,             
                    'price_subtotal_incl': price_unit         
                }])

        return jsonify({'success': True, 'commande_id': order_id}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500



# Etant donné que bonita nous envoie un objet java, nous avons du le recupérer sous forme de texte puis le formater manuellement en json grace à différentes regex

def parse_custom_string_to_json(input_str):
    input_str = re.sub(r'(\w+):', r'"\1":', input_str)
    input_str = re.sub(r':\s*([a-zA-Z_]+)(?=[,\]\}])', r': "\1"', input_str)
    input_str = re.sub(r':\s*(?=[,\]\}])', r': null', input_str)
    input_str = re.sub(r'\[\s*("quantité":.*?"persistenceId_string":.*?)(?=\])\]', r'{\1}', input_str)
    input_str = re.sub(r'\[\s*\{', '[{', input_str)
    input_str = re.sub(r'\}\s*,\s*\{', '},{', input_str)
    input_str = re.sub(r'\}\s*\]', '}]', input_str)

    if input_str.startswith('[') and input_str.endswith(']'):
        input_str = '{' + input_str[1:-1] + '}'

    return input_str

# Odoo POS a besoin d'une référence sinon ça cause une erreur dans odoo. Pour réparer ça, voilà la référence.
def generate_odoo_pos_reference():
    return f"{random.randint(10000,99999)}-{random.randint(100,999)}-{random.randint(1000,9999)}"


if __name__ == '__main__':
    app.run(debug=True)
