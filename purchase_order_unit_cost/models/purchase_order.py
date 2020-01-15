# -*- coding: utf-8 -*-
"""Purchase Order Unit Cost"""

from odoo import api, fields, models, _


class PurchaseOrderLine(models.Model):
    """ Purchase Order Line Model

    Add Unit Cost In Purchase Order Lines.
    """
    _inherit = "purchase.order.line"

    unit_cost = fields.Float(
        related='product_id.unit_cost',
    )
