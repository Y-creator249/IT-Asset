from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ITBilling(models.Model):
    _name = 'it.billing'
    _description = 'Facturation IT'
    _inherit = ['mail.thread']

    name = fields.Char('Numéro de facture', required=True, copy=False, tracking=True)
    contract_id = fields.Many2one('it.contract', string='Contrat', required=True, tracking=True)
    client_id = fields.Many2one('it.client', string='Client', related='contract_id.client_id', store=True, tracking=True)
    invoice_id = fields.Many2one('account.move', string='Facture', readonly=True)
    amount = fields.Monetary(string='Montant', related='contract_id.amount', store=True)
    currency_id = fields.Many2one('res.currency', string='Devise', related='contract_id.currency_id')
    billing_date = fields.Date(string='Date de facturation', required=True, default=fields.Date.today)
    frequency = fields.Selection([
        ('monthly', 'Mensuel'),
        ('quarterly', 'Trimestriel'),
        ('yearly', 'Annuel')
    ], string='Fréquence', required=True, default='monthly')
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('invoiced', 'Facturé'),
        ('paid', 'Payé'),
        ('cancelled', 'Annulé')
    ], string='État', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('it.billing') or 'Nouveau'
        return super().create(vals_list)


    def action_generate_invoice(self):
        for record in self:
            if record.state != 'draft':
                continue

            # Récupérer le journal des ventes
            journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
            if not journal:
                raise UserError(_("Aucun journal de vente n'a été trouvé."))

            # Récupérer ou créer le produit de service
            product = self.env['product.product'].search([('name', '=', 'Service IT')], limit=1)
            if not product:
                product = self.env['product.product'].create({
                    'name': 'Service IT',
                    'type': 'service',
                    'invoice_policy': 'order',
                })

            # Récupérer le compte comptable
            account = product.property_account_income_id or \
                     product.categ_id.property_account_income_categ_id or \
                     self.env['account.account'].search([('code', '=', '706000')], limit=1)

            if not account:
                raise UserError(_("Veuillez configurer un compte de revenus pour le produit 'Service IT' ou sa catégorie."))

            invoice_vals = {
                'move_type': 'out_invoice',
                'partner_id': record.client_id.partner_id.id,
                'invoice_date': record.billing_date,
                'journal_id': journal.id,
                'invoice_line_ids': [(0, 0, {
                    'product_id': product.id,
                    'name': f"Facturation {record.contract_id.name}",
                    'quantity': 1,
                    'price_unit': record.amount,
                    'account_id': account.id,
                })],
            }

            try:
                invoice = self.env['account.move'].create(invoice_vals)
                record.write({
                    'invoice_id': invoice.id,
                    'state': 'invoiced'
                })
            except Exception as e:
                raise UserError(_("Erreur lors de la création de la facture: %s") % str(e))

            return {
                'type': 'ir.actions.act_window',
                'name': _('Facture générée'),
                'res_model': 'account.move',
                'res_id': invoice.id,
                'view_mode': 'form',
            }

    @api.model
    def _cron_generate_billings(self):
        today = fields.Date.today()
        contracts = self.env['it.contract'].search([
            ('state', '=', 'confirmed'),
            ('date_end', '>=', today)
        ])
        for contract in contracts:
            last_billing = self.search([
                ('contract_id', '=', contract.id),
                ('state', 'in', ['invoiced', 'paid'])
            ], order='billing_date desc', limit=1)
            if not last_billing or self._check_next_billing_date(last_billing):
                self.create({
                    'contract_id': contract.id,
                    'billing_date': today,
                    'frequency': contract.contract_type == 'maintenance' and 'monthly' or 'yearly'
                })

    def _check_next_billing_date(self, last_billing):
        from datetime import datetime
        from dateutil.relativedelta import relativedelta
        last_date = last_billing.billing_date
        today = fields.Date.today()
        if last_billing.frequency == 'monthly':
            next_date = last_date + relativedelta(months=1)
        elif last_billing.frequency == 'quarterly':
            next_date = last_date + relativedelta(months=3)
        else:  # yearly
            next_date = last_date + relativedelta(years=1)
        return today >= next_date