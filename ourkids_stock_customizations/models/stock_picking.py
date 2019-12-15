# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_is_zero


class StockPicking(models.Model):
    _inherit = 'stock.picking'

