from odoo import models, fields, api

class AccountMove(models.Model):
    """Extension du modèle account.move pour ajouter la relation avec les contrats IT"""
    _inherit = 'account.move'
    
    # Relation avec les contrats IT
    contract_id = fields.Many2one('it.contract', string='Contrat IT', tracking=True,
                                 help="Contrat associé à cette facture")
    
    # Relation avec les abonnements
    subscription_id = fields.Many2one('it.subscription', string='Abonnement IT', tracking=True,
                                    help="Abonnement associé à cette facture")
    
    # Champ calculé pour afficher dans le portail client
    is_it_invoice = fields.Boolean(string='Facture IT', compute='_compute_is_it_invoice', store=True)
    
    @api.depends('contract_id', 'subscription_id')
    def _compute_is_it_invoice(self):
        """Détermine si cette facture est liée à un service IT"""
        for move in self:
            move.is_it_invoice = bool(move.contract_id or move.subscription_id)
    
    def action_view_contract(self):
        """Ouvre le formulaire du contrat associé"""
        self.ensure_one()
        if not self.contract_id:
            return {}
        
        return {
            'name': 'Contrat',
            'type': 'ir.actions.act_window',
            'res_model': 'it.contract',
            'view_mode': 'form',
            'res_id': self.contract_id.id,
        }
    
    def action_view_subscription(self):
        """Ouvre le formulaire de l'abonnement associé"""
        self.ensure_one()
        if not self.subscription_id:
            return {}
        
        return {
            'name': 'Abonnement',
            'type': 'ir.actions.act_window',
            'res_model': 'it.subscription',
            'view_mode': 'form',
            'res_id': self.subscription_id.id,
        }
    
    # Méthodes d'accès au portail
    def get_portal_it_details(self):
        """Récupère les informations IT pour affichage dans le portail client"""
        self.ensure_one()
        result = {
            'contract': self.contract_id,
            'subscription': self.subscription_id,
            'is_it_invoice': self.is_it_invoice,
        }
        return result
