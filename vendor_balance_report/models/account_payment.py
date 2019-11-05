# -*- coding: utf-8 -*-
""" init object """
from odoo import fields, models, api, _


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    vendor_type = fields.Selection(related='partner_id.vendor_type')
    is_supplier = fields.Boolean(related='partner_id.supplier')

    season_id = fields.Many2one(comodel_name="product.season", string="", required=False, )

    @api.onchange('partner_id')
    def onchange_partner_season(self):
        self.update({'season_id': None})
