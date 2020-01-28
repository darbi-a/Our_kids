# -*- coding: utf-8 -*-
""" init object """
from odoo import fields, models, api, _
from odoo.addons import decimal_precision as dp


class InventoryLine(models.Model):
    _inherit = "stock.inventory.line"

    # theoretical_qty = fields.Float(
    #     'Theoretical Quantity', compute='_compute_theoretical_qty',
    #     digits=dp.get_precision('Product Unit of Measure'), readonly=True, store=True,groups="stock.group_stock_manager")

    @api.onchange('product_id', 'location_id', 'product_uom_id', 'prod_lot_id', 'partner_id', 'package_id')
    def _onchange_quantity_context(self):
        if self.product_id and self.location_id and self.product_id.uom_id.category_id == self.product_uom_id.category_id:
            self._compute_theoretical_qty()
            # self.product_qty = self.theoretical_qty
            self.product_qty = 0


class StockInventory(models.Model):
    _inherit = "stock.inventory"

    def get_barcode_view_state(self):
        inventories = super(StockInventory,self).get_barcode_view_state()
        for inventory in inventories:
            inventory['group_inventory_valuation'] = self.env.user.has_group('ourkids_access_rights.group_inventory_valuation')
        return inventories