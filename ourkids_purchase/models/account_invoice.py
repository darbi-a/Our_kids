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

class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    sale_price = fields.Float(related='product_id.lst_price')
    virtual_profit_percentage = fields.Float(related='product_id.profit_percentage')
    actual_profit_percentage = fields.Float(string="Profit Percentage", compute='compute_percentage')

    @api.depends('sale_price', 'price_unit', 'product_id', 'product_id.standard_price')
    def compute_percentage(self):
        for rec in self:
            if rec.sale_price:
                rec.actual_profit_percentage = 100.0 * ((rec.sale_price - rec.price_unit) / rec.sale_price)


