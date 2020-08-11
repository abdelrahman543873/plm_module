# -*- coding: utf-8 -*-
# from odoo import http


# class WaleedFactory(http.Controller):
#     @http.route('/waleed_factory/waleed_factory/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/waleed_factory/waleed_factory/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('waleed_factory.listing', {
#             'root': '/waleed_factory/waleed_factory',
#             'objects': http.request.env['waleed_factory.waleed_factory'].search([]),
#         })

#     @http.route('/waleed_factory/waleed_factory/objects/<model("waleed_factory.waleed_factory"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('waleed_factory.object', {
#             'object': obj
#         })
