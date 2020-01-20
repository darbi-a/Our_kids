# -*- coding: utf-8 -*-
""" init object """
from odoo import fields, models, api, _

import logging

LOGGER = logging.getLogger(__name__)


class PosConfig(models.Model):
    _inherit = 'pos.config'

    allow_return_password = fields.Boolean()
    return_order_password = fields.Char()
