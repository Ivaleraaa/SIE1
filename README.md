# SIE1
Projet de SIE n°1


9. La Tulipe : Commande à Table  
Objectif : Permettre aux clients de commander depuis leur table.  
Idée :  
Associer un QR code à chaque table, redirigeant vers une interface de commande.  
Permettre aux clients de choisir parmi les bières et les formats disponibles.  
Envoyer la commande directement à la caisse Odoo.  
Amélioration : Ajouter un système de paiement en ligne pour éviter les files d’attente.  



MDP :SIE1  
email : mm

# Comment run le projet ?
```bash
docker compose up -d
```
L'interface pdv se trouve en http://localhost:8069/web#action=372&model=pos.config&view_type=kanban&cids=1&menu_id=213  
Il faut ouvrir une session bar.

# Comment lancer le flask ?
Afin qu'il marche sur MacOs : flask --app cmd:app run --port 8000 (le port 5000 est déjà attribué)  
Sinon, : flask --app cmd:app run

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