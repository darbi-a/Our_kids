# -*- coding: utf-8 -*-
""" init object """
from odoo import fields, models, api, _

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    vendor_account_id = fields.Many2one(comodel_name="account.account", related='partner_id.property_account_payable_id',string='Vendor Account' )
    sale_price = fields.Float(related='product_id.lst_price' )
    percentage = fields.Float(string="Column 1",compute='compute_percentage')

    @api.depends('sale_price','price_unit','product_id','product_id.standard_price')
    def compute_percentage(self):
        for rec in self:
            if rec.price_unit:
                rec.percentage = 100.0 * ( rec.sale_price / rec.price_unit)

            # elif rec.product_id.standard_price:
            #     rec.percentage = 100.0 * (rec.sale_price / rec.product_id.standard_price)






