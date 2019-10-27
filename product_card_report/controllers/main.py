# -*- coding: utf-8 -*-
""" init object """
from odoo import fields, models, api, _, tools, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, date, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from dateutil.relativedelta import relativedelta
from odoo.fields import Datetime as fieldsDatetime
import calendar
from odoo import http
from odoo.http import request
from odoo import tools

import logging

LOGGER = logging.getLogger(__name__)


class ProductCard(http.Controller):

    @http.route(['/custom/product_card/<int:card_report_id>'], type='http', auth="public", website=True)
    def report_card(self,card_report_id, **kw):
        report_obj = request.env['product.card.report.wizard'].browse(int(card_report_id))
        data = report_obj.get_report_data()
        return request.render('product_card_report.product_card_tmp_report', {'data': data,
                                                                              'product_name':report_obj.product_id.name,
                                                                              'date_from':report_obj.date_from,
                                                                              'date_to':report_obj.date_to,
                                                                              'location':report_obj.location_id.name,
                                                                              })
