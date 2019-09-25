# -*- coding: utf-8 -*-

from odoo import api, fields, models
from collections import deque

class account_journal(models.Model):
    _inherit = 'account.journal'


    pos_money_log = fields.Boolean(string="Use in Money Log",  )


