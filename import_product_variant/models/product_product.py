# -*- coding: utf-8 -*-
""" init object """
from odoo import fields, models, api
from odoo.exceptions import UserError



import logging

LOGGER = logging.getLogger(__name__)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    vendor_num = fields.Char(string="Vendor Number", required=True, )
    categ_name = fields.Char(string="Category Name", required=False, )
    vendor_color = fields.Char(string="Vendor Color", required=False, )
    categ_num = fields.Char(string="Category Number", required=False, )
    sale_price =fields.Float("Sales Price2")
    # has_seller = fields.Boolean(string="has seller",compute="_get_seller"  )
    # seller_ids = fields.One2many(readonly=True)
    # variant_seller_ids = fields.One2many(readonly=True)
    un_edit = fields.Boolean(string="UN Edit",compute='_compute_un_edit' )

    def _compute_un_edit(self):
        for rec in self:
            sale = self.env['sale.order.line'].search([('product_id','=',rec.id)])
            pur = self.env['purchase.order.line'].search([('product_id','=',rec.id)])
            pos = self.env['pos.order.line'].search([('product_id','=',rec.id)])
            inv = self.env['account.invoice.line'].search([('product_id','=',rec.id)])
            if sale or pur or inv or pos:
                self.un_edit = True
            else:
                self.un_edit = False

    @api.depends('sale_price')
    def _compute_product_price_extra(self):
        for product in self:
            product.price_extra = product.sale_price

    @api.model
    def create(self, values):
        # Add code here
        rec = super(ProductProduct, self).create(values)
        if rec.vendor_num:
            vendor = self.env['res.partner'].search([('ref', '=', rec.vendor_num)], limit=1)
            seller = self.env['product.supplierinfo'].create({
                'product_tmpl_id': rec.product_tmpl_id.id,
                'name': vendor.id,
            })
            # val_seller=(0,0,{'name': vendor.id,})
            # rec.seller_ids=seller
            print('seller **', seller)
        print('rec.seller_ids ', rec.seller_ids)
        return rec


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    vendor_num = fields.Char(string="Vendor Number", required=False, )
    vendor_color = fields.Char(string="Vendor Color", required=False, )
    categ_num = fields.Char(string="Category Number", required=False, )
    sale_price =fields.Float("Sales Price2")
    # custom_attribute_lines = fields.Many2many(comodel_name='product.template.attribute.line', string='Product Attributes')
    # attribute_line_ids = fields.One2many()
    variant_price = fields.Float(string="Sale Price", compute='compute_variant_price' )
    @api.multi
    def create_variant_ids(self):

        return True

    @api.depends('product_variant_ids','product_variant_ids.sale_price')
    def compute_variant_price(self):
        for rec in self:
            if len(rec.product_variant_ids) > 1:
                rec.variant_price = 0
            elif len(rec.product_variant_ids) == 1:
                rec.variant_price = rec.product_variant_ids[0].sale_price

    @api.model
    def clear_list_price(self):
        # self._cr.execute("update product_template set list_price = 0")
        products = self.search([('list_price','!=',0)])
        for p in products:
            p.write({'list_price': 0.0})


class productAtt(models.Model):
    _inherit = 'product.template.attribute.line'

    product_tmpl_id = fields.Many2one('product.template', string='Product Template', ondelete='cascade', required=False, index=True)

class product_att_val(models.Model):
    _inherit = 'product.template.attribute.value'
    product_tmpl_id = fields.Many2one(
        'product.template', string='Product Template',
        required=False, ondelete='cascade', index=True)


