# -*- coding: utf-8 -*-
""" init object """
from odoo import fields, models, api


class StockQuat(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def get_stock_quant(self,product_id):
        locations_domain = self.env['product.product']._get_domain_locations()
        domain_quant = [('product_id','=',int(product_id))]  + locations_domain[0]
        self._merge_quants()
        self._unlink_zero_quants()
        quants_groupby = self.env['stock.quant'].read_group(domain_quant, ['location_id','product_id', 'quantity'], ['product_id','location_id'], orderby='id',lazy=False)
        return quants_groupby

