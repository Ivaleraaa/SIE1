from flask import Flask, request, jsonify
import xmlrpc.client

app = Flask("Beer manager")

# # Détails connexion odoo
# odoo_url = "http://localhost:8069"  # serv odoo
# db_name = "postgres2"               # Nom de la base de données
# username = "mm"                     # Nom d'utilisateur
# password = "SIE1"                   # Mot de passe

# # Connexion via XML-RPC à Odoo
# common = xmlrpc.client.ServerProxy(f"{odoo_url}/xmlrpc/2/common")
# models = xmlrpc.client.ServerProxy(f"{odoo_url}/xmlrpc/2/object")

# # Authentification
# try:
#     uid = common.authenticate(db_name, username, password, {})
#     if not uid:
#         print("❌ Authentication failed!")
#         exit(1)
#     print(f"✅ Authenticated! User ID: {uid}")
# except Exception as e:
#     print(f"❌ Failed to authenticate: {e}")
#     exit(1)


@app.route('/', methods=['POST'])
def commander_bieres():
    print("Requête reçue !")
    print("Headers:", dict(request.headers))
    print("JSON brut :", request.get_data(as_text=True))
    
    data = request.get_json()
    print("Données JSON :", data)


    # (le reste de ton traitement ici...)
    return jsonify({"status": "ok"})