# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    lock_all_disc = fields.Boolean(string="Lock All Discount", default=False)
    all_disc_password = fields.Char(string=u"Password")
