from odoo import models, fields, api, _
from datetime import date, timedelta
from odoo.exceptions import UserError

class ITSubscription(models.Model):
    _name = 'it.subscription'
    _description = 'Abonnement IT'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_start desc, name'

    name = fields.Char(string='Référence', required=True, copy=False, tracking=True)
    description = fields.Text(string='Description', tracking=True)
    active = fields.Boolean(default=True)
    
    # Relations
    client_id = fields.Many2one('it.client', string='Client', required=True, tracking=True, 
                               ondelete='restrict')
    partner_id = fields.Many2one('res.partner', string='Partenaire', related='client_id.partner_id', 
                                store=True, readonly=True)
    service_level_id = fields.Many2one('it.service.level', string='Niveau de Service', 
                                     tracking=True)
    
    # Dates
    date_start = fields.Date(string='Date de début', required=True, default=fields.Date.today, 
                           tracking=True)
    date_end = fields.Date(string='Date de fin', tracking=True)
    next_invoice_date = fields.Date(string='Prochaine facturation', tracking=True)
    auto_renew = fields.Boolean(string='Renouvellement automatique', default=True, tracking=True)
    
    # Informations de facturation
    frequency = fields.Selection([
        ('monthly', 'Mensuel'),
        ('quarterly', 'Trimestriel'),
        ('semi_annual', 'Semestriel'),
        ('annual', 'Annuel')
    ], string='Fréquence de facturation', default='monthly', required=True, tracking=True)
    
    amount = fields.Float(string='Montant', required=True, tracking=True)
    currency_id = fields.Many2one('res.currency', string='Devise', 
                                 default=lambda self: self.env.company.currency_id)
    tax_id = fields.Many2one('account.tax', string='Taxe')
    
    # Statut
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('active', 'Actif'),
        ('expired', 'Expiré'),
        ('cancelled', 'Annulé')
    ], string='Statut', default='draft', tracking=True)
    
    # Historique de facturation
    invoice_count = fields.Integer(string='Nombre de factures', compute='_compute_invoice_count')
    invoice_ids = fields.One2many('account.move', 'subscription_id', string='Factures')
    
    # Notifications
    renewal_reminder_sent = fields.Boolean(string='Rappel de renouvellement envoyé', default=False)
    days_before_reminder = fields.Integer(string='Jours avant rappel', default=30,
                                        help="Nombre de jours avant la date de fin pour envoyer un rappel")
    
    # Équipements liés
    equipment_ids = fields.Many2many('it.equipment', string='Équipements couverts')
    equipment_count = fields.Integer(string='Nombre d\'équipements', compute='_compute_equipment_count')
    
    # Calcul des compteurs
    def _compute_invoice_count(self):
        for sub in self:
            sub.invoice_count = len(sub.invoice_ids)
    
    def _compute_equipment_count(self):
        for sub in self:
            sub.equipment_count = len(sub.equipment_ids)
    
    # Gestion des états
    def action_activate(self):
        return self.write({'state': 'active'})
    
    def action_cancel(self):
        return self.write({'state': 'cancelled'})
    
    def action_set_to_draft(self):
        return self.write({'state': 'draft'})
    
    # Actions
    def action_view_invoices(self):
        self.ensure_one()
        return {
            'name': 'Factures',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.invoice_ids.ids)],
            'context': {'default_partner_id': self.partner_id.id, 'default_subscription_id': self.id}
        }
    
    def action_view_equipments(self):
        self.ensure_one()
        return {
            'name': 'Équipements',
            'type': 'ir.actions.act_window',
            'res_model': 'it.equipment',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.equipment_ids.ids)],
            'context': {'default_client_id': self.client_id.id}
        }
    
    # Automatisation
    @api.model
    def _cron_check_expiration(self):
        """Vérifier les abonnements qui vont expirer bientôt"""
        today = fields.Date.today()
        subs_to_notify = self.search([
            ('state', '=', 'active'),
            ('date_end', '!=', False),
            ('renewal_reminder_sent', '=', False),
            ('date_end', '<=', fields.Date.to_string(today + timedelta(days=30))),
            ('date_end', '>=', fields.Date.to_string(today))
        ])
        
        for subscription in subs_to_notify:
            days_left = (subscription.date_end - today).days
            
            # Notification dans Odoo
            subscription.message_post(
                body=f"Cet abonnement expire dans {days_left} jours. Veuillez contacter le client pour discuter du renouvellement.",
                subject="Rappel d'expiration d'abonnement"
            )
            
            # Notification par email au responsable du compte
            if subscription.client_id.account_manager_id and subscription.client_id.account_manager_id.email:
                template = self.env.ref('it_asset_management.email_template_subscription_reminder', raise_if_not_found=False)
                if template:
                    template.send_mail(subscription.id, force_send=True)
            
            subscription.renewal_reminder_sent = True
    
    # Renouvellement
    def action_renew(self, months=12):
        """Renouveler l'abonnement pour la période spécifiée"""
        self.ensure_one()
        if self.state in ['active', 'expired']:
            new_start_date = self.date_end or fields.Date.today()
            new_end_date = date(new_start_date.year + (months // 12), 
                               new_start_date.month + (months % 12), 
                               1) - timedelta(days=1)
            
            self.write({
                'date_start': new_start_date,
                'date_end': new_end_date,
                'state': 'active',
                'renewal_reminder_sent': False
            })
    
    # Génération des factures
    def action_create_invoice(self):
        """Créer une facture pour cet abonnement"""
        self.ensure_one()
        
        # Récupérer le journal des ventes
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        if not journal:
            raise UserError(_("Aucun journal de vente n'a été trouvé. Veuillez en créer un d'abord."))
            
        # Récupérer le compte produit par défaut
        product_account = self.env['ir.property']._get('property_account_income_id', 'product.template')
        if not product_account:
            product_account = self.env['ir.property']._get('property_account_expense_categ_id', 'product.category')
            
        if not product_account:
            raise UserError(_("Veuillez configurer un compte produit par défaut dans la configuration comptable."))
        
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'subscription_id': self.id,
            'invoice_date': fields.Date.today(),
            'journal_id': journal.id,
            'invoice_line_ids': [(0, 0, {
                'name': f"Abonnement {self.name} - {self.description or ''}",
                'quantity': 1,
                'price_unit': self.amount,
                'tax_ids': [(6, 0, [self.tax_id.id])] if self.tax_id else False,
                'account_id': product_account.id,
            })],
        })
        
        # Mettre à jour la date de prochaine facturation
        next_date = fields.Date.today()
        if self.frequency == 'monthly':
            next_date = date(next_date.year, next_date.month + 1, 1) - timedelta(days=1)
        elif self.frequency == 'quarterly':
            next_date = date(next_date.year, next_date.month + 3, 1) - timedelta(days=1)
        elif self.frequency == 'semi_annual':
            next_date = date(next_date.year, next_date.month + 6, 1) - timedelta(days=1)
        elif self.frequency == 'annual':
            next_date = date(next_date.year + 1, next_date.month, 1) - timedelta(days=1)
        
        self.write({'next_invoice_date': next_date})
        
        return {
            'name': 'Facture',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': invoice.id,
        }
    
    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code('it.subscription')
        return super(ITSubscription, self).create(vals)
    
    def write(self, vals):
        # Si la date de fin est dans le passé, mettre à jour le statut à 'expired'
        result = super(ITSubscription, self).write(vals)
        today = fields.Date.today()
        for record in self:
            if record.date_end and record.date_end < today and record.state == 'active':
                record.state = 'expired'
        return result
