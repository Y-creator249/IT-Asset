from odoo import models, fields, api, _

class ITEquipment(models.Model):
    _name = 'it.equipment'
    _description = 'Équipement IT'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nom', required=True, tracking=True)
    type_id = fields.Many2one('it.equipment.type', string='Type', required=True)
    serial_number = fields.Char(string='Numéro de série', tracking=True)
    category = fields.Selection([
        ('hardware', 'Matériel'),
        ('software', 'Logiciel'),
        ('network', 'Réseau'),
        ('peripheral', 'Périphérique'),
        ('other', 'Autre')
    ], string='Catégorie', required=True, default='hardware', tracking=True)
    client_id = fields.Many2one('it.client', string='Client', tracking=True)
    purchase_date = fields.Date(string='Date d\'achat', tracking=True)
    warranty_end = fields.Date(string='Fin de garantie', tracking=True)
    state = fields.Selection([
        ('available', 'Disponible'),
        ('assigned', 'Assigné'),
        ('maintenance', 'En maintenance'),
        ('retired', 'Retiré')
    ], string='État', default='available', tracking=True)
    active = fields.Boolean(default=True)