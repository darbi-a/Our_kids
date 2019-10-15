# -*- coding: utf-8 -*-
""" init object """

import werkzeug

from odoo import http
from odoo.http import request
from odoo.tools.misc import file_open
from odoo.addons.web.controllers.main import Binary as BNR

class pos_offline(http.Controller):

    @http.route("/serviceworker.js")
    def get_service_worker(self, **kwargs):
        return http.Response(
            werkzeug.wsgi.wrap_file(
                request.httprequest.environ,
                file_open('offline_pos/static/src/js/serviceworker.js', 'rb')
            ),
            content_type='application/javascript; charset=utf-8',
            headers=[('Cache-Control', 'max-age=36000')],
            direct_passthrough=True,
        )

class Binary(BNR):

    @http.route([
        '/get/company_logo'
    ], type='http', auth="none", cors="*")
    def get_company_logo(self, dbname=None, **kw):
        return BNR.company_logo( dbname, **kw)
