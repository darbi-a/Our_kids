# -*- coding: utf-8 -*-
""" init object """
from odoo import fields, models, api, _


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    season_id = fields.Many2one(comodel_name="product.season" )
