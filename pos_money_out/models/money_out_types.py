# -*- coding: utf-8 -*-
""" init object """
from odoo import fields, models


class MoneyOutType(models.Model):
    _name = 'money.out.type'
    _rec_name = 'name'
    _description = 'Money Out Type'

    name = fields.Char(string="Name", required=True, )
