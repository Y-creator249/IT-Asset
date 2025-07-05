from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class ITTechnician(models.Model):
    _name = 'it.technician2'
    _description = 'Technicien IT'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Nom',
        required=True,
        tracking=True
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employé associé',
        tracking=True,
        ondelete='set null'
    )
    phone = fields.Char(
        string='Téléphone',
        tracking=True
    )
    email = fields.Char(
        string='Email',
        tracking=True
    )
    speciality = fields.Selection(
        selection=[
            ('hardware', 'Matériel'),
            ('software', 'Logiciel'),
            ('network', 'Réseau'),
            ('security', 'Sécurité'),
            ('all', 'Polyvalent')
        ],
        string='Spécialité',
        required=True,
        default='all',
        tracking=True
    )
    certification_ids = fields.Many2many(
        'it.certification',
        'it_technician2_cert_rel',
        'technician_id',
        'certification_id',
        string='Certifications',
        ondelete='restrict'
    )
    intervention_ids = fields.One2many(
        'it.intervention',
        'technician2_id',
        string='Interventions'
    )
    intervention_count = fields.Integer(
        compute='_compute_intervention_count',
        string="Nombre d'interventions"
    )
    active = fields.Boolean(
        default=True,
        tracking=True
    )
    notes = fields.Text('Notes')

    @api.depends('intervention_ids')
    def _compute_intervention_count(self):
        for record in self:
            record.intervention_count = len(record.intervention_ids)

    def action_view_interventions(self):
        """Ouvre la liste des interventions liées au technicien."""
        self.ensure_one()
        return {
            'name': _('Interventions'),
            'type': 'ir.actions.act_window',
            'res_model': 'it.intervention',
            'view_mode': 'list,form',
            'domain': [('technician2_id', '=', self.id)],
            'context': {
                'default_technician2_id': self.id,
                'search_default_technician2_id': self.id
            },
        } 