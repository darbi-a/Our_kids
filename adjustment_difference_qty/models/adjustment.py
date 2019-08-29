# -*- coding: utf-8 -*-
# Copyright 2017 Jarvis (www.odoomod.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models, _ ,exceptions
from odoo import SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import dateutil.parser
from ast import literal_eval



class inventory(models.Model):
    _inherit = 'stock.inventory.line'


    difference_qty = fields.Float(string="Difference Quantity",  required=False,compute='_compute_difference_qty' )


    @api.one
    @api.depends('theoretical_qty','product_qty')
    def _compute_difference_qty(self):
        self.difference_qty = self.product_qty - self.theoretical_qty
        pass

