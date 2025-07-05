from odoo import models, fields, api, _

class ITLicense(models.Model):
    _name = 'it.license'
    _description = 'Licence IT'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nom', required=True, tracking=True)
    license_key = fields.Char(string='Clé de licence', tracking=True)
    client_id = fields.Many2one('it.client', string='Client', required=True, tracking=True)
    equipment_id = fields.Many2one('it.equipment', string='Équipement', domain="[('category', '=', 'software')]", tracking=True)
    contract_id = fields.Many2one('it.contract', string='Contrat', tracking=True)
    purchase_date = fields.Date(string='Date d\'achat', tracking=True)
    expiry_date = fields.Date(string='Date d\'expiration', tracking=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('expired', 'Expirée'),
        ('cancelled', 'Annulée')
    ], string='État', default='active', tracking=True)
    active = fields.Boolean(default=True)

    @api.onchange('client_id')
    def _onchange_client_id(self):
        self.equipment_id = False
        self.contract_id = False
        return {'domain': {
            'equipment_id': [('client_id', '=', self.client_id.id), ('category', '=', 'software')],
            'contract_id': [('client_id', '=', self.client_id.id)]
        }}

    @api.model
    def _cron_check_expired_licenses(self):
        today = fields.Date.today()
        expired_licenses = self.search([
            ('state', '=', 'active'),
            ('expiry_date', '<', today)
        ])
        expired_licenses.write({'state': 'expired'})