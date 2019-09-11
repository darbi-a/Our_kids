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

class PoLineWizard(models.TransientModel):
    _name = 'vendor.po.line.wizard'
    _description = 'vendor.po.line.wizard'

    purchase_line_ids = fields.Many2many(comodel_name="purchase.order.line", compute='compute_purchase_order_line_ids')

    @api.model
    def default_get(self, fields):
        res = super(PoLineWizard, self).default_get(fields)
        other_sale_order_lines = self.env.context.get('other_sale_order_lines')
        res['purchase_line_ids'] = other_sale_order_lines
        return res

    def compute_purchase_order_line_ids(self):
        for rec in self:
            rec.purchase_line_ids = rec.env.context.get('other_sale_order_lines')




