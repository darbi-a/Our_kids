# -*- coding: utf-8 -*-
""" init object """
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    vendor_account_id = fields.Many2one(comodel_name="account.account", related='partner_id.property_account_payable_id',string='Vendor Account' )
    sale_price = fields.Float(related='product_id.lst_price' )
    profit_percentage = fields.Float(related='product_id.profit_percentage' )
    percentage = fields.Float(string="Profit Percentage",compute='compute_percentage')
    from_other_vendor = fields.Boolean(compute='compute_from_other_vendor',defualt=False)


    @api.depends('sale_price','price_unit','product_id','product_id.standard_price')
    def compute_percentage(self):
        for rec in self:
            if rec.sale_price:
                rec.percentage = 100.0 * ( (rec.sale_price - rec.price_unit) / rec.sale_price)

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

    def action_open_other_lines(self):
        other_sale_order_lines = self.env['purchase.order.line'].search([('product_id', '=', self.product_id.id),('order_id.partner_id', '!=', self.order_id.partner_id.id)])
        return  {
            'name': _('Purchase Orders From Other Vendors'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'vendor.po.line.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context':{'other_sale_order_lines': other_sale_order_lines.ids}

        }

    @api.constrains('partner_id')
    def check_partner(self):
        if self.partner_id and self.product_id.seller_ids:
            vendors = self.product_id.seller_ids.mapped('name')
            if self.partner_id not in vendors:
                raise ValidationError(_('This vendor is not the supplier of this product %s')  %(self.product_id.name))











