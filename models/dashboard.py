from odoo import models, fields, api
from datetime import datetime, timedelta

class ITAssetDashboard(models.Model):
    _name = 'it.asset.dashboard'
    _description = 'IT Asset Management Dashboard'

    @api.model
    def get_dashboard_data(self):
        """Fetch dashboard data for IT Asset Management"""
        # Current month date range
        today = fields.Date.today()
        first_day_month = today.replace(day=1)
        last_month = first_day_month - timedelta(days=1)
        first_day_last_month = last_month.replace(day=1)
        
        # Get counts from different models
        equipment_count = self.env['it.equipment'].search_count([])
        contract_count = self.env['it.contract'].search_count([])
        revenue = sum(self.env['it.billing'].search([]).mapped('amount_total'))
        avg_contract_value = revenue / contract_count if contract_count else 0
        
        # Calculate percentage changes
        equipment_last_month = self.env['it.equipment'].search_count([
            ('create_date', '<', first_day_month)
        ])
        equipment_change = round(((equipment_count - equipment_last_month) / equipment_last_month * 100) 
                                if equipment_last_month else 0, 1)
        
        contract_last_month = self.env['it.contract'].search_count([
            ('create_date', '<', first_day_month)
        ])
        contract_change = round(((contract_count - contract_last_month) / contract_last_month * 100) 
                               if contract_last_month else 0, 1)
        
        # Top clients by equipment count
        top_clients_by_equipment = self.env['it.client'].search_read(
            [], ['name', 'equipment_count'], limit=5, order='equipment_count DESC')
        
        # Top clients by contract value
        top_clients_by_contract = self.env['it.client'].search_read(
            [], ['name', 'contract_total'], limit=5, order='contract_total DESC')
        
        # Monthly data for chart
        months = []
        revenue_data = []
        
        # Get data for the last 6 months
        for i in range(5, -1, -1):
            month_date = first_day_month - timedelta(days=30*i)
            month_name = month_date.strftime('%B %Y')
            months.append(month_name)
            
            month_start = month_date.replace(day=1)
            if i > 0:
                next_month = month_date.replace(day=1) + timedelta(days=32)
                month_end = next_month.replace(day=1) - timedelta(days=1)
            else:
                month_end = today
                
            monthly_revenue = sum(self.env['it.billing'].search([
                ('invoice_date', '>=', month_start),
                ('invoice_date', '<=', month_end)
            ]).mapped('amount_total'))
            
            revenue_data.append(monthly_revenue)
        
        return {
            'counts': {
                'equipment': equipment_count,
                'contracts': contract_count,
                'revenue': revenue,
                'avg_contract': avg_contract_value,
            },
            'changes': {
                'equipment_change': equipment_change,
                'contract_change': contract_change,
                'revenue_change': 0,  # Calculate based on your needs
                'avg_contract_change': 0,  # Calculate based on your needs
            },
            'top_clients_equipment': top_clients_by_equipment,
            'top_clients_contract': top_clients_by_contract,
            'chart_data': {
                'months': months,
                'revenue': revenue_data,
            }
        } 