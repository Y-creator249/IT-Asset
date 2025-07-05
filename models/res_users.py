from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    client_ids = fields.Many2many(
        'it.client',
        'it_client_users_rel',
        'user_id',
        'client_id',
        string='Clients assignés'
    )
    
    @api.model
    def _get_signup_invitation_scope(self):
        """
        Surcharge pour toujours permettre l'inscription libre
        dans le contexte du module IT Asset Management
        """
        # Vérifie si c'est un accès depuis notre module
        if self.env.context.get('it_asset_portal'):
            return 'b2c'  # b2c permet l'inscription libre
        return super(ResUsers, self)._get_signup_invitation_scope()
    
    @api.model
    def _signup_create_user(self, values):
        """
        Surcharge pour contourner la vérification d'invitation
        lorsque nous sommes dans le contexte du portail IT
        """
        # Si on est dans le contexte du module IT Asset
        if self.env.context.get('it_asset_portal'):
            # Pas de vérification pour les utilisateurs non invités
            return self._create_user_from_template(values)
        # Sinon comportement normal
        return super(ResUsers, self)._signup_create_user(values)