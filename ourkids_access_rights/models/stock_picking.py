# -*- coding: utf-8 -*-
""" init object """
from odoo import fields, models, api, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    location_rel_id = fields.Many2one(comodel_name="stock.location", related='location_id',readonly=True )
    location_rel_dest_id = fields.Many2one(comodel_name="stock.location", related='location_dest_id',readonly=True )

    def get_barcode_view_state(self):
        pickings = super(StockPicking,self).get_barcode_view_state()
        for picking in pickings:
            picking['group_stock_manager'] = self.env.user.has_group('stock.group_stock_manager')
            picking['group_inventory_valuation'] = self.env.user.has_group('ourkids_access_rights.group_inventory_valuation')

        return pickings


