# -*- coding: utf-8 -*-
""" init object """
from odoo import fields, models, api, _

import logging

LOGGER = logging.getLogger(__name__)

class PosConfig(models.Model):
    _inherit = 'pos.config'

    lock_stock_qty = fields.Boolean(string="Lock Stock Qty", default=False)
    stock_amount_password = fields.Char(string=u"Password")
