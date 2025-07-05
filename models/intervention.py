from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class ITIntervention(models.Model):
    _name = 'it.intervention'
    _description = 'Intervention IT'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Numéro d'intervention", required=True, copy=False, tracking=True)
    incident_id = fields.Many2one('it.incident', string='Incident', tracking=True)
    equipment_id = fields.Many2one('it.equipment', string='Équipement', required=True, tracking=True)
    client_id = fields.Many2one('it.client', string='Client', related='equipment_id.client_id', store=True, tracking=True)
    contract_id = fields.Many2one('it.contract', string='Contrat', tracking=True)
    description = fields.Text(string='Description de l\'intervention', required=True)
    intervention_date = fields.Datetime(string='Date de l\'intervention', default=fields.Datetime.now, required=True)
    
    # Nouveau champ technicien
    technician2_id = fields.Many2one('it.technician2', string='Technicien', tracking=True, required=True)
    
    state = fields.Selection([
        ('planned', 'Planifiée'),
        ('done', 'Terminée'),
        ('cancelled', 'Annulée')
    ], string='État', default='planned', tracking=True)
    active = fields.Boolean(default=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('it.intervention') or 'Nouveau'
        return super().create(vals_list)

    def action_done(self):
        self.write({'state': 'done'})
        if self.equipment_id:
            self.equipment_id.write({'state': 'available'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    @api.onchange('equipment_id')
    def _onchange_equipment_id(self):
        self.contract_id = False
        return {'domain': {
            'contract_id': [('client_id', '=', self.client_id.id)]
        }}