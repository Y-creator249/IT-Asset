from odoo import http, fields
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.exceptions import AccessError, MissingError, UserError
from collections import OrderedDict
from odoo.tools.translate import _
from werkzeug.urls import url_encode
import logging

_logger = logging.getLogger(__name__)

class ITAssetPortal(CustomerPortal):
    # Nombre d'éléments par page pour la pagination
    _items_per_page = 10
    
    # Route pour la page d'accueil personnalisée après inscription
    @http.route(['/client/welcome'], type='http', auth="user", website=True)
    def client_welcome(self, **kw):
        partner = request.env.user.partner_id
        client = request.env['it.client'].sudo().search([('partner_id', '=', partner.id)], limit=1)
        
        # Si l'utilisateur n'a pas de client IT associé, nous le créons automatiquement
        if not client and partner:
            client_vals = {
                'name': partner.name,
                'partner_id': partner.id,
                'email': partner.email or request.env.user.login,
                'phone': partner.phone or '',
                'client_type': 'enterprise',
                'status': 'active',
                'onboarding_date': fields.Date.today(),
            }
            
            # Création du client IT
            client = request.env['it.client'].sudo().create(client_vals)
            _logger.info(f"Création automatique d'un client IT (ID: {client.id}) pour l'utilisateur {request.env.user.login} depuis client_welcome")
        
        # Préparation des valeurs pour le template
        values = self._prepare_portal_layout_values()
        
        # Ajout des compteurs pour le dashboard personnalisé
        counters = ['equipment_count', 'contract_count', 'subscription_count', 'incident_count', 'invoice_count']
        values.update(self._prepare_home_portal_values(counters))
        
        # Ajout du client pour l'affichage du nom
        values['client'] = client
        values['page_name'] = 'client_welcome'
        
        return request.render("it_asset_management.client_welcome_page", values)
    
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id

        # Compteurs pour le dashboard
        if 'equipment_count' in counters:
            values['equipment_count'] = request.env['it.equipment'].search_count([
                ('client_id.partner_id', '=', partner.id)
            ])
        if 'contract_count' in counters:
            values['contract_count'] = request.env['it.contract'].search_count([
                ('partner_id', '=', partner.id)
            ])
        if 'subscription_count' in counters:
            values['subscription_count'] = request.env['sale.subscription'].search_count([
                ('partner_id', '=', partner.id)
            ])
        if 'incident_count' in counters:
            values['incident_count'] = request.env['it.incident'].search_count([
                ('client_id.partner_id', '=', partner.id)
            ])
        if 'invoice_count' in counters:
            values['invoice_count'] = request.env['account.move'].search_count([
                ('partner_id', '=', partner.id),
                ('move_type', 'in', ('out_invoice', 'out_refund')),
                ('state', 'not in', ('draft', 'cancel'))
            ])
        
        return values

    # DASHBOARD avec redirection vers notre formulaire personnalisé
    @http.route(['/my', '/my/home'], type='http', auth="user", website=True)
    def home(self, **kw):
        # Vérifier si l'utilisateur a un client IT associé
        partner = request.env.user.partner_id
        client = request.env['it.client'].sudo().search([('partner_id', '=', partner.id)], limit=1)
        
        # Si l'utilisateur n'a pas de client IT associé, nous le créons automatiquement
        if not client and partner:
            client_vals = {
                'name': partner.name,
                'partner_id': partner.id,
                'email': partner.email or request.env.user.login,
                'phone': partner.phone or '',
                'client_type': 'enterprise',
                'status': 'active',
                'onboarding_date': fields.Date.today(),
            }
            
            # Création du client IT
            client = request.env['it.client'].sudo().create(client_vals)
            # Log via le logger standard plutôt que via ir.logging
            _logger.info(f"Création automatique d'un client IT (ID: {client.id}) pour l'utilisateur {request.env.user.login} depuis portal.home")
            
        # Afficher le dashboard
        values = self._prepare_portal_layout_values()
        return request.render("it_asset_management.portal_dashboard", values)

    # ÉQUIPEMENTS
    @http.route(['/my/equipements', '/my/equipements/page/<int:page>'], type='http', auth="user", website=True)
    def portal_equipements(self, page=1, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        
        # Recherche des équipements
        EquipmentObj = request.env['it.equipment']
        domain = [('client_id.partner_id', '=', partner.id)]
        
        # Pagination
        equipment_count = EquipmentObj.search_count(domain)
        pager = portal_pager(
            url="/my/equipements",
            total=equipment_count,
            page=page,
            step=self._items_per_page
        )
        
        # Options de tri
        order = 'name'  # Par défaut, tri par nom
        if sortby == 'date':
            order = 'purchase_date desc'
        elif sortby == 'warranty':
            order = 'warranty_end'
        
        # Récupération des équipements
        equipments = EquipmentObj.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        
        values.update({
            'equipments': equipments,
            'page_name': 'equipements',
            'pager': pager,
            'default_url': '/my/equipements',
            'sortby': sortby,
        })
        return request.render("it_asset_management.portal_equipements", values)
    
    @http.route(['/my/equipement/<int:equipment_id>'], type='http', auth="user", website=True)
    def portal_equipement_detail(self, equipment_id, **kw):
        try:
            equipment_sudo = self._document_check_access('it.equipment', equipment_id)
        except (AccessError, MissingError):
            return request.redirect('/my')
            
        values = {
            'equipment': equipment_sudo,
            'page_name': 'equipement_detail',
        }
        return request.render("it_asset_management.portal_equipement_detail", values)

    # CONTRATS
    @http.route(['/my/contrats', '/my/contrats/page/<int:page>'], type='http', auth="user", website=True)
    def portal_contrats(self, page=1, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        
        # Recherche des contrats
        ContractObj = request.env['it.contract']
        domain = [('partner_id', '=', partner.id)]
        
        # Pagination
        contract_count = ContractObj.search_count(domain)
        pager = portal_pager(
            url="/my/contrats",
            total=contract_count,
            page=page,
            step=self._items_per_page
        )
        
        # Options de tri
        order = 'name'  # Par défaut, tri par nom
        if sortby == 'date':
            order = 'date_start desc'
        elif sortby == 'expiry':
            order = 'date_end'
        
        # Récupération des contrats
        contracts = ContractObj.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        
        values.update({
            'contracts': contracts,
            'page_name': 'contrats',
            'pager': pager,
            'default_url': '/my/contrats',
            'sortby': sortby,
        })
        return request.render("it_asset_management.portal_contrats", values)
    
    @http.route(['/my/contrat/<int:contract_id>'], type='http', auth="user", website=True)
    def portal_contrat_detail(self, contract_id, **kw):
        try:
            contract_sudo = self._document_check_access('it.contract', contract_id)
        except (AccessError, MissingError):
            return request.redirect('/my')
            
        values = {
            'contract': contract_sudo,
            'page_name': 'contrat_detail',
        }
        return request.render("it_asset_management.portal_contrat_detail", values)

    # ABONNEMENTS
    @http.route(['/my/abonnements', '/my/abonnements/page/<int:page>'], type='http', auth="user", website=True)
    def portal_abonnements(self, page=1, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        
        # Vérifier si le module de souscription est installé
        if 'sale.subscription' not in request.env:
            pager = portal_pager(
                url="/my/abonnements",
                total=0,
                page=page,
                step=self._items_per_page
            )
            
            values.update({
                'subscriptions': [],
                'page_name': 'abonnements',
                'subscription_count': 0,
                'module_missing': True,
                'pager': pager,
                'default_url': '/my/abonnements',
                'sortby': sortby
            })
            return request.render("it_asset_management.portal_abonnements", values)
        
        # Recherche des abonnements
        SubscriptionObj = request.env['sale.subscription']
        domain = [('partner_id', '=', partner.id)]
        
        # Pagination
        subscription_count = SubscriptionObj.search_count(domain)
        pager = portal_pager(
            url="/my/abonnements",
            total=subscription_count,
            page=page,
            step=self._items_per_page
        )
        
        # Options de tri
        order = 'name'  # Par défaut, tri par nom
        if sortby == 'date':
            order = 'date_start desc'
        elif sortby == 'state':
            order = 'state'
        
        # Récupération des abonnements
        subscriptions = SubscriptionObj.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        
        values.update({
            'subscriptions': subscriptions,
            'page_name': 'abonnements',
            'pager': pager,
            'default_url': '/my/abonnements',
            'sortby': sortby,
        })
        return request.render("it_asset_management.portal_abonnements", values)
    
    @http.route(['/my/abonnement/<int:subscription_id>'], type='http', auth="user", website=True)
    def portal_abonnement_detail(self, subscription_id, **kw):
        try:
            subscription_sudo = self._document_check_access('sale.subscription', subscription_id)
        except (AccessError, MissingError):
            return request.redirect('/my')
            
        values = {
            'subscription': subscription_sudo,
            'page_name': 'abonnement_detail',
        }
        return request.render("it_asset_management.portal_abonnement_detail", values)

    # INCIDENTS
    @http.route(['/my/incidents', '/my/incidents/page/<int:page>'], type='http', auth="user", website=True)
    def portal_incidents(self, page=1, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        
        # Récupération du client lié au partenaire
        client = request.env['it.client'].search([('partner_id', '=', partner.id)], limit=1)
        
        if not client:
            # Si pas de client, afficher une page vide mais ne pas rediriger
            # Créer un pager vide pour éviter les erreurs de template
            pager = portal_pager(
                url="/my/incidents",
                total=0,
                page=page,
                step=self._items_per_page
            )
            
            values.update({
                'incidents': [],
                'page_name': 'incidents',
                'default_url': '/my/incidents',
                'sortby': sortby,
                'client': False,
                'equipment_ids': [],
                'pager': pager,
            })
            return request.render("it_asset_management.portal_incidents", values)
        
        # Recherche des incidents
        IncidentObj = request.env['it.incident']
        domain = [('client_id', '=', client.id)]
        
        # Pagination
        incident_count = IncidentObj.search_count(domain)
        pager = portal_pager(
            url="/my/incidents",
            total=incident_count,
            page=page,
            step=self._items_per_page
        )
        
        # Options de tri
        order = 'date_reported desc'  # Par défaut, tri par date
        if sortby == 'name':
            order = 'name'
        elif sortby == 'state':
            order = 'state, date_reported desc'
        elif sortby == 'priority':
            order = 'priority, date_reported desc'
        
        # Récupération des incidents
        incidents = IncidentObj.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        
        # Récupération des équipements pour le formulaire de création
        equipment_ids = request.env['it.equipment'].search([('client_id', '=', client.id)])
        
        values.update({
            'incidents': incidents,
            'page_name': 'incidents',
            'pager': pager,
            'default_url': '/my/incidents',
            'sortby': sortby,
            'client': client,
            'equipment_ids': equipment_ids,
        })
        return request.render("it_asset_management.portal_incidents", values)
    
    @http.route(['/my/incident/<int:incident_id>'], type='http', auth="user", website=True)
    def portal_incident_detail(self, incident_id, **kw):
        try:
            incident_sudo = self._document_check_access('it.incident', incident_id)
        except (AccessError, MissingError):
            return request.redirect('/my')
            
        values = {
            'incident': incident_sudo,
            'page_name': 'incident_detail',
        }
        return request.render("it_asset_management.portal_incident_detail", values)
    
    @http.route(['/my/incident/create'], type='http', auth="user", website=True)
    def portal_create_incident(self, **kw):
        partner = request.env.user.partner_id
        client = request.env['it.client'].search([('partner_id', '=', partner.id)], limit=1)
        
        if not client:
            values = self._prepare_portal_layout_values()
            values.update({
                'page_name': 'create_incident',
                'client': False,
                'equipment_ids': [],
                'no_client_message': True
            })
            return request.render("it_asset_management.portal_create_incident", values)
        
        equipment_ids = request.env['it.equipment'].search([('client_id', '=', client.id)])
        
        values = {
            'page_name': 'create_incident',
            'client': client,
            'equipment_ids': equipment_ids,
        }
        return request.render("it_asset_management.portal_create_incident", values)
    
    @http.route(['/my/incident/submit'], type='http', auth="user", website=True)
    def portal_submit_incident(self, **post):
        partner = request.env.user.partner_id
        client = request.env['it.client'].search([('partner_id', '=', partner.id)], limit=1)
        
        if not client:
            return request.redirect('/my')
        
        vals = {
            'client_id': client.id,
            'description': post.get('description'),
            'priority': post.get('priority', 'medium'),
            'state': 'new',
            'date_reported': fields.Datetime.now(),
        }
        
        if post.get('equipment_id'):
            vals['equipment_id'] = int(post.get('equipment_id'))
        
        incident = request.env['it.incident'].sudo().create(vals)
        
        return request.redirect('/my/incident/%s' % incident.id)

    # FACTURES
    @http.route(['/my/factures', '/my/factures/page/<int:page>'], type='http', auth="user", website=True)
    def portal_factures(self, page=1, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        
        # Recherche des factures
        AccountMoveObj = request.env['account.move']
        domain = [
            ('partner_id', '=', partner.id),
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('state', 'not in', ('draft', 'cancel'))
        ]
        
        # Pagination
        invoice_count = AccountMoveObj.search_count(domain)
        pager = portal_pager(
            url="/my/factures",
            total=invoice_count,
            page=page,
            step=self._items_per_page
        )
        
        # Options de tri
        order = 'date desc, name desc'  # Par défaut, tri par date
        if sortby == 'name':
            order = 'name desc'
        elif sortby == 'state':
            order = 'state, date desc'
        
        # Récupération des factures
        invoices = AccountMoveObj.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        
        values.update({
            'invoices': invoices,
            'page_name': 'factures',
            'pager': pager,
            'default_url': '/my/factures',
            'sortby': sortby,
        })
        return request.render("it_asset_management.portal_factures", values)
    
    # Route pour créer rapidement un compte client depuis le portail
    @http.route(['/portal/create_client'], type='http', auth="user", website=True)
    def portal_create_client(self, **kw):
        """Permet à un utilisateur authentifié de créer un client facilement depuis le portail"""
        values = {}
        
        # Si c'est une requête GET, afficher le formulaire
        if request.httprequest.method == 'GET':
            values = self._prepare_portal_layout_values()
            return request.render("it_asset_management.portal_create_client", values)
        
        # Si c'est une requête POST, traiter les données
        if request.httprequest.method == 'POST':
            # Récupérer l'utilisateur connecté
            user = request.env.user
            
            # Préparer les valeurs pour le client
            client_vals = {
                'name': kw.get('name') or user.partner_id.name,
                'partner_id': user.partner_id.id,
                'email': kw.get('email') or user.partner_id.email or user.login,
                'phone': kw.get('phone') or user.partner_id.phone or '',
                'client_type': kw.get('client_type', 'enterprise'),
                'status': 'active',
                'onboarding_date': fields.Date.today(),
            }
            
            # Vérifier si un client existe déjà pour ce partenaire
            existing_client = request.env['it.client'].sudo().search([('partner_id', '=', user.partner_id.id)], limit=1)
            
            # Si un client existe déjà, mettre à jour ses informations
            if existing_client:
                existing_client.sudo().write({
                    'name': client_vals['name'],
                    'email': client_vals['email'],
                    'phone': client_vals['phone'],
                    'client_type': client_vals['client_type'],
                })
                _logger.info(f"Client IT mis à jour: {existing_client.id} pour l'utilisateur {user.login}")
                message = "Votre profil client a été mis à jour avec succès!"
            # Sinon, créer un nouveau client
            else:
                new_client = request.env['it.client'].sudo().create(client_vals)
                _logger.info(f"Client IT créé: {new_client.id} pour l'utilisateur {user.login}")
                message = "Votre compte client a été créé avec succès!"
            
            # Retourner au tableau de bord avec un message de succès
            return request.redirect('/my?client_created=1&message=' + message)
            
    # MÉTHODE HELPER POUR VÉRIFIER L'ACCÈS AUX DOCUMENTS
    def _document_check_access(self, model_name, document_id, access_token=None):
        document = request.env[model_name].browse([document_id])
        document_sudo = document.sudo().exists()
        if not document_sudo:
            raise MissingError(_("Ce document n'existe pas."))
            
        if model_name == 'it.equipment':
            if document_sudo.client_id.partner_id != request.env.user.partner_id:
                raise AccessError(_("Vous n'avez pas accès à ce document."))
        elif model_name == 'it.contract':
            if document_sudo.partner_id != request.env.user.partner_id:
                raise AccessError(_("Vous n'avez pas accès à ce document."))
        elif model_name == 'it.incident':
            if document_sudo.client_id.partner_id != request.env.user.partner_id:
                raise AccessError(_("Vous n'avez pas accès à ce document."))
        else:  # Pour les abonnements et autres modèles
            document_sudo.check_access_rights('read')
            document_sudo.check_access_rule('read')
            
        return document_sudo