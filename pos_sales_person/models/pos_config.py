# -*- coding: utf-8 -*-
""" init object """
from odoo import fields, models, api, _


class PosConfig(models.Model):
    _inherit = 'pos.config'

    sale_persons_ids = fields.Many2many(comodel_name="hr.employee",string="Sale Persons")
