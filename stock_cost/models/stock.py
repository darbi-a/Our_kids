# -*- coding: utf-8 -*-

from odoo import api, fields, models
from collections import deque

class stock_quant(models.Model):
    _inherit = 'stock.quant'


    cost = fields.Float(string="Total Cost",  required=False, compute='_compute_cost',store=True )
    unit_cost = fields.Float(string="Unit Cost",  required=False, related='product_id.standard_price',store=True )


    @api.one
    @api.depends('product_id','quantity')
    def _compute_cost(self):
        for rec in self:
            rec.cost=rec.product_id.standard_price * rec.quantity

class stock_move(models.Model):
    _inherit = 'stock.move'


    subtotal = fields.Float(string="Subtotal",  required=False, compute='_compute_suptotal' )
    unit_cost = fields.Float(string="Unit Cost",  required=False,related='product_id.standard_price' )

    @api.one
    @api.depends('product_id','quantity_done')
    def _compute_suptotal(self):
        for rec in self:
            rec.subtotal=rec.product_id.standard_price * rec.quantity_done

