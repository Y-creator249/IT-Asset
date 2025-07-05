from odoo import models, fields, api
from datetime import date

class ITCertification(models.Model):
    _name = 'it.certification'
    _description = 'Certification IT'
    _order = 'name'

    name = fields.Char(string='Nom', required=True)
    code = fields.Char(string='Code/Référence')
    active = fields.Boolean(default=True)
    
    # Détails de la certification
    description = fields.Text(string='Description')
    provider = fields.Char(string='Organisme certificateur', help="Organisme qui délivre cette certification")
    level = fields.Selection([
        ('basic', 'Basique'),
        ('intermediate', 'Intermédiaire'),
        ('advanced', 'Avancé'),
        ('expert', 'Expert'),
    ], string='Niveau', default='intermediate')
    
    # Validité
    validity_duration = fields.Integer(
        string='Durée de validité (mois)', 
        default=24,
        help="Durée de validité de la certification avant renouvellement"
    )
    
    # Catégorisation
    category = fields.Selection([
        ('hardware', 'Matériel'),
        ('software', 'Logiciel'),
        ('network', 'Réseau'),
        ('security', 'Sécurité'),
        ('cloud', 'Cloud'),
        ('database', 'Base de données'),
        ('methodology', 'Méthodologie'),
        ('other', 'Autre'),
    ], string='Catégorie', default='other')
    
    # Technologie concernée
    technology_id = fields.Many2one('ir.model.data', string='Technologie associée')
    
    # Information sur l'examen
    exam_required = fields.Boolean(string='Examen requis', default=True)
    recertification_required = fields.Boolean(string='Recertification requise', default=True)
    
    # Notes supplémentaires
    notes = fields.Html(string='Notes additionnelles')
    
    # Compteur de techniciens
    technician_count = fields.Integer(string='Nombre de techniciens', compute='_compute_technician_count')
    
    @api.depends('name')
    def _compute_technician_count(self):
        for record in self:
            record.technician_count = self.env['it.technician'].search_count([
                ('certification_ids', 'in', record.id)
            ])
    
    def action_view_technicians(self):
        self.ensure_one()
        return {
            'name': f'Techniciens avec certification {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'it.technician',
            'view_mode': 'list,form',
            'domain': [('certification_ids', 'in', self.id)],
        }
        
    # TODO: Implémenter le modèle it.technician.certification
    # def check_expiry_for_technicians(self):
    #     """Vérifie les certifications expirant prochainement et envoie une notification aux techniciens"""
    #     technician_cert = self.env['it.technician.certification'].search([
    #         ('certification_id', 'in', self.ids),
    #         ('expiry_date', '!=', False),
    #     ])
    #     
    #     today = date.today()
    #     for record in technician_cert:
    #         if record.expiry_date:
    #             days_remaining = (record.expiry_date - today).days
    #             if days_remaining <= 30 and not record.expiry_notified:
    #                 # Envoyer une notification
    #                 record.technician_id.message_post(
    #                     body=f"La certification <b>{record.certification_id.name}</b> expire dans {days_remaining} jours.",
    #                     subject="Alerte d'expiration de certification",
    #                 )
    #                 record.write({'expiry_notified': True})
