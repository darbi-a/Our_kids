# -*- coding: utf-8 -*-
""" init object """
from odoo import fields, models, api


import logging

LOGGER = logging.getLogger(__name__)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    vendor_num = fields.Char(string="Vendor Number", required=False, )
    vendor_color = fields.Char(string="Vendor Color", required=False, )
    categ_num = fields.Char(string="Category Number", required=False, )
    sale_price =fields.Float("Sales Price2")
    seller_ids = fields.One2many('product.supplierinfo', 'product_tmpl_id', string='Vendors',compute = '_compute_get_seller', help="Define vendor pricelists.")

    @api.depends('list_price', 'price_extra', 'sale_price')
    def _compute_product_lst_price(self):
        to_uom = None
        if 'uom' in self._context:
            to_uom = self.env['uom.uom'].browse([self._context['uom']])
        for product in self:
            if product.sale_price:
                product.list_price = product.sale_price
            if to_uom:
                list_price = product.uom_id._compute_price(product.list_price, to_uom)
            else:
                list_price = product.list_price
            product.lst_price = list_price + product.price_extra

    @api.one
    @api.depends('vendor_num')
    def _compute_get_seller(self):
        for rec in self:
            if rec.vendor_num:
                vendor = self.env['res.partner'].search([('ref','=',rec.vendor_num)],limit=1)
                if vendor:
                    seller_obj = self.env['product.supplierinfo']
                    seller = seller_obj.search([('product_id','=',rec.id),('name','=',vendor.id)],limit=1)
                    if not seller:
                        seller = self.env['product.supplierinfo'].create({
                                                        'product_id':rec.id,
                                                        'product_tmpl_id':rec.product_tmpl_id.id,
                                                        'name':vendor.id,
                    })
                    rec.seller_ids = [(6,0,seller.ids)]

                    if not rec.seller_ids:
                        rec.write({'seller_ids':[(6,0,seller.ids)]})
                else: rec.seller_ids = False





class ProductTemplate(models.Model):
    _inherit = 'product.template'

    vendor_num = fields.Char(string="Vendor Number", required=False, )
    vendor_color = fields.Char(string="Vendor Color", required=False, )
    categ_num = fields.Char(string="Category Number", required=False, )


class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    product_uom = fields.Many2one(
        'uom.uom', 'Unit of Measure',
        related='product_id.uom_po_id',
        help="This comes from the product form.")