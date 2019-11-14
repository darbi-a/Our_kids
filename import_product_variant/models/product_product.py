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
    # vendor_id = fields.Many2one(comodel_name="res.partner", string="Vendor",compute = '_compute_get_seller', required=False, )
    # compute = '_compute_get_seller',
    seller_ids = fields.One2many('product.supplierinfo', 'product_tmpl_id', string='Vendors',compute = '_compute_get_seller', help="Define vendor pricelists.")
    @api.one
    @api.depends('vendor_num')
    def _compute_get_seller(self):
        for rec in self:
            if rec.vendor_num:
                vendor = self.env['res.partner'].search([('ref','=',rec.vendor_num)],limit=1)
                print("** vendor= ", vendor)
                if vendor:
                    seller_obj = self.env['product.supplierinfo']
                    seller = seller_obj.search([('product_id','=',rec.id),('name','=',vendor.id)],limit=1)
                    if not seller:
                        print("not seller ")
                        seller = self.env['product.supplierinfo'].create({
                                                        'product_id':rec.id,
                                                        'product_tmpl_id':rec.product_tmpl_id.id,
                                                        'name':vendor.id,
                    })
                    print("seler = ",seller)
                    print("vendor 2= ",vendor)
                    rec.seller_ids = [(6,0,seller.ids)]
                    print("## rec.seller_ids  1= ",  rec.seller_ids )

                    if not rec.seller_ids:
                        print("** rec.seller_ids  2= ", rec.seller_ids)

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