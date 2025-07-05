from odoo import models, fields, api, _

class ITIncident(models.Model):
    _name = 'it.incident'
    _description = 'Incident IT'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Numéro', readonly=True, copy=False, default=lambda self: self.env['ir.sequence'].next_by_code('it.ticket'))
    client_id = fields.Many2one('it.client', string='Client', required=True, tracking=True)
    equipment_id = fields.Many2one('it.equipment', string='Équipement', tracking=True)
    contract_id = fields.Many2one('it.contract', string='Contrat', tracking=True)
    description = fields.Text(string='Description', required=True)
    state = fields.Selection([
        ('new', 'Nouveau'),
        ('in_progress', 'En cours'),
        ('resolved', 'Résolu'),
        ('closed', 'Fermé')
    ], string='État', default='new', tracking=True)
    priority = fields.Selection([
        ('low', 'Basse'),
        ('medium', 'Moyenne'),
        ('high', 'Haute')
    ], string='Priorité', default='medium', tracking=True)
    assigned_to = fields.Many2one('res.users', string='Assigné à', tracking=True)
    date_reported = fields.Datetime(string='Date de signalement', default=fields.Datetime.now, readonly=True)
    date_resolved = fields.Datetime(string='Date de résolution', readonly=True)
    active = fields.Boolean(default=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code('it.ticket')
        return super().create(vals_list)

    def action_in_progress(self):
        self.write({'state': 'in_progress'})

    def action_resolve(self):
        self.write({
            'state': 'resolved',
            'date_resolved': fields.Datetime.now()
        })

    def action_close(self):
        self.write({'state': 'closed'})

    @api.onchange('client_id')
    def _onchange_client_id(self):
        self.equipment_id = False
        self.contract_id = False
        return {'domain': {
            'equipment_id': [('client_id', '=', self.client_id.id)],
            'contract_id': [('client_id', '=', self.client_id.id)]
        }}