# SIE1
Projet de SIE n°1


9. La Tulipe : Commande à Table  
Objectif : Permettre aux clients de commander depuis leur table.  
Idée :  
Associer un QR code à chaque table, redirigeant vers une interface de commande.  
Permettre aux clients de choisir parmi les bières et les formats disponibles.  
Envoyer la commande directement à la caisse Odoo.    

A propos de la configuration du Odoo :   
IL est impératif d'avoir les bières crées dans les produits que propose le bar. Sinon, le service ne fonctionnera pas.  
Dans le module point de vente, il faut avoir coché la case "est un bar / restaurant" dans les paramètres du module, afin que chaque commande ait une table associée. Aussi, il faut bien que les tables aient un simple numéro comme nom, et non "T1", "T2" ou autre. Pour changer cela, il faut modifier le plan de la salle dans les paramètres du module.  

Afin que le projet puisse fonctionner, il faut créer une session bar/restaurant, et qu'elle soit active.

MDP :SIE1  
email : mm


# Comment run le projet ?
```bash
docker compose up -d
```
L'interface pdv se trouve en http://localhost:8069/web#action=372&model=pos.config&view_type=kanban&cids=1&menu_id=213  
Il faut ouvrir une session bar.

# Comment lancer le flask ?
`flask --app cmd:app run --port 8000`  


Pour faire un test de requête Odoo : 
```bash
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d '{
    "idtable": 4,
    "bieres": [
      {
        "quantité": null,
        "persistenceId_string": "rousse"
      }
    ]
  }' -v
  ```

Maintenant, il est possible de lancer Bonita afin d'executer le formulaire.