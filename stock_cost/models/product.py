# -*- coding: utf-8 -*-

from odoo import api, fields, models
from collections import deque


class product(models.Model):
    _inherit = 'product.product'


    unit_cost = fields.Float(string="Last Cost",  required=False,compute='_compute_last_cost',store=True)

    @api.one
    @api.depends('qty_available')
    def _compute_last_cost(self):
        for rec in self:
            if rec.categ_id:
                if rec.categ_id.property_cost_method != 'fifo':
                    rec.unit_cost = rec.standard_price
                else:
                    moves=self.env['stock.move'].search([('product_id','=',rec.id)],order='date desc',limit=1 )
                    cost=0.0
                    if moves:
                        cost = moves.value/moves.product_uom_qty
                    rec.unit_cost=cost

