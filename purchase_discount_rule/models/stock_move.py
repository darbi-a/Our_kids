# -*- coding: utf-8 -*-
""" Purchase Discount Rule """

from odoo import api, models


class StockMove(models.Model):
    """Stock Move Model

    Change unit price to include discounts values.
    """
    _inherit = "stock.move"

    @api.multi
    def _get_price_unit(self):
        """Use discounted unit price instead of unit price"""
        self.ensure_one()
        if self.purchase_line_id and self.product_id.id == self.purchase_line_id.product_id.id:
            line = self.purchase_line_id
            order = line.order_id
            price_unit = line.discounted_unit_price
            if line.taxes_id:
                price_unit = \
                line.taxes_id.with_context(round=False).compute_all(
                    price_unit, currency=line.order_id.currency_id, quantity=1.0)['total_excluded']
            if line.product_uom.id != line.product_id.uom_id.id:
                price_unit *= line.product_uom.factor / line.product_id.uom_id.factor
            if order.currency_id != order.company_id.currency_id:
                price_unit = order.currency_id.compute(price_unit, order.company_id.currency_id, round=False)
            return price_unit
        return super(StockMove, self)._get_price_unit()
