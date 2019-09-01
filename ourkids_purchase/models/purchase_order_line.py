# -*- coding: utf-8 -*-
""" init object """
from odoo import fields, models, api, _

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    vendor_account_id = fields.Many2one(comodel_name="account.account", related='partner_id.property_account_payable_id',string='Vendor Account' )
    sale_price = fields.Float(related='product_id.lst_price' )
    percentage = fields.Float(string="Column 1",compute='compute_percentage')
    from_other_vendor = fields.Boolean(compute='compute_from_other_vendor',defualt=False)

    @api.depends('sale_price','price_unit','product_id','product_id.standard_price')
    def compute_percentage(self):
        for rec in self:
            if rec.price_unit:
<<<<<<< HEAD
                rec.percentage = 100.0 * ( rec.sale_price / rec.price_unit) - 100.0

            # elif rec.product_id.standard_price:
            #     rec.percentage = 100.0 * (rec.sale_price / rec.product_id.standard_price)

    def compute_from_other_vendor(self):
        for rec in self:
            product_id = rec.product_id.id
            other_sale_order_lines = rec.env['purchase.order.line'].search([('product_id','=',product_id)])
            partner_ids = other_sale_order_lines.mapped('order_id.partner_id')
            if len(partner_ids) > 1 or (len(partner_ids) == 1 and partner_ids[0] != rec.order_id.partner_id):
                rec.from_other_vendor = True
            else:
                rec.from_other_vendor = False
=======
                rec.percentage = 100.0 * ( rec.sale_price / rec.price_unit)
>>>>>>> 95d251579bd409fe125728e8ab0f3460ce317de7

            # elif rec.product_id.standard_price:
            #     rec.percentage = 100.0 * (rec.sale_price / rec.product_id.standard_price)






