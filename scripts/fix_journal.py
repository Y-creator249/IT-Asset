#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de réparation pour le problème de journal de vente manquant.
À exécuter depuis la racine d'Odoo:
python -m odoo shell -d <nom_base> --no-http -c <fichier_config> < addons/it_asset_management/scripts/fix_journal.py
"""

import logging
_logger = logging.getLogger(__name__)

def fix_sales_journal():
    """Créer un journal de vente s'il n'existe pas déjà"""
    # Vérifier si un journal de vente existe déjà
    env = env  # Accès à l'environnement Odoo dans le shell
    
    print("Recherche de journaux de vente existants...")
    journals = env['account.journal'].sudo().search([('type', '=', 'sale')])
    if journals:
        for journal in journals:
            print(f"Journal de vente trouvé: {journal.name} [{journal.code}]")
        return journals[0]
    
    print("Aucun journal de vente trouvé. Création d'un nouveau journal...")
    
    # Créer une séquence pour le journal
    sequence = env['ir.sequence'].sudo().create({
        'name': 'Factures IT',
        'implementation': 'standard',
        'padding': 4,
        'number_next': 1,
        'number_increment': 1,
        'prefix': 'IT/%(year)s/',
        'company_id': env.company.id,
    })
    
    # Chercher un compte par défaut
    default_account = None
    for code in ['706000', '707000', '700000']:
        account = env['account.account'].sudo().search([
            ('code', '=', code),
            ('company_id', '=', env.company.id)
        ], limit=1)
        if account:
            default_account = account
            break
    
    # Si aucun compte trouvé, essayer de créer un
    if not default_account:
        print("Tentative de création d'un compte de revenus...")
        account_type = env.ref('account.data_account_type_revenue', raise_if_not_found=False)
        if not account_type:
            account_type = env.ref('account.data_account_type_other_income', raise_if_not_found=False)
        
        if account_type:
            default_account = env['account.account'].sudo().create({
                'code': '706000',
                'name': 'Prestations de services IT',
                'user_type_id': account_type.id,
                'company_id': env.company.id,
            })
    
    # Créer le journal de vente
    journal_vals = {
        'name': 'Ventes IT Asset',
        'code': 'ITSAL',
        'type': 'sale',
        'sequence_id': sequence.id,
        'company_id': env.company.id,
        'active': True,
    }
    
    if default_account:
        journal_vals['default_account_id'] = default_account.id
        
    journal = env['account.journal'].sudo().create(journal_vals)
    print(f"Journal de vente créé: {journal.name} [{journal.code}]")
    
    # Associer le journal à la propriété par défaut
    if journal:
        property_obj = env['ir.property'].sudo()
        property_obj.set_default(
            'property_journal_id',
            'it.billing',
            journal.id,
            env.company.id
        )
        print("Propriété par défaut définie pour le journal de vente")
    
    # Commit immédiat pour sauvegarder les modifications
    env.cr.commit()
    return journal

# Exécution du script
try:
    print("Début de réparation du journal de vente...")
    journal = fix_sales_journal()
    if journal:
        print(f"Réparation terminée avec succès! Journal: {journal.name} [{journal.code}]")
    else:
        print("Échec de la réparation.")
except Exception as e:
    print(f"Erreur lors de la réparation: {str(e)}") 