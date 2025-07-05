from odoo import models, fields, api, _
from datetime import date, timedelta
from odoo.exceptions import UserError

class ITContract(models.Model):
    _name = 'it.contract'
    _description = 'Contrat IT'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

    name = fields.Char(string='Nom', required=True, tracking=True)
    reference = fields.Char(string='Référence', readonly=True, copy=False)
    client_id = fields.Many2one('it.client', string='Client', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Partenaire', related='client_id.partner_id', store=True, readonly=True)
    
    # Compteurs pour la vue statistique
    equipment_count = fields.Integer(string='Nombre d\'équipements', compute='_compute_equipment_count')
    invoice_count = fields.Integer(string='Nombre de factures', compute='_compute_invoice_count')
    invoice_ids = fields.One2many('account.move', 'contract_id', string='Factures')
    
    # Add contract_type field
    contract_type = fields.Selection([
        ('maintenance', 'Maintenance'),
        ('support', 'Support technique'),
        ('license', 'Licence logiciel'),
        ('hosting', 'Hébergement'),
        ('other', 'Autre')
    ], string='Type de contrat', required=True, default='maintenance', tracking=True)
    
    date_start = fields.Date(string='Date début', required=True, tracking=True)
    date_end = fields.Date(string='Date fin', tracking=True)
    amount = fields.Monetary(string='Montant', required=True, tracking=True)
    currency_id = fields.Many2one('res.currency', string='Devise',
        default=lambda self: self.env.company.currency_id)
    description = fields.Html(string='Description')
    equipment_ids = fields.Many2many('it.equipment', string='Équipements')
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('expired', 'Expiré'),
        ('cancelled', 'Annulé')
    ], string='État', default='draft', tracking=True)
    active = fields.Boolean(default=True)
    
    # Champs pour les notifications
    expiry_reminder_sent = fields.Boolean(string='Rappel d\'expiration envoyé', default=False)
    days_before_reminder = fields.Integer(string='Jours avant rappel', default=30,
                                        help="Nombre de jours avant la date de fin pour envoyer un rappel")

    # ... rest of the existing methods ...

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('reference'):
                vals['reference'] = self.env['ir.sequence'].next_by_code('it.contract')
        return super().create(vals_list)

    def action_draft(self):
        """Remettre le contrat en brouillon"""
        for contract in self:
            if contract.state == 'confirmed':
                contract.write({'state': 'draft'})
        return True

    def action_confirm(self):
        """Confirmer le contrat"""
        for contract in self:
            if contract.state == 'draft':
                contract.write({'state': 'confirmed'})
        return True

    @api.onchange('date_start', 'date_end')
    def _onchange_dates(self):
        if self.date_start and self.date_end and self.date_end < self.date_start:
            self.date_end = self.date_start

    @api.model
    def _cron_check_expired_contracts(self):
        """Vérifier et marquer les contrats expirés"""
        today = fields.Date.today()
        # Contrats expirés
        expired_contracts = self.search([
            ('state', '=', 'confirmed'),
            ('date_end', '<', today)
        ])
        expired_contracts.write({'state': 'expired'})
        
        # Contrats à rappeler
        contracts_to_notify = self.search([
            ('state', '=', 'confirmed'),
            ('date_end', '!=', False),
            ('expiry_reminder_sent', '=', False),
            ('date_end', '<=', fields.Date.to_string(today + timedelta(days=30))),
            ('date_end', '>=', fields.Date.to_string(today))
        ])
        
        for contract in contracts_to_notify:
            days_left = (contract.date_end - today).days
            
            # Notification dans Odoo
            contract.message_post(
                body=f"Ce contrat expire dans {days_left} jours. Veuillez contacter le client pour discuter du renouvellement.",
                subject="Rappel d'expiration de contrat"
            )
            
            # Notification par email au responsable du compte si configuré
            if contract.client_id.account_manager_id and contract.client_id.account_manager_id.email:
                template = self.env.ref('it_asset_management.email_template_contract_reminder', raise_if_not_found=False)
                if template:
                    template.send_mail(contract.id, force_send=True)
            
            contract.expiry_reminder_sent = True
            
    # Méthodes de comptage
    def _compute_equipment_count(self):
        for contract in self:
            contract.equipment_count = len(contract.equipment_ids)
            
    def _compute_invoice_count(self):
        for contract in self:
            contract.invoice_count = len(contract.invoice_ids)
    
    # Actions d'affichage
    def action_view_equipment(self):
        self.ensure_one()
        return {
            'name': 'Équipements',
            'type': 'ir.actions.act_window',
            'res_model': 'it.equipment',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.equipment_ids.ids)],
            'context': {'default_client_id': self.client_id.id}
        }
    
    def action_view_invoices(self):
        self.ensure_one()
        return {
            'name': 'Factures',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.invoice_ids.ids)],
            'context': {'default_partner_id': self.partner_id.id, 'default_contract_id': self.id}
        }
    
    def action_cancel(self):
        """Annuler le contrat"""
        for contract in self:
            contract.write({'state': 'cancelled'})
        return True
        
    def action_renew(self, months=12):
        """Renouveler le contrat pour la période spécifiée"""
        self.ensure_one()
        if self.state in ['confirmed', 'expired']:
            new_start_date = self.date_end or fields.Date.today()
            new_end_date = date(new_start_date.year + (months // 12), 
                               new_start_date.month + (months % 12), 
                               1) - timedelta(days=1)
            
            self.write({
                'date_start': new_start_date,
                'date_end': new_end_date,
                'state': 'confirmed',
                'expiry_reminder_sent': False
            })
    
    # Méthodes d'accès au portail
    def _compute_access_url(self):
        for record in self:
            record.access_url = '/my/contrat/%s' % record.id

    def _get_portal_return_action(self):
        return self.env.ref('it_asset_management.action_portal_contract')

    def get_portal_url(self, suffix=None, report_type=None, download=None, query_string=None, anchor=None):
        """Generate portal URL for contract record"""
        self.ensure_one()
        url = '/my/contrat/%s' % self.id
        if suffix:
            url = '%s/%s' % (url, suffix)
        return url
        
    def get_equipment_details(self):
        """Get equipment details for portal display"""
        self.ensure_one()
        return {
            'equipment': self.equipment_ids,
            'count': len(self.equipment_ids),
            'has_expired_warranty': any(eq.warranty_end_date and eq.warranty_end_date < fields.Date.today() for eq in self.equipment_ids if eq.warranty_end_date)
        }
        
    def action_create_invoice(self):
        """Créer une facture pour ce contrat"""
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
            'contract_id': self.id,
            'invoice_date': fields.Date.today(),
            'journal_id': journal.id,
            'invoice_line_ids': [(0, 0, {
                'name': f"Contrat {self.name} - {self.contract_type}",
                'quantity': 1,
                'price_unit': self.amount,
                'account_id': product_account.id,
            })],
        })
        
        return {
            'name': 'Facture',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': invoice.id,
        }