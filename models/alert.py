from odoo import models, fields, api, _

class ITAlert(models.Model):
    _name = 'it.alert'
    _description = 'Alerte IT'
    _inherit = ['mail.thread']

    name = fields.Char(string='Nom', required=True)
    alert_type = fields.Selection([
        ('warranty', 'Fin de garantie'),
        ('license', 'Expiration de licence'),
        ('maintenance', 'Maintenance préventive')
    ], string='Type d\'alerte', required=True)
    equipment_id = fields.Many2one('it.equipment', string='Équipement')
    license_id = fields.Many2one('it.license', string='Licence')
    contract_id = fields.Many2one('it.contract', string='Contrat')
    client_id = fields.Many2one('it.client', string='Client', required=True)
    alert_date = fields.Date(string='Date de l\'alerte', required=True)
    description = fields.Text(string='Description')
    state = fields.Selection([
        ('new', 'Nouveau'),
        ('sent', 'Envoyé'),
        ('done', 'Terminé')
    ], string='État', default='new')

    def action_send_alert(self):
        self.ensure_one()
        template = self.env.ref('it_asset_management.email_template_alert')
        self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)
        self.write({'state': 'sent'})

    @api.model
    def _cron_generate_alerts(self):
        today = fields.Date.today()
        # Alertes pour fin de garantie
        equipments = self.env['it.equipment'].search([
            ('warranty_end', '=', today),
            ('state', '!=', 'retired')
        ])
        for eq in equipments:
            self.create({
                'name': f"Fin de garantie: {eq.name}",
                'alert_type': 'warranty',
                'equipment_id': eq.id,
                'client_id': eq.client_id.id,
                'alert_date': today,
                'description': f"La garantie de l'équipement {eq.name} expire aujourd'hui."
            })
        # Alertes pour licences
        licenses = self.env['it.license'].search([
            ('expiry_date', '=', today),
            ('state', '=', 'active')
        ])
        for lic in licenses:
            self.create({
                'name': f"Expiration licence: {lic.name}",
                'alert_type': 'license',
                'license_id': lic.id,
                'client_id': lic.client_id.id,
                'alert_date': today,
                'description': f"La licence {lic.name} expire aujourd'hui."
            })