# -*- coding: utf-8 -*-
""" init object """
from odoo import fields, models, api


import logging

LOGGER = logging.getLogger(__name__)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    vendor_num = fields.Char(string="Vendor Number", required=False, )
    categ_num = fields.Char(string="Category Number", required=False, )


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    vendor_num = fields.Char(string="Vendor Number", required=False, )
    categ_num = fields.Char(string="Category Number", required=False, )
