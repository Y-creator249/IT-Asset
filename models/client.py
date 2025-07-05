from odoo import models, fields, api
from datetime import date, timedelta

class ITClient(models.Model):
    _name = 'it.client'
    _description = 'IT Client'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Partenaire', required=True, tracking=True)
    reference = fields.Char(string='Reference', readonly=True, copy=False)
    active = fields.Boolean(default=True)
    
    # Contact Information
    email = fields.Char(string='Email', tracking=True)
    phone = fields.Char(string='Téléphone', tracking=True)
    
    # Classification
    client_type = fields.Selection([
        ('enterprise', 'Entreprise'),
        ('government', 'Gouvernement'),
        ('education', 'Éducation'),
        ('nonprofit', 'Association'),
        ('individual', 'Particulier')
    ], string='Type de Client', default='enterprise', tracking=True)
    
    industry = fields.Selection([
        ('technology', 'Technologie'),
        ('healthcare', 'Santé'),
        ('finance', 'Finance'),
        ('education', 'Éducation'),
        ('manufacturing', 'Industrie'),
        ('retail', 'Commerce'),
        ('services', 'Services'),
        ('other', 'Autre')
    ], string='Secteur d\'activité', tracking=True)
    
    size = fields.Selection([
        ('small', 'Petite (1-50)'),
        ('medium', 'Moyenne (51-250)'),
        ('large', 'Grande (251-1000)'),
        ('enterprise', 'Très grande (1000+)')
    ], string='Taille', tracking=True)
    
    # Service Management
    service_level_id = fields.Many2one('it.service.level', string='Niveau de Service', tracking=True)
    account_manager_id = fields.Many2one('res.users', string='Gestionnaire de Compte', tracking=True)
    technical_contact_id = fields.Many2one('res.partner', string='Contact Technique', tracking=True)
    
    # Contract Information
    contract_count = fields.Integer(compute='_compute_contract_count', string='Nombre de Contrats')
    equipment_count = fields.Integer(compute='_compute_equipment_count', string='Nombre d\'Équipements')
    ticket_count = fields.Integer(compute='_compute_ticket_count', string='Nombre de Tickets')
    subscription_count = fields.Integer(compute='_compute_subscription_count', string='Nombre d\'Abonnements')
    invoice_count = fields.Integer(compute='_compute_invoice_count', string='Nombre de Factures')
    
    # Client Status
    status = fields.Selection([
        ('draft', 'Brouillon'),
        ('active', 'Actif'),
        ('inactive', 'Inactif'),
        ('suspended', 'Suspendu')
    ], string='Statut', default='draft', tracking=True)
    
    # Dates
    onboarding_date = fields.Date(string='Date d\'intégration', tracking=True)
    last_review_date = fields.Date(string='Dernière revue', tracking=True)
    next_review_date = fields.Date(string='Prochaine revue', tracking=True)
    
    # Notes
    notes = fields.Html(string='Notes', tracking=True)
    
    # Compute methods for counters
    def _compute_contract_count(self):
        for client in self:
            client.contract_count = self.env['it.contract'].search_count([('client_id', '=', client.id)])
            
    def _compute_equipment_count(self):
        for client in self:
            client.equipment_count = self.env['it.equipment'].search_count([('client_id', '=', client.id)])
            
    def _compute_ticket_count(self):
        for client in self:
            # Utiliser partner_id qui existe dans helpdesk.ticket au lieu de client_id
            client.ticket_count = self.env['helpdesk.ticket'].search_count([('partner_id', '=', client.partner_id.id)])
            
    def _compute_subscription_count(self):
        for client in self:
            client.subscription_count = self.env['it.subscription'].search_count([('client_id', '=', client.id)])
            
    def _compute_invoice_count(self):
        for client in self:
            client.invoice_count = self.env['account.move'].search_count([('partner_id', '=', client.partner_id.id), ('move_type', 'in', ('out_invoice', 'out_refund'))])
    
    # Action methods to open related views
    def action_view_contracts(self):
        self.ensure_one()
        return {
            'name': 'Contrats',
            'type': 'ir.actions.act_window',
            'res_model': 'it.contract',
            'view_mode': 'tree,form',
            'domain': [('client_id', '=', self.id)],
            'context': {'default_client_id': self.id}
        }
        
    def action_view_equipment(self):
        self.ensure_one()
        return {
            'name': 'Équipements',
            'type': 'ir.actions.act_window',
            'res_model': 'it.equipment',
            'view_mode': 'tree,form',
            'domain': [('client_id', '=', self.id)],
            'context': {'default_client_id': self.id}
        }
        
    def action_view_tickets(self):
        self.ensure_one()
        return {
            'name': 'Tickets',
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.partner_id.id)],
            'context': {'default_partner_id': self.partner_id.id}
        }
        
    def action_view_subscriptions(self):
        self.ensure_one()
        return {
            'name': 'Abonnements',
            'type': 'ir.actions.act_window',
            'res_model': 'it.subscription',
            'view_mode': 'tree,form',
            'domain': [('client_id', '=', self.id)],
            'context': {'default_client_id': self.id}
        }
        
    def action_view_invoices(self):
        self.ensure_one()
        return {
            'name': 'Factures',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.partner_id.id), ('move_type', 'in', ('out_invoice', 'out_refund'))],
            'context': {'default_partner_id': self.partner_id.id, 'default_move_type': 'out_invoice'}
        }
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('reference'):
                vals['reference'] = self.env['ir.sequence'].next_by_code('it.client')
        return super().create(vals_list)
    
    def _compute_access_url(self):
        for record in self:
            record.access_url = '/my/client/%s' % record.id

    def _get_portal_return_action(self):
        return self.env.ref('it_asset_management.action_portal_client')
        
    def get_portal_url(self, suffix=None, report_type=None, download=None, query_string=None, anchor=None):
        """Generate portal URL for client self record"""
        self.ensure_one()
        url = '/my/client/%s' % self.id
        if suffix:
            url = '%s/%s' % (url, suffix)
        return url
        
    def _prepare_portal_layout_values(self):
        """Prepare values for portal templates"""
        values = super(ITClient, self)._prepare_portal_layout_values()
        values.update({
            'client': self,
            'page_name': 'client',
        })
        return values
        
    def get_equipment_details(self):
        """Get equipment details for portal display"""
        self.ensure_one()
        equipment = self.env['it.equipment'].search([('client_id', '=', self.id)])
        today = fields.Date.today()
        return {
            'equipment': equipment,
            'count': len(equipment),
            'has_expired_warranty': any(eq.warranty_end_date and eq.warranty_end_date < today for eq in equipment if eq.warranty_end_date)
        }
        
    def get_contract_details(self):
        """Get contract details for portal display"""
        self.ensure_one()
        contracts = self.env['it.contract'].search([('client_id', '=', self.id)])
        return {
            'contracts': contracts,
            'count': len(contracts),
            'active_contracts': len(contracts.filtered(lambda c: c.state == 'active'))
        }
        
    def get_ticket_details(self):
        """Get ticket details for portal display"""
        self.ensure_one()
        tickets = self.env['helpdesk.ticket'].search([('partner_id', '=', self.partner_id.id)])
        return {
            'tickets': tickets,
            'count': len(tickets),
            'open_tickets': len(tickets.filtered(lambda t: t.stage_id.is_closed is False))
        }
        
    def get_subscription_details(self):
        """Get subscription details for portal display"""
        self.ensure_one()
        subscriptions = self.env['it.subscription'].search([('client_id', '=', self.id)])
        return {
            'subscriptions': subscriptions,
            'count': len(subscriptions),
            'active_subscriptions': len(subscriptions.filtered(lambda s: s.state == 'active'))
        }
        
    def get_invoice_details(self):
        """Get invoice details for portal display"""
        self.ensure_one()
        invoices = self.env['account.move'].search([
            ('partner_id', '=', self.partner_id.id),
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('state', '!=', 'cancel')
        ])
        return {
            'invoices': invoices,
            'count': len(invoices),
            'unpaid_invoices': len(invoices.filtered(lambda i: i.payment_state != 'paid')),
            'total_due': sum(invoices.filtered(lambda i: i.payment_state != 'paid').mapped('amount_residual'))
        }
        
    def action_delete_client(self):
        """Action to delete a client after checks"""
        self.ensure_one()
        # Check for related records that should prevent deletion
        if self.env['it.contract'].search_count([('client_id', '=', self.id), ('state', '=', 'active')]):
            raise models.UserError("Impossible de supprimer ce client car il possède des contrats actifs.")
            
        if self.env['helpdesk.ticket'].search_count([('client_id', '=', self.id), ('stage_id.is_closed', '=', False)]):
            raise models.UserError("Impossible de supprimer ce client car il possède des tickets ouverts.")
            
        if self.env['account.move'].search_count([('partner_id', '=', self.partner_id.id), 
                                                  ('move_type', 'in', ('out_invoice', 'out_refund')), 
                                                  ('payment_state', '!=', 'paid')]):
            raise models.UserError("Impossible de supprimer ce client car il possède des factures impayées.")
            
        # Archive related records instead of deleting them
        equipment = self.env['it.equipment'].search([('client_id', '=', self.id)])
        if equipment:
            equipment.write({'active': False})
            
        contracts = self.env['it.contract'].search([('client_id', '=', self.id)])
        if contracts:
            contracts.write({'active': False})
            
        subscriptions = self.env['it.subscription'].search([('client_id', '=', self.id)])
        if subscriptions:
            subscriptions.write({'active': False})
            
        # Actually delete the client
        return self.unlink()
        
    def unlink(self):
        """Override unlink to handle dependencies"""
        for client in self:
            # Check if client can be deleted
            if client.env.context.get('force_delete'):
                # Skip checks if force_delete is in context
                pass
            else:
                # Check for critical dependencies
                critical_dependencies = False
                critical_dependencies = critical_dependencies or client.env['it.contract'].search_count([('client_id', '=', client.id), ('state', '=', 'active')])
                critical_dependencies = critical_dependencies or client.env['helpdesk.ticket'].search_count([('client_id', '=', client.id), ('stage_id.is_closed', '=', False)])
                critical_dependencies = critical_dependencies or client.env['account.move'].search_count([('partner_id', '=', client.partner_id.id), 
                                                                                                        ('move_type', 'in', ('out_invoice', 'out_refund')), 
                                                                                                        ('payment_state', '!=', 'paid')])
                
                if critical_dependencies:
                    # Instead of deleting with critical dependencies, archive the client
                    client.write({'active': False, 'status': 'inactive'})
                    return True
        
        # Call parent implementation to actually delete records
        return super(ITClient, self).unlink()