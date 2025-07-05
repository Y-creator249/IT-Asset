from . import models
from . import controllers
from . import wizard
from .models import post_init_hook, post_update_hook

def post_init_hook(cr, registry):
    """
    Hook exécuté après l'installation du module.
    Permet d'activer l'inscription libre des utilisateurs.
    """
    import logging
    _logger = logging.getLogger(__name__)
    
    from odoo import api, SUPERUSER_ID
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Activer les paramètres d'inscription
    params = env['ir.config_parameter'].sudo()
    params.set_param('auth_signup.allow_uninvited', 'True')
    params.set_param('auth_signup.reset_password', 'True')
    params.set_param('auth_signup.invitation_scope', 'b2b')
    
    # Initialiser les journaux et comptes comptables
    try:
        _logger.info("Initialisation des journaux et comptes comptables...")
        
        # D'abord vérifier si notre journal existe déjà
        journal = env.ref('it_asset_management.it_asset_sales_journal', False)
        if journal:
            _logger.info(f"Journal de vente défini trouvé: {journal.name} ({journal.code})")
        else:
            # Essayer d'initialiser via la méthode standard
            result = env['it.billing'].init_accounting()
            
            if result.get('journal'):
                _logger.info(f"Journal de vente initialisé: {result['journal'].name} ({result['journal'].code})")
            else:
                _logger.warning("Aucun journal de vente n'a pu être initialisé! Création manuelle...")
                # Création manuelle d'un journal de vente comme dernier recours
                try:
                    sequence = env['ir.sequence'].sudo().create({
                        'name': 'Factures IT',
                        'implementation': 'standard',
                        'padding': 4,
                        'number_next': 1,
                        'number_increment': 1,
                        'prefix': 'IT/%(year)s/',
                        'company_id': env.company.id,
                    })
                    
                    journal = env['account.journal'].sudo().create({
                        'name': 'Ventes IT Asset (Manuel)',
                        'code': 'ITSM',
                        'type': 'sale',
                        'sequence_id': sequence.id,
                        'company_id': env.company.id,
                        'active': True,
                    })
                    _logger.info(f"Journal de vente créé manuellement: {journal.name} ({journal.code})")
                except Exception as e:
                    _logger.error(f"Échec de la création manuelle du journal: {str(e)}")
        
        # Vérifier le compte de revenus
        account = env.ref('it_asset_management.it_sales_income_account', False)
        if account:
            _logger.info(f"Compte de revenus défini trouvé: {account.code} - {account.name}")
        elif result and result.get('account'):
            _logger.info(f"Compte de revenus initialisé: {result['account'].code} - {result['account'].name}")
        else:
            _logger.warning("Aucun compte de revenus n'a pu être initialisé!")
            
    except Exception as e:
        _logger.error(f"Erreur lors de l'initialisation des journaux et comptes: {str(e)}")