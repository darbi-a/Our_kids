# -*- coding: utf-8 -*-
""" init object """
from odoo import fields, models, api, _
from odoo.addons import decimal_precision as dp


class InventoryLine(models.Model):
    _inherit = "stock.inventory.line"

    theoretical_qty = fields.Float(
        'Theoretical Quantity', compute='_compute_theoretical_qty',
        digits=dp.get_precision('Product Unit of Measure'), readonly=True, store=True,groups="stock.group_stock_manager")