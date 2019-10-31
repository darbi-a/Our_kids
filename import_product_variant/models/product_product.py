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
    vendor_id = fields.Many2one(comodel_name="res.partner", string="Vendor",compute = '_compute_get_seller', required=False, )
    # compute = '_compute_get_seller',
    seller_ids = fields.One2many('product.supplierinfo', 'product_tmpl_id',  'Vendors', help="Define vendor pricelists.")
    @api.one
    @api.depends('vendor_num')
    def _compute_get_seller(self):
        for rec in self:
            if rec.vendor_num:
                vendor = self.env['res.partner'].search([('ref','=',rec.vendor_num)],limit=1)
                print("vendor 2= ", vendor)
                if vendor:
                    seller_obj = self.env['product.supplierinfo']
                    seller = seller_obj.search([('product_id','=',rec.id),('name','=',vendor.id)],limit=1)
                    if not seller:
                        seller = self.env['product.supplierinfo'].create({
                                                        'product_id':rec.id,
                                                        'name':vendor.id,
                    })
                    print("seler = ",seller)
                    print("seler 2= ",vendor)
                    # rec.seller_ids = [(6,0,seller.ids)]
                    print(" rec.seller_ids  2= ",  rec.seller_ids )
                    rec.write({'seller_ids':[(6,0,seller.ids)]})
                    rec.vendor_id = vendor.id
                else:rec.vendor_id =False

        pass




class ProductTemplate(models.Model):
    _inherit = 'product.template'

    vendor_num = fields.Char(string="Vendor Number", required=False, )
    vendor_color = fields.Char(string="Vendor Color", required=False, )
    categ_num = fields.Char(string="Category Number", required=False, )
