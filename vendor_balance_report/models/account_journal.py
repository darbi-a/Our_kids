# -*- coding: utf-8 -*-
""" init object """
from odoo import fields, models, api, _


class AccountJouranl(models.Model):
    _inherit = 'account.journal'

    use_in_initial_balance = fields.Boolean(default=False,index=True )
