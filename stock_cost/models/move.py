# -*- coding: utf-8 -*-

from odoo import api, fields, models
from collections import deque


class stock_move(models.Model):
    _inherit = 'stock.move'


    subtotal = fields.Float(string="Subtotal",  required=False, compute='_compute_suptotal' )
    unit_cost = fields.Float(string="Unit Cost",  required=False,related='product_id.standard_price')

    @api.one
    @api.depends('product_id','quantity_done')
    def _compute_suptotal(self):
        for rec in self:
            rec.subtotal=rec.product_id.standard_price * rec.quantity_done
        pass