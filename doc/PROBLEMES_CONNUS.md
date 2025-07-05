# Problèmes connus et solutions

## Erreur: "Aucun journal de vente n'a été trouvé"

Si vous rencontrez l'erreur "Aucun journal de vente n'a été trouvé" lors de la génération de factures, voici plusieurs solutions possibles:

### Solution 1: Mise à jour du module

```bash
python -m odoo -d <nom_base> -u it_asset_management
```

Cette commande devrait déclencher l'installation du journal de vente par défaut via le fichier `journal_data.xml`.

### Solution 2: Créer un journal manuellement

1. Allez dans Comptabilité > Configuration > Journaux comptables
2. Cliquez sur "Créer"
3. Renseignez les informations suivantes:
   - Nom: Ventes
   - Code: SALE
   - Type: Ventes
   - Cochez "Actif"
4. Sauvegardez

### Solution 3: Utiliser le script Python

```bash
# À exécuter depuis la racine d'Odoo
python -m odoo shell -d <nom_base> --no-http -c <fichier_config> < addons/it_asset_management/scripts/fix_journal.py
```

### Solution 4: Utiliser le script SQL

Si vous avez accès direct à la base de données:

```bash
psql -U <utilisateur> -d <nom_base> -f addons/it_asset_management/scripts/fix_journal.sql
```

## Autres problèmes connus

### Erreur 403 Forbidden dans le portail client

Si les clients rencontrent une erreur 403 lors de l'accès aux contrats ou factures via le portail, assurez-vous que:
1. Les règles de sécurité dans `security_rules.xml` sont correctement configurées
2. Les droits d'accès dans `ir.model.access.csv` incluent les droits en lecture pour le groupe "portal"

### Champ "type_id" manquant sur les équipements

Si vous ne pouvez pas créer d'équipements car le champ "type_id" est manquant, mettez à jour le module pour installer les types d'équipement par défaut. 