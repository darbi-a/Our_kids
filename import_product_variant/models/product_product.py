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
    seller_ids = fields.One2many('product.supplierinfo', 'product_tmpl_id', string='Vendors',compute='_onchange_vendor_num', help="Define vendor pricelists.")
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

    def _assin_seller(self):
        seller_id = []
        temp = self.product_tmpl_id
        if self.vendor_num and temp:
            vendor = self.env['res.partner'].search([('ref', '=', self.vendor_num)], limit=1)
            if vendor:
                seller_obj = self.env['product.supplierinfo']
                seller = seller_obj.search([('product_id', '=', self.id), ('name', '=', vendor.id)], limit=1)
                if not seller:
                    seller = self.env['product.supplierinfo'].create({
                        'product_tmpl_id': temp.id,
                        'product_id': self.id,
                        'name': vendor.id,
                    })
                    seller_id= [(6,0,seller.ids)]
                else:
                    seller_id = [(6, 0, seller.ids)]
        if seller_id:
            return seller_id
        else: return False

    @api.one
    @api.depends('vendor_num')
    def _onchange_vendor_num(self):
        try:
            seller = self._assin_seller()
            self.seller_ids = seller
        except:
            return True

    # @api.model
    # def create(self,vals):
    #
    #     new_record = super(ProductProduct, self).create(vals)
    #     self._onchange_vendor_num()
    #     return new_record

    # @api.one
    # @api.depends('vendor_num')
    # def _compute_get_seller(self):
    #     for rec in self:
    #         if rec.vendor_num:
    #             vendor = self.env['res.partner'].search([('ref','=',rec.vendor_num)],limit=1)
    #             if vendor:
    #                 seller_obj = self.env['product.supplierinfo']
    #                 seller = seller_obj.search([('product_id','=',rec.id),('name','=',vendor.id)],limit=1)
    #                 if not seller:
    #                     seller = self.env['product.supplierinfo'].create({
    #                                                     'product_id':rec.id,
    #                                                     'product_tmpl_id':rec.product_tmpl_id.id,
    #                                                     'name':vendor.id,
    #                 })
    #                 rec.seller_ids = [(6,0,seller.ids)]
    #
    #                 # if not rec.seller_ids:
    #                 #     rec.write({'seller_ids':[(6,0,seller.ids)]})
    #             else: rec.seller_ids = False
    #         else:
    #             rec.seller_ids = False





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