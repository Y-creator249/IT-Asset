from odoo import models, fields, api

class ITCategory(models.Model):
    _name = 'it.category'
    _description = 'IT Asset Category'
    _order = 'sequence, name'

    name = fields.Char(string='Nom', required=True)
    code = fields.Char(string='Code', help="Code court pour la catégorie")
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)
    type = fields.Selection([
        ('equipment', 'Équipement'),
        ('contract', 'Contrat'),
        ('license', 'Licence'),
        ('service', 'Service'),
        ('other', 'Autre')
    ], string='Type', default='equipment', required=True)
    sequence = fields.Integer(string='Séquence', default=10,
                             help="Séquence d'affichage des catégories")