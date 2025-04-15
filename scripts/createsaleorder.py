import xmlrpc.client

# Détails de connexion à Odoo
odoo_url = "http://localhost:8069"  # Remplacez par l'URL de votre serveur Odoo
db_name = "demo-test"               # Remplacez par le nom de votre base de données
username = "amansabrina.ossey@gmail.com"  # Remplacez par votre nom d'utilisateur
password = "odoo"                  # Remplacez par votre mot de passe

# Créer un client XML-RPC pour le point de terminaison commun
common = xmlrpc.client.ServerProxy(f"{odoo_url}/xmlrpc/2/common")

# Authentification avec Odoo
try:
    uid = common.authenticate(db_name, username, password, {})
    if not uid:
        print("❌ Authentication failed!")
        exit(1)
    print(f"✅ Authenticated! User ID: {uid}")
except Exception as e:
    print(f"❌ Failed to authenticate: {e}")
    exit(1)

# Créer un client XML-RPC pour le point de terminaison objet
models = xmlrpc.client.ServerProxy(f"{odoo_url}/xmlrpc/2/object")

# Fonction pour obtenir l'ID d'un partenaire (client)
def get_customer_id(models, db_name, uid, password, name):
    search_criteria = [["name", "=", name]]
    customer_ids = models.execute_kw(db_name, uid, password,
                                     "res.partner", "search", [search_criteria], {"limit": 1})
    return customer_ids[0] if customer_ids else None

# Fonction pour obtenir l'ID d'un produit
def get_product_id(models, db_name, uid, password, product_name):
    search_criteria = [["name", "=", product_name]]
    product_ids = models.execute_kw(db_name, uid, password,
                                    "product.product", "search", [search_criteria], {"limit": 1})
    return product_ids[0] if product_ids else None

# Définir le nom du client
customer_name = "Azure Interior"  # Changez selon vos besoins
customer_id = get_customer_id(models, db_name, uid, password, customer_name)
if not customer_id:
    print(f"❌ Customer '{customer_name}' not found!")
    exit(1)
print(f"✅ Customer found: ID {customer_id}")

# Définir les produits
products = [
    {"name": "Cabinet with Doors", "quantity": 2, "price": 150.0},
    {"name": "Large Desk", "quantity": 1, "price": 300.0}
]

# Préparer les lignes de commande
order_lines = []
for product in products:
    product_id = get_product_id(models, db_name, uid, password, product["name"])
    if not product_id:
        print(f"❌ Product '{product['name']}' not found!")
        exit(1)
    print(f"✅ Product '{product['name']}' found: ID {product_id}")

    order_lines.append((0, 0, {
        "product_id": product_id,
        "product_uom_qty": product["quantity"],
        "price_unit": product["price"]
    }))

# Créer la commande de vente
try:
    order_data = {
        "partner_id": customer_id,
        "order_line": order_lines
    }

    sale_order_id = models.execute_kw(db_name, uid, password,
                                      "sale.order", "create", [order_data])

    print(f"✅ Sales Order Created: ID {sale_order_id}")

    # Confirmer la commande de vente
    models.execute_kw(db_name, uid, password,
                      "sale.order", "action_confirm", [[sale_order_id]])

    print("✅ Sales Order Confirmed!")
except Exception as e:
    print(f"❌ Error creating order: {e}")