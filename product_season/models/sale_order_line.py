# -*- coding: utf-8 -*-
""" Sale Order Line Season And Barcode """
from odoo import fields, models

import logging
LOGGER = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    season_id = fields.Many2one(related='product_id.season_id')
    barcode = fields.Char(related='product_id.barcode')
