# -*- coding: utf-8 -*-
# from odoo import http


# class ItAssetManagement(http.Controller):
#     @http.route('/it_asset_management/it_asset_management', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/it_asset_management/it_asset_management/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('it_asset_management.listing', {
#             'root': '/it_asset_management/it_asset_management',
#             'objects': http.request.env['it_asset_management.it_asset_management'].search([]),
#         })

#     @http.route('/it_asset_management/it_asset_management/objects/<model("it_asset_management.it_asset_management"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('it_asset_management.object', {
#             'object': obj
#         })

