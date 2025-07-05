from odoo import models, fields, api

class ITEquipmentType(models.Model):
    _name = 'it.equipment.type'
    _description = 'Type d\'Équipement IT'
    _order = 'sequence, name'

    name = fields.Char(string='Nom', required=True)
    sequence = fields.Integer(string='Séquence', default=10)
    active = fields.Boolean(default=True)
    code = fields.Char(string='Code', help="Code interne pour ce type d'équipement")
    
    # Paramètres par défaut pour ce type d'équipement
    default_warranty_duration = fields.Integer(
        string='Durée de garantie par défaut (mois)', 
        default=24,
        help="Durée de garantie par défaut appliquée à la création d'un équipement de ce type"
    )
    
    default_lifecycle_duration = fields.Integer(
        string='Durée de vie par défaut (mois)', 
        default=36,
        help="Durée de vie moyenne pour planifier le renouvellement de ce type d'équipement"
    )
    
    # Informations complémentaires
    description = fields.Text(string='Description')
    icon = fields.Char(string='Icône', help="Nom de l'icône Font Awesome (ex: laptop, server, desktop, etc.)")
    color = fields.Integer(string='Couleur', default=0)
    
    # Statistiques
    equipment_count = fields.Integer(
        string='Nombre d\'équipements', 
        compute='_compute_equipment_count'
    )
    
    @api.depends('name')
    def _compute_equipment_count(self):
        for record in self:
            record.equipment_count = self.env['it.equipment'].search_count([
                ('type_id', '=', record.id)
            ])

    def action_view_equipments(self):
        self.ensure_one()
        return {
            'name': f'Équipements de type {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'it.equipment',
            'view_mode': 'list,form',
            'domain': [('type_id', '=', self.id)],
            'context': {'default_type_id': self.id}
        }
