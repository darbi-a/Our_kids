# -*- coding: utf-8 -*-
""" init object """
from odoo import fields, models, api, _


class ProductProduct(models.Model):
    _inherit = 'product.product'

    profit_percentage = fields.Float()

