import werkzeug
import odoo
import logging
from werkzeug.urls import url_encode
from datetime import datetime

from odoo import http, tools, _, fields
from odoo.http import request
from odoo.addons.web.controllers.home import ensure_db, Home
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class ITAssetAuthSignup(AuthSignupHome):
    
    # Helper pour s'assurer que l'inscription est activée
    def _ensure_signup_allowed(self):
        """Force l'activation de l'inscription si elle n'est pas déjà activée"""
        try:
            # Utiliser une requête SQL directe pour mettre à jour le paramètre sans problème de transaction
            # Cette approche évite les problèmes de concurrence et de contraintes uniques
            request.env.cr.execute("""
                UPDATE ir_config_parameter
                SET value = 'True'
                WHERE key = 'auth_signup.allow_uninvited'
                  AND value != 'True'
            """)
            
            # Si des lignes ont été mises à jour, on commit tout de suite
            if request.env.cr.rowcount:
                _logger.info("Activation de l'inscription libre des utilisateurs")
                request.env.cr.commit()
            
            # Vérification que le paramètre est bien activé
            allow_signup = request.env['ir.config_parameter'].sudo().get_param('auth_signup.allow_uninvited') == 'True'
            if not allow_signup:
                # Si toujours pas activé, on insère directement
                request.env.cr.execute("""
                    INSERT INTO ir_config_parameter (key, value, create_uid, write_uid, create_date, write_date)
                    SELECT 'auth_signup.allow_uninvited', 'True', 1, 1, now(), now()
                    WHERE NOT EXISTS (SELECT 1 FROM ir_config_parameter WHERE key = 'auth_signup.allow_uninvited')
                """)
                request.env.cr.commit()
                _logger.info("Insertion de l'inscription libre des utilisateurs")
                
            return True
        except Exception as e:
            # Éviter l'interpolation de chaîne qui pourrait causer une récursion de log
            _logger.error("Erreur lors de l'activation de l'inscription libre: %s", str(e))
            # On continue même en cas d'erreur
            return True
    
    # Route personnalisée pour la déconnexion
    @http.route('/it/logout', type='http', auth="public", website=True)
    def it_logout(self, **kw):
        request.session.logout(keep_db=True)
        return request.redirect('/web/login')
    
    # Surcharge de la méthode web_auth_signup pour adapter le processus d'inscription
    @http.route('/web/signup', type='http', auth='public', website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):
        # S'assurer que l'inscription est activée
        self._ensure_signup_allowed()
        
        # Si c'est une requête POST, rediriger vers client_register
        if request.httprequest.method == 'POST':
            _logger.info(f"Redirection de /web/signup vers client_register avec: {kw}")
            return self.client_register(**kw)
            
        # Sinon, continuer avec le comportement normal
        redirect_url = '/my'
        kw['redirect'] = redirect_url
            
        # Préparation du contexte pour le template
        qcontext = self.get_auth_signup_qcontext()
        qcontext.update({'redirect': redirect_url})
        
        # Si l'utilisateur veut s'inscrire directement
        if 'type' not in qcontext and request.httprequest.method == 'POST':
            try:
                # Faire l'inscription
                self.do_signup(qcontext)
                
                # Connecter l'utilisateur directement
                login = qcontext.get('login')
                password = qcontext.get('password')
                
                _logger.info(f"Tentative d'authentification avec le login: {login}")
                request.env.cr.commit()  # S'assurer que l'utilisateur est bien créé avant la connexion
                
                # La méthode authenticate n'accepte que 2 paramètres: dbname et credential (un dict)
                credential = {'login': login, 'password': password}
                uid = request.session.authenticate(request.db, credential)
                
                if uid:
                    _logger.info(f"Authentification réussie avec uid={uid}")
                    # S'assurer qu'un client IT est créé
                    user = request.env['res.users'].sudo().browse(uid)
                    existing_client = request.env['it.client'].sudo().search([('partner_id', '=', user.partner_id.id)], limit=1)
                    
                    if not existing_client:
                        # Créer le client IT
                        client_vals = {
                            'name': user.partner_id.name,
                            'partner_id': user.partner_id.id,
                            'email': user.partner_id.email or login,
                            'phone': user.partner_id.phone or '',
                            'client_type': qcontext.get('client_type', 'enterprise'),
                            'status': 'active',
                            'onboarding_date': fields.Date.today(),
                        }
                        new_client = request.env['it.client'].sudo().create(client_vals)
                        _logger.info(f"Création automatique d'un client IT (ID: {new_client.id}) pour l'utilisateur {login}")
                    
                    # FORCER la redirection vers le portail client avec werkzeug
                    _logger.info(f"Redirection forceée vers {redirect_url} après inscription réussie")
                    response = werkzeug.utils.redirect(redirect_url, 303)  # Code 303 force la redirection
                    return response
                else:
                    _logger.error(f"Authentification échouée pour {login} après inscription")
            except Exception as e:
                _logger.error(f"Erreur lors de l'inscription: {str(e)}")
                qcontext['error'] = str(e)
        
        # Ajouter le type de client au contexte pour le formulaire d'inscription
        if 'client_types' not in qcontext:
            qcontext['client_types'] = [('enterprise', 'Entreprise'), ('government', 'Gouvernement'), 
                                      ('education', 'Éducation'), ('nonprofit', 'Association'), 
                                      ('individual', 'Particulier')]
                
        # Ajout d'un indicateur pour le template
        qcontext['form_view'] = 'signup'
        
        response = request.render('it_asset_management.client_auth_form', qcontext)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
        return response
    
    # Surcharge de _signup_with_values pour créer automatiquement un client IT
    def _signup_with_values(self, token, values):
        # Extraction et sauvegarde des valeurs client IT avant de les supprimer
        client_vals = {
            'client_type': values.pop('client_type', 'enterprise'),
            'phone': values.pop('phone', ''),
            'company_name': values.pop('company_name', '')
        }
        
        # Appel de la méthode d'origine pour créer l'utilisateur
        login, password = request.env['res.users'].sudo().with_context(it_asset_portal=True).signup(values, token)
        request.env.cr.commit()     # commit pour finaliser la création de l'utilisateur
        
        # Authentifier l'utilisateur
        # La méthode authenticate n'accepte que 2 paramètres: dbname et credential (un dict)
        credential = {'login': login, 'password': password}
        uid = request.session.authenticate(request.db, credential)
        
        if uid:
            # Récupérer l'utilisateur et créer un client IT s'il n'existe pas déjà
            user = request.env['res.users'].sudo().browse(uid)
            
            # Vérifier si un client IT existe déjà pour ce partenaire
            existing_client = request.env['it.client'].sudo().search([('partner_id', '=', user.partner_id.id)], limit=1)
            
            if not existing_client:
                # Préparation des valeurs pour le client IT
                new_client_vals = {
                    'name': client_vals.get('company_name') or user.partner_id.name,
                    'partner_id': user.partner_id.id,
                    'email': user.partner_id.email or user.login,
                    'phone': client_vals.get('phone', ''),
                    'client_type': client_vals.get('client_type', 'enterprise'),
                    'status': 'active',
                    'onboarding_date': fields.Date.today(),
                }
                
                # Création du client IT
                new_client = request.env['it.client'].sudo().create(new_client_vals)
                _logger.info(f"Création automatique d'un client IT (ID: {new_client.id}) pour l'utilisateur {login}")
            
            _logger.info(f"Utilisateur {login} inscrit et redirigé vers le portail client")
        else:
            _logger.error(f"Erreur lors de l'authentification de l'utilisateur {login} après inscription")

        
    # Page de création directe de compte
    @http.route('/client/direct_signup', type='http', auth="public", website=True)
    def direct_signup_page(self, **kw):
        values = {
            'error': kw.get('error'),
            'success': kw.get('success'),
        }
        return request.render('it_asset_management.direct_signup_page', values)
        
    # Traitement du formulaire de création directe
    @http.route('/client/direct_create', type='http', auth="public", website=True)
    def direct_create(self, **kw):
        try:
            # S'assurer que l'inscription est activée
            self._ensure_signup_allowed()
            
            # Sauvegarde des valeurs client IT
            company_name = kw.get('company_name', '')
            
            # Vérifier si l'email existe déjà dans le système
            email = kw.get('email')
            existing_user = request.env['res.users'].sudo().search([('login', '=', email)], limit=1)
            if existing_user:
                error = f"Un compte existe déjà avec cet email ({email})."
                return request.redirect(f'/client/direct_signup?error={error}')
            
            # Préparation des valeurs pour l'inscription (uniquement les champs valides pour res.users)
            values = {
                'login': kw.get('email'),
                'name': kw.get('name'),
                'password': kw.get('password'),
            }
            
            # Création de l'utilisateur
            db = request.db
            login, password = request.env['res.users'].sudo().with_context(it_asset_portal=True).signup(values, None)
            
            # Authentification automatique
            request.env.cr.commit()  # Important pour que les modifications soient persistées
            # La méthode authenticate n'accepte que 2 paramètres: dbname et credential (un dict)
            credential = {'login': login, 'password': password}
            uid = request.session.authenticate(db, credential)
            
            if not uid:
                return request.redirect('/client/direct_signup?error=Échec de connexion après inscription')
            
            # Récupération des détails de l'utilisateur
            user = request.env['res.users'].sudo().browse(uid)
            
            # Création du client IT
            client_vals = {
                'name': company_name or user.partner_id.name,
                'partner_id': user.partner_id.id,
                'email': user.partner_id.email or user.login,
                'phone': kw.get('phone', ''),
                'client_type': 'enterprise',  # Type par défaut
                'status': 'active',
                'onboarding_date': fields.Date.today(),
            }
            
            # Création du client IT
            client = request.env['it.client'].sudo().create(client_vals)
            
            # Redirection vers le tableau de bord client
            _logger.info(f"Client IT créé avec succès via création directe: {client.id}")
            return werkzeug.utils.redirect('/my')
            
        except Exception as e:
            _logger.error("Erreur lors de la création directe: %s", str(e))
            return request.redirect(f'/client/direct_signup?error={werkzeug.urls.url_quote(str(e))}')
    
    # Création rapide d'un compte client
    @http.route('/client/express_create', type='http', auth="public", website=True)
    def express_create(self, **kw):
        try:
            # S'assurer que l'inscription est activée
            self._ensure_signup_allowed()
            
            # Récupération et validation des données
            email = kw.get('email')
            if not email or '@' not in email:
                return request.redirect('/client/direct_signup?error=Email invalide')
            
            # Vérifier si l'email existe déjà dans le système
            existing_user = request.env['res.users'].sudo().search([('login', '=', email)], limit=1)
            if existing_user:
                error = f"Un compte existe déjà avec cet email ({email})."
                return request.redirect(f'/client/direct_signup?error={error}')
                
            # Génération d'un mot de passe par défaut
            password = 'Express123'  # Mot de passe temporaire
            
            # Préparation des valeurs pour l'inscription
            values = {
                'login': email,
                'name': kw.get('name') or email.split('@')[0],
                'password': password,
            }
            
            # Création de l'utilisateur
            db = request.db
            login, password = request.env['res.users'].sudo().with_context(it_asset_portal=True).signup(values, None)
            
            # Authentification automatique
            request.env.cr.commit()
            # La méthode authenticate n'accepte que 2 paramètres: dbname et credential (un dict)
            credential = {'login': login, 'password': password}
            uid = request.session.authenticate(db, credential)
            
            if not uid:
                return request.redirect('/client/direct_signup?error=Échec de connexion après création express')
            
            # Récupération des détails de l'utilisateur
            user = request.env['res.users'].sudo().browse(uid)
            
            # Création du client IT
            client_vals = {
                'name': f"Entreprise {values['name'].upper()}",
                'partner_id': user.partner_id.id,
                'email': email,
                'phone': '',
                'client_type': 'enterprise',  # Type par défaut pour la création express
                'status': 'active',
                'onboarding_date': fields.Date.today(),
            }
            
            # Création du client
            client = request.env['it.client'].sudo().create(client_vals)
            request.env.cr.commit()
            
            _logger.info(f"Client IT express créé: {client.id} pour le partenaire {user.partner_id.id}")
            success_message = f"Compte express créé avec succès! Email: {email} | Mot de passe: {password}"
            
            # Redirection vers le portail client
            return werkzeug.utils.redirect('/my')
            
        except Exception as e:
            _logger.error("Exception lors de la création express: %s", str(e))
            return request.redirect(f'/client/direct_signup?error={werkzeug.urls.url_quote(str(e))}')

        
    # Nouvelle route pour l'inscription client directe
    @http.route('/client/register', type='http', auth="public", website=True)
    def client_register(self, **kw):
        """
        Traitement du formulaire d'inscription client personnalisé.
        Gère le processus d'inscription et de création de client IT.
        """
        # S'assurer que l'inscription est activée
        self._ensure_signup_allowed()
        
        # Valeur de redirection par défaut - changement vers notre page d'accueil personnalisée
        redirect = kw.get('redirect', '/client/welcome')
        
        # Limite le nombre de tentatives de récursion pour éviter RecursionError
        retry_count = kw.get('_retry_count', 0)
        if retry_count > 2:  # Limite à 3 tentatives max (0, 1, 2)
            error = "Trop de tentatives d'inscription. Veuillez contacter l'administrateur."
            return request.redirect(f'/client/auth?form=signup&error={error}&redirect={redirect}')
        
        try:
            # Activation directe du paramètre système
            request.env['ir.config_parameter'].sudo().set_param('auth_signup.allow_uninvited', 'True')

            # Vérifier que les champs obligatoires sont présents
            required_fields = ['name', 'login', 'password', 'confirm_password']
            for field in required_fields:
                if field not in kw or not kw[field].strip():
                    error = f"Le champ {field} est obligatoire."
                    return request.redirect(f'/client/auth?form=signup&error={error}&redirect={redirect}')
                    
            # Vérifier que les mots de passe correspondent
            if kw['password'] != kw['confirm_password']:
                error = "Les mots de passe ne correspondent pas."
                return request.redirect(f'/client/auth?form=signup&error={error}&redirect={redirect}')
                
            # Vérifier si l'email existe déjà dans le système
            email = kw.get('login')
            existing_user = request.env['res.users'].sudo().search([('login', '=', email)], limit=1)
            if existing_user:
                error = f"Un compte existe déjà avec cet email ({email})."
                return request.redirect(f'/client/auth?form=signup&error={error}&redirect={redirect}')
                
            # Stocker le type de client pour l'utiliser après création de l'utilisateur
            client_type = kw.get('client_type', 'enterprise')
            client_phone = kw.get('phone', '')
            company_name = kw.get('company_name', '')
            
            # Préparation des valeurs pour l'inscription (uniquement les champs valides pour res.users)
            values = {
                'login': kw.get('login'),
                'name': kw.get('name'),
                'password': kw.get('password'),
            }
            
            # Créer l'utilisateur avec le contexte it_asset_portal=True
            # La méthode signup() retourne seulement (login, password) et non (db, login, password)
            login, password = request.env['res.users'].sudo().with_context(it_asset_portal=True).signup(values)
            
            # Authentifier l'utilisateur
            request.env.cr.commit()  # Commit pour s'assurer que l'utilisateur est créé
            db = request.db
            # La méthode authenticate n'accepte que 2 paramètres: dbname et credential (un dict)
            credential = {'login': login, 'password': password}
            uid = request.session.authenticate(db, credential)
            
            if not uid:
                error = "Échec de l'authentification après inscription."
                return request.redirect(f'/client/auth?form=signup&error={error}&redirect={redirect}')
            
            # Récupérer l'utilisateur créé
            user = request.env['res.users'].sudo().browse(uid)
            
            # Créer un client IT associé
            client_vals = {
                'name': company_name or kw.get('name'),
                'partner_id': user.partner_id.id,
                'email': user.login,
                'phone': client_phone,
                'client_type': client_type,
                'status': 'active',
                'onboarding_date': fields.Date.today(),
            }
            
            # Vérifier si un client IT existe déjà pour ce partenaire
            existing_client = request.env['it.client'].sudo().search([('partner_id', '=', user.partner_id.id)], limit=1)
                
            if not existing_client:
                # Création du client IT
                client = request.env['it.client'].sudo().create(client_vals)
                _logger.info(f"Client IT créé: {client.id} pour le partenaire {user.partner_id.id}")
            else:
                # Mise à jour du client existant
                existing_client.sudo().write(client_vals)
                _logger.info(f"Client IT mis à jour: {existing_client.id} pour le partenaire {user.partner_id.id}")
            
            # Redirection vers la page d'accueil du client
            return werkzeug.utils.redirect(redirect)
            
        except Exception as e:
            # Utiliser un logger standard sans interpolation de chaîne pour éviter les récursions
            _logger.error("Exception lors de l'inscription client: %s", str(e))
            
            # Si c'est une erreur d'inscription non autorisée, forcer l'activation
            if "utilisateurs non invités" in str(e) or "uninvited" in str(e):
                try:
                    # Utiliser une méthode directe avec SQL pour éviter les problèmes de transaction
                    request.env.cr.execute("""
                        UPDATE ir_config_parameter 
                        SET value = 'True' 
                        WHERE key = 'auth_signup.allow_uninvited'
                    """)
                    request.env.cr.commit()
                    _logger.info("Activation forcée de l'inscription libre après erreur")
                    
                    # Réessayer l'inscription avec compteur incrémenté
                    new_kw = dict(kw)
                    new_kw['_retry_count'] = retry_count + 1
                    return self.client_register(**new_kw)
                except Exception as sql_err:
                    _logger.error("Erreur lors de la modification du paramètre: %s", str(sql_err))
            
            # Pour les autres erreurs, rediriger vers le formulaire avec l'erreur
            error_msg = werkzeug.urls.url_quote(str(e))
            return request.redirect(f'/client/auth?form=signup&error={error_msg}&redirect={redirect}')
            
    # Route personnalisée pour afficher notre formulaire de connexion/inscription
    @http.route('/client/auth', type='http', auth="public", website=True)
    def client_auth(self, **kw):
        # S'assurer que l'inscription est activée
        self._ensure_signup_allowed()
        
        # Détermine si on affiche le formulaire de connexion ou d'inscription
        form_view = kw.get('form', 'login')
        if form_view not in ['login', 'signup']:
            form_view = 'login'
            
        # Redirection par défaut vers le tableau de bord client
        redirect_url = '/my'
        if kw.get('redirect'):
            redirect_url = kw.get('redirect')
            
        qcontext = self.get_auth_signup_qcontext()
        qcontext.update({
            'form_view': form_view,
            'redirect': redirect_url
        })
        
        # Ajout des types de client pour le formulaire d'inscription
        if form_view == 'signup':
            qcontext['client_types'] = [
                ('enterprise', 'Entreprise'),
                ('government', 'Gouvernement'),
                ('education', 'Éducation'),
                ('nonprofit', 'Association'),
                ('individual', 'Particulier')
            ]
        
        # Si une erreur est spécifiée dans l'URL, l'ajouter au contexte
        if kw.get('error'):
            qcontext['error'] = kw.get('error')
            
        # Rendu du template avec les valeurs de contexte
        response = request.render('it_asset_management.client_auth_form', qcontext)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
        return response
    
    def _prepare_signup_values(self, qcontext):
        values = dict(qcontext or {}, is_website_user=True)
        if not values.get('name') and qcontext.get('name') and qcontext.get('lastname'):
            values['name'] = '%s %s' % (qcontext.get('name'), qcontext.get('lastname'))
        # Ajouter des champs personnalisés pour la création du client
        values.update({
            'phone': qcontext.get('phone'),
            'company_name': qcontext.get('company_name'),
            'client_type': qcontext.get('client_type', 'enterprise'),
        })
        return values
        
    @http.route('/web/login', type='http', auth='none', sitemap=False)
    def web_login(self, redirect=None, *args, **kw):
        # Assurer que l'URL de redirection est valide et toujours définie
        if not redirect:
            redirect = '/my'
        
        # Appel de la méthode parente (sans ajouter redirect aux kw)
        response = super(ITAssetAuthSignup, self).web_login(redirect=redirect, *args, **kw)
        
        # Si l'utilisateur est connecté, ajouter un bouton vers le portail client
        if request.session.uid:
            # Vérifier si l'utilisateur a un client IT associé
            user = request.env['res.users'].sudo().browse(request.session.uid)
            existing_client = request.env['it.client'].sudo().search([('partner_id', '=', user.partner_id.id)], limit=1)
                
            # Si pas de client IT, en créer un automatiquement
            if not existing_client and user.partner_id:
                try:
                    client_vals = {
                        'name': user.partner_id.name,
                        'partner_id': user.partner_id.id,
                        'email': user.partner_id.email or user.login,
                        'phone': user.partner_id.phone or '',
                        'client_type': 'enterprise',  # Type par défaut
                        'status': 'active',
                        'onboarding_date': fields.Date.today(),
                    }
                    new_client = request.env['it.client'].sudo().create(client_vals)
                    _logger.info(f"Création automatique d'un client IT (ID: {new_client.id}) pour l'utilisateur {user.login} après connexion")
                except Exception as e:
                    _logger.error(f"Erreur lors de la création du client IT après connexion: {str(e)}")
        
        return response
