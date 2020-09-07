# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging

LOGGER = logging.getLogger(__name__)


class UpdateVendorPricelist(models.TransientModel):
    _name = 'update.vendor.pricelist'
    _description = 'Update Vendor Pricelist'

    @api.model
    def default_get(self, fields):
        res = super(UpdateVendorPricelist, self).default_get(fields)
        price_list_id = self.env.context.get('active_id')
        if price_list_id:
            pricelist = self.env['product.pricelist'].browse(price_list_id)
            vendor_pricslist_itmes = pricelist.mapped('item_ids').filtered(lambda i: i.applied_on == 'product_vendor')
            vendor_nums = list(set(pricelist.mapped('item_ids').filtered(lambda i: i.applied_on == '0_product_variant').mapped('product_id.vendor_num') ))
            partners = self.env['res.partner'].search([('ref','in',vendor_nums)]) | vendor_pricslist_itmes.mapped('partner_id')
            res['available_partner_ids'] = partners.ids
            res['pricelist_id'] = price_list_id

        return res

    pricelist_items_ids = fields.Many2many(comodel_name="product.pricelist.item",)
    available_partner_ids = fields.Many2many(comodel_name="res.partner")
    partner_id = fields.Many2one(comodel_name="res.partner", string="Vendor", required=True,domain="[('id','in',available_partner_ids)]" )
    pricelist_id = fields.Many2one(comodel_name="product.pricelist", string="", required=False, )

    @api.onchange('partner_id')
    def onchange_partner(self):
        if self.partner_id:
            pricelist_itmes = self.pricelist_id.item_ids
            vendor_pricslist_itmes = pricelist_itmes.filtered(lambda i: i.applied_on == 'product_vendor' and i.partner_id == self.partner_id)
            supplied_pricelist_items = pricelist_itmes.filtered(lambda i: i.applied_on == '0_product_variant' and i.product_id.vendor_num == self.partner_id.ref )
            items = vendor_pricslist_itmes | supplied_pricelist_items
            self.update({'pricelist_items_ids': [(6,0,items.ids)]})
        else:
            self.update({'pricelist_items_ids': [(5,)]})

    def delete_items(self):
        self.pricelist_items_ids.unlink()

    def action_confirm(self):
        return {'type': 'ir.actions.act_window_close'}
