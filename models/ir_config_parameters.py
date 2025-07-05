from odoo import api, models, SUPERUSER_ID

class IrConfigParameter(models.Model):
    _inherit = 'ir.config_parameter'
    
    @api.model
    def init(self):
        """
        Initialise des paramètres système lors du démarrage.
        Notamment, active l'inscription libre des utilisateurs
        """
        super(IrConfigParameter, self).init()
        
        # Récupération des paramètres avec sudo pour avoir tous les droits
        params = self.sudo()
        
        # Définir les paramètres d'inscription si nécessaire, sans commit
        params_to_set = {
            'auth_signup.allow_uninvited': 'True',
            'auth_signup.reset_password': 'True',
            'auth_signup.invitation_scope': 'b2b'
        }
        
        for key, value in params_to_set.items():
            current_value = params.get_param(key, 'False')
            if current_value != value:
                params.set_param(key, value) 