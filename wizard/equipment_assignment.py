from odoo import models, fields, api, _
from odoo.exceptions import UserError

class EquipmentAssignment(models.TransientModel):
    _name = 'it.equipment.assignment.wizard' 
    _description = "Assistant d'affectation d'équipement"

    equipment_id = fields.Many2one('it.equipment', string='Équipement', required=True)
    client_id = fields.Many2one('it.client', string='Client', required=True)
    assignment_date = fields.Date(string="Date d'affectation", default=fields.Date.today, required=True)
    notes = fields.Text(string='Notes')

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if self._context.get('active_id'):
            equipment = self.env['it.equipment'].browse(self._context.get('active_id'))
            res.update({
                'equipment_id': equipment.id,
                'client_id': equipment.client_id.id,
            })
        return res

    def action_assign(self):
        self.ensure_one()
        if self.equipment_id.state == 'assigned':
            raise UserError(_("Cet équipement est déjà affecté."))
            
        self.equipment_id.write({
            'client_id': self.client_id.id,
            'assignment_date': self.assignment_date,
            'state': 'assigned',
            'notes': self.notes,
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Succès'),
                'message': _("L'équipement a été affecté avec succès."),
                'type': 'success',
                'sticky': False,
            }
        }