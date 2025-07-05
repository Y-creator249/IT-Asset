PROBLÈME : "Aucun journal de vente n'a été trouvé"
=============================================

Si vous rencontrez l'erreur "Aucun journal de vente n'a été trouvé" lors de la création d'une facture,
voici plusieurs solutions pour résoudre ce problème:

SOLUTION 1 : Créer un journal de vente via l'interface
-----------------------------------------------------
1. Connectez-vous à Odoo avec un compte administrateur
2. Allez dans: Comptabilité > Configuration > Journaux comptables
3. Cliquez sur "Créer"
4. Configurez comme suit:
   - Nom: Ventes
   - Code court: SALE
   - Type: Ventes
5. Enregistrez

SOLUTION 2 : Exécuter le script SQL fourni
-----------------------------------------
1. Accédez à votre serveur PostgreSQL
2. Exécutez le script SQL suivant sur votre base de données Odoo:
   
   ```sql
   psql -U odoo -d votre_base_de_donnees -f create_journal.sql
   ```

SOLUTION 3 : Forcer l'initialisation depuis l'interface Odoo
-----------------------------------------------------------
1. Allez dans Applications > Mettre à jour la liste des applications
2. Recherchez "IT Asset Management"
3. Cliquez sur "Mettre à jour" pour réinstaller le module

Si malgré ces solutions le problème persiste, contactez votre administrateur système. 