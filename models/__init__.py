from . import models
from . import client
from . import equipment
from . import contract
from . import category
from . import incident
from . import intervention
from . import license
from . import alert
from . import billing
from . import res_users
from . import technician  # nouveau modèle
from . import service_level
from . import equipment_type
from . import certification
from . import subscription
from . import account_move
from . import ir_config_parameters
from . import dashboard  # tableau de bord

def post_init_hook(cr, registry):
    """Post-init hook pour initialiser la configuration comptable"""
    import logging
    _logger = logging.getLogger(__name__)
    
    try:
        from odoo import api, SUPERUSER_ID
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        # Initialiser les comptes comptables
        _logger.info("Initialisation des journaux et comptes comptables...")
        result = env['it.billing'].init_accounting()
        
        if result.get('journal'):
            _logger.info(f"Journal de vente initialisé: {result['journal'].name} ({result['journal'].code})")
        else:
            _logger.warning("Aucun journal de vente n'a pu être initialisé!")
        
        if result.get('account'):
            _logger.info(f"Compte de revenus initialisé: {result['account'].code} - {result['account'].name}")
        else:
            _logger.warning("Aucun compte de revenus n'a pu être initialisé!")
            
    except Exception as e:
        _logger.error(f"Erreur lors de l'initialisation des journaux et comptes: {str(e)}")

# Hook de mise à jour pour initialiser le modèle technician2
def post_update_hook(cr, registry):
    from odoo import api, SUPERUSER_ID
    env = api.Environment(cr, SUPERUSER_ID, {})
    try:
        # Créer quelques techniciens par défaut si aucun n'existe
        if not env['it.technician2'].search_count([]):
            env['it.technician2'].create({
                'name': 'Technicien par défaut',
                'speciality': 'all',
                'email': 'support@example.com',
                'phone': '+33123456789'
            })
            env.cr.commit()
            
    except Exception as e:
        import logging
        _logger = logging.getLogger(__name__)
        _logger.error(f"Erreur lors de l'initialisation des techniciens: {str(e)}")
