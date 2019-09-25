# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PosConfig(models.Model):
    _inherit = 'pos.config'

    lock_price = fields.Boolean(string="Lock price", default=False)
    price_password = fields.Char(string=u"Password")
    lock_discount = fields.Boolean(string="Lock discount", default=False)
    discount_password = fields.Char(string=u"Password")
    lock_delete = fields.Boolean(string="Lock delete", default=False)
    delete_password = fields.Char(string=u"Password")
    
    lock_fiscal_position = fields.Boolean(default=False)
    fiscal_position_password = fields.Char(string=u"Password")
    lock_global_discount = fields.Boolean(default=False)
    global_discount_password = fields.Char(string=u"Password")
    lock_inactive_orders = fields.Boolean(default=False)
    inactive_orders_pwd = fields.Char(string=u"Password")

    @api.constrains('price_password')
    def check_price_password(self):
        if self.lock_price is True:
            for item in str(self.price_password):
                try:
                    int(item)
                except Exception as e:
                    raise ValidationError(_("The unlock price password should be a number"))

    @api.constrains('discount_password')
    def check_discount_password(self):
        if self.lock_discount is True:
            for item in str(self.discount_password):
                try:
                    int(item)
                except Exception as e:
                    raise ValidationError(_("The unlock discount password should be a number"))

    @api.constrains('delete_password')
    def check_delete_password(self):
        if self.lock_delete is True:
            for item in str(self.delete_password):
                try:
                    int(item)
                except Exception as e:
                    raise ValidationError(_("The unlock delete password should be a number"))
    
    @api.constrains('fiscal_position_password')
    def check_delete_password(self):
        if self.lock_fiscal_position is True:
            for item in str(self.fiscal_position_password):
                try:
                    int(item)
                except Exception as e:
                    raise ValidationError(_("The unlock fiscal position password should be a number"))
    
    @api.constrains('global_discount_password')
    def check_delete_password(self):
        if self.lock_global_discount is True:
            for item in str(self.global_discount_password):
                try:
                    int(item)
                except Exception as e:
                    raise ValidationError(_("The unlock global discount password should be a number"))
