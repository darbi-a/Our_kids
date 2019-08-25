# -*- coding: utf-8 -*-
""" init object """
from odoo import fields, models, api, _ ,tools, SUPERUSER_ID
from odoo.exceptions import ValidationError,UserError
from datetime import datetime , date ,timedelta
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


class PosSession(models.Model):
    _inherit = 'pos.session'

    @api.multi
    def get_returned_amount(self):
        for rec in self:
            order_id = self.env['pos.order'].search([('session_id', '=', rec.id)])
            if order_id:
                returned_amount = 0
                for order in order_id:

                    if order.amount_total < 0:
                        returned_amount += order.amount_total

                return abs(returned_amount)

    @api.multi
    def get_total_discount(self):
        for rec in self:
            total_discount = 0
            order_id = self.env['pos.order'].search([('session_id', '=', rec.id)])
            if order_id:
                for order in order_id:
                    for each in order.lines:

                        if each.product_id.is_discount or each.product_id.is_coupon:
                            total_discount += abs(each.price_unit * each.qty)

                        if each.discount:
                            total_discount += (each.price_unit * each.qty) - each.price_subtotal

            return total_discount
