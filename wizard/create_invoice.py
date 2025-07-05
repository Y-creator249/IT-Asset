from odoo import models, fields, api, _
from odoo.exceptions import UserError

class CreateInvoiceWizard(models.TransientModel):
    _name = 'it.create.invoice.wizard' 
    _description = 'Assistant de création de facture'

    contract_id = fields.Many2one('it.contract', string='Contrat', required=True)
    date = fields.Date(string='Date de facturation', default=fields.Date.today, required=True)
    amount = fields.Float(string='Montant', required=True)
    description = fields.Text(string='Description')

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if self._context.get('active_id'):
            contract = self.env['it.contract'].browse(self._context.get('active_id'))
            res.update({
                'contract_id': contract.id,
                'amount': contract.amount,
            })
        return res

    def action_create_invoice(self):
        self.ensure_one()
        # Récupérer le journal des ventes
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        if not journal:
            # Essayer de créer un journal de vente
            try:
                journal = self.env['account.journal'].create({
                    'name': 'Ventes IT',
                    'code': 'VITJ',
                    'type': 'sale',
                    'company_id': self.env.company.id,
                })
            except Exception as e:
                raise UserError(_("Aucun journal de vente n'a été trouvé et impossible d'en créer un. Veuillez en créer un dans Comptabilité > Configuration > Journaux comptables.\n\nErreur: %s") % str(e))
        
        # Récupérer le compte produit par défaut
        product_account = self.env['ir.property']._get('property_account_income_id', 'product.template')
        if not product_account:
            product_account = self.env['ir.property']._get('property_account_income_categ_id', 'product.category')

        # En dernier recours, essayer de trouver le compte 706000 (vente de prestations)
        if not product_account:
            product_account = self.env['account.account'].search([('code', 'like', '70%'), ('deprecated', '=', False)], limit=1)

        if not product_account:
            raise UserError(_("Veuillez configurer un compte produit par défaut dans la configuration comptable."))

        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.contract_id.client_id.partner_id.id,
            'invoice_date': self.date,
            'journal_id': journal.id,
            'invoice_line_ids': [(0, 0, {
                'name': self.description or f"Facturation contrat {self.contract_id.name}",
                'quantity': 1,
                'price_unit': self.amount,
                'account_id': product_account.id,
            })],
        }
        
        try:
            invoice = self.env['account.move'].create(invoice_vals)
        except Exception as e:
            raise UserError(_("Erreur lors de la création de la facture: %s") % str(e))
            
        return {
            'name': _('Facture'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
        }