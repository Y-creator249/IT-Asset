#!/usr/bin/env python3
"""
Script pour initialiser manuellement les journaux et comptes comptables
pour le module it_asset_management.

Exécution:
    python -m odoo.addons.it_asset_management.scripts.init_accounting
    
    ou bien
    
    cd /chemin/vers/odoo
    ./odoo-bin shell -d [database_name] -c [config_file]
    
    # Puis dans la console Python:
    >>> from odoo.addons.it_asset_management.scripts.init_accounting import init_accounting
    >>> init_accounting(env)
"""

import logging
_logger = logging.getLogger(__name__)

def init_accounting(env):
    """Initialiser les journaux et comptes comptables"""
    print("Initialisation des journaux et comptes comptables...")
    
    # Essayer de créer un journal de vente
    journal = None
    journal_obj = env['account.journal'].sudo()
    
    # Chercher un journal de vente existant
    journal = journal_obj.search([('type', '=', 'sale')], limit=1)
    if journal:
        print(f"Journal de vente existant trouvé: {journal.name} ({journal.code})")
    else:
        # Essayer différents codes
        codes = ['SALE', 'VTE', 'VITJ', 'S001', 'S002', 'S003', 'S004', 'S005']
        for code in codes:
            existing = journal_obj.search([('code', '=', code)], limit=1)
            if not existing:
                try:
                    journal = journal_obj.create({
                        'name': 'Ventes',
                        'code': code,
                        'type': 'sale',
                        'company_id': env.company.id,
                    })
                    print(f"Journal de vente créé: {journal.name} ({journal.code})")
                    env.cr.commit()
                    break
                except Exception as e:
                    print(f"Erreur lors de la création du journal {code}: {str(e)}")
    
    if not journal:
        print("ERREUR: Impossible de créer un journal de vente!")
    
    # Essayer de trouver/créer un compte de revenus
    account = None
    account_obj = env['account.account'].sudo()
    
    # Chercher via les propriétés par défaut
    account = env['ir.property'].sudo()._get('property_account_income_id', 'product.template')
    if account:
        print(f"Compte de revenus trouvé via property_account_income_id: {account.code} - {account.name}")
    else:
        account = env['ir.property'].sudo()._get('property_account_income_categ_id', 'product.category')
        if account:
            print(f"Compte de revenus trouvé via property_account_income_categ_id: {account.code} - {account.name}")
    
    # Chercher des comptes standards
    if not account:
        searches = [
            ('706000', 'Prestations de services'),
            ('707000', 'Ventes de produits'),
            ('700000', 'Ventes'),
            ('709000', 'Revenus divers'),
            ('70%', 'Comptes commençant par 70')
        ]
        
        for code, desc in searches:
            account = account_obj.search([('code', 'like', code), ('deprecated', '=', False)], limit=1)
            if account:
                print(f"Compte de revenus trouvé ({desc}): {account.code} - {account.name}")
                break
    
    # Chercher par type de compte
    if not account:
        account = account_obj.search([
            ('user_type_id.type', '=', 'other'),
            ('user_type_id.name', 'ilike', 'income'),
            ('deprecated', '=', False)
        ], limit=1)
        if account:
            print(f"Compte de revenus trouvé via type: {account.code} - {account.name}")
    
    # En dernier recours, essayer de créer un compte
    if not account:
        account_type = env.ref('account.data_account_type_revenue', raise_if_not_found=False)
        if not account_type:
            account_type = env.ref('account.data_account_type_other_income', raise_if_not_found=False)
        
        if account_type:
            codes = [('706000', 'Prestations de services'), ('707000', 'Ventes de produits'), 
                    ('700000', 'Ventes'), ('709000', 'Revenus divers')]
            
            for code, name in codes:
                try:
                    existing = account_obj.search([('code', '=', code)], limit=1)
                    if not existing:
                        account = account_obj.create({
                            'code': code,
                            'name': name,
                            'user_type_id': account_type.id,
                            'company_id': env.company.id,
                        })
                        print(f"Compte de revenus créé: {code} - {name}")
                        env.cr.commit()
                        break
                except Exception as e:
                    print(f"Erreur lors de la création du compte {code}: {str(e)}")
    
    if not account:
        print("ERREUR: Impossible de trouver/créer un compte de revenus!")
    
    return {
        'journal': journal,
        'account': account
    }

# Si exécuté directement
if __name__ == "__main__":
    # Quand exécuté comme script indépendant
    import sys
    import os
    
    # Ajouter le répertoire parent au path pour permettre l'import d'Odoo
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))
    
    # Tentative d'importation d'Odoo
    try:
        from odoo import api, SUPERUSER_ID
        from odoo.tools import config
        import odoo
    except ImportError:
        print("Erreur: Impossible d'importer Odoo. Assurez-vous que le script est exécuté depuis le répertoire odoo.")
        sys.exit(1)
    
    # Configuration de la base de données
    dbname = sys.argv[1] if len(sys.argv) > 1 else 'odoo'
    
    # Initialisation de l'environnement Odoo
    odoo.tools.config.parse_config(['--workers=0', '--log-level=info'])
    registry = odoo.registry(dbname)
    
    with api.Environment.manage(), registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        result = init_accounting(env)
        
        if result['journal'] and result['account']:
            print("\nInitialisation réussie!")
        else:
            print("\nInitialisation partiellement réussie ou échouée.") 