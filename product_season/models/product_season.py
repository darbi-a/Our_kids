# -*- coding: utf-8 -*-
""" init object """
from odoo import fields, models, api, _


import logging

LOGGER = logging.getLogger(__name__)
class ProductSeason(models.Model):
    _name = 'product.season'
    _rec_name = 'name'
    _description = 'Product Season'

    name = fields.Char(string="Name", required=True, )
