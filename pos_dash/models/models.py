# -*- coding: utf-8 -*-

from odoo import models, fields, api




class product_product(models.Model):
    _inherit = "product.product"
    description = fields.Html(
        'Description', translate=True,
        help="A precise description of the Product, used only for internal information purposes.")

class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    price_subtotal = fields.Float(compute='_compute_amount_line_all', digits=0, string='Subtotal w/o Tax', store=True)
    price_subtotal_incl = fields.Float(compute='_compute_amount_line_all', digits=0, string='Total', store=True)
