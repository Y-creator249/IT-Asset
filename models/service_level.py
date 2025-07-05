from odoo import models, fields, api

class ITServiceLevel(models.Model):
    _name = 'it.service.level'
    _description = 'Niveau de Service IT'
    _order = 'sequence, name'

    name = fields.Char(string='Nom', required=True)
    code = fields.Char(string='Code', required=True)
    sequence = fields.Integer(string='Séquence', default=10)
    active = fields.Boolean(default=True)
    
    # SLA Information
    response_time = fields.Float(string='Temps de réponse (heures)', help="Temps de réponse garanti pour les incidents")
    resolution_time = fields.Float(string='Temps de résolution (heures)', help="Temps de résolution garanti pour les incidents")
    
    # Availability
    availability_percentage = fields.Float(string='Disponibilité (%)', default=99.5, 
                                         help="Pourcentage de disponibilité garanti pour les services")
    maintenance_window = fields.Char(string='Fenêtre de maintenance', 
                                   help="Exemple: Dimanche 22h-02h")
    
    # Support Details
    support_hours = fields.Selection([
        ('business', 'Heures de bureau (9h-18h)'),
        ('extended', 'Étendu (8h-20h)'),
        ('24x5', '24/7 hors weekend (24x5)'),
        ('24x7', 'Permanent (24x7)')
    ], string='Heures de support', default='business')
    
    support_days = fields.Selection([
        ('businessdays', 'Jours ouvrés'),
        ('alldays', 'Tous les jours')
    ], string='Jours de support', default='businessdays')
    
    support_phone = fields.Char(string='Téléphone de support')
    support_email = fields.Char(string='Email de support')
    
    # Financial
    price = fields.Float(string='Prix mensuel', help="Prix mensuel de ce niveau de service")
    
    # Description
    description = fields.Html(string='Description', help="Description détaillée de ce niveau de service")
    
    # Color for display
    color = fields.Integer(string='Couleur', default=0)
    
    def name_get(self):
        result = []
        for record in self:
            name = f"{record.code} - {record.name}" if record.code else record.name
            result.append((record.id, name))
        return result
