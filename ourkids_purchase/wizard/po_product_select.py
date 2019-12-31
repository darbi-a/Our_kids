# -*- coding: utf-8 -*-
""" init object """
from odoo import fields, models, api, _


class PoProductSelect(models.TransientModel):
    _name = 'po.product.select'
    _description = 'po.product.select'

    product_ids = fields.Many2many(comodel_name="product.product")

    def action_confirm(self):
        order_id = self._context.get('active_id')
        order = self.env['purchase.order'].browse(order_id)
        values = []
        for product in self.product_ids:
            vals = {
                'product_id': product.id
            }
            order_line = self.env['purchase.order.line'].new(vals)
            order_line.onchange_product_id()
            order_line_vals = order_line._convert_to_write(order_line._cache)
            values.append((0,0,order_line_vals))

        order.order_line = values
