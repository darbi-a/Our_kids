# -*- coding: utf-8 -*-


from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class LoyaltyProgram(models.Model):
    _inherit = 'loyalty.program'

    pp_payment_visa = fields.Float(string='Points per Payment Visa', help="How many loyalty points are given to the customer when pay visa")
    pp_payment_cash = fields.Float(string='Points per Payment Cash', help="How many loyalty points are given to the customer when pay cash")
    pp_payment_cash_visa = fields.Float(string='Points per Payment Cash & Visa', help="How many loyalty points are given to the customer when pay cash and visa")
