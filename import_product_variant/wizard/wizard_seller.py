#-*- coding: utf-8 -*-
import os
import base64
import tempfile
from odoo.exceptions import UserError
from odoo import api, fields, models, _, SUPERUSER_ID
import xlrd



class ImportSeller(models.TransientModel):
    _name = "wizard.seller"

    name = fields.Char(string="", required=False,default='New' )
    res_ids = fields.Integer('Number Resource IDs', compute="_compute_amount")

    @api.one
    @api.depends('name')
    def _compute_amount(self):
        temp_ids = self.env['product.product'].search(
            [('vendor_num','!=',False),('seller_ids', '=',False), ('variant_seller_ids', '=', False)], limit=20000)
        self.res_ids = len(temp_ids)
    def assin_seller(self):
        temp_ids = self.env['product.product'].search(
            [('vendor_num','!=',False),('seller_ids','=',False),('variant_seller_ids','=',False)],limit=20000)
        print("#temp_ids ==> ",len(temp_ids))
        for rec in temp_ids:
            vendor = self.env['res.partner'].search([('ref', '=', rec.vendor_num)], limit=1)
            if vendor:
                self.env['product.supplierinfo'].create({
                    'product_tmpl_id': rec.product_tmpl_id.id,
                    'name': vendor.id,
                })
    def delete_all_sellers(self):
        sellers = self.env['product.supplierinfo']
        sql = "delete from %s" % sellers._table
        self._cr.execute(sql)

