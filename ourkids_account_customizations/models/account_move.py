# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_is_zero

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.constrains('amount')
    def check_amount(self):
        precision_currency = self.currency_id or self.company_id.currency_id
        if float_is_zero(self.amount, precision_rounding=precision_currency.rounding):
            raise ValidationError(_('Can not create Journal Entry with zero amount'))

