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

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    total_discount = fields.Float(compute='compute_total_qty_discount',store=True )
    total_quantity = fields.Float(compute='compute_total_qty_discount',store=True )

    @api.multi
    @api.depends('order_line','order_line.discount','order_line.price_subtotal','order_line.product_qty')
    def compute_total_qty_discount(self):
        for rec in self:
            qty = 0.0
            discount = 0.0
            for line in rec.order_line:
                qty += line.product_qty
                discount += line.discount * line.price_subtotal / 100.0

            rec.total_discount = discount
            rec.total_quantity = qty



