# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_is_zero


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.constrains('partner_id','move_ids_without_package')
    def check_picking_moves_vendor(self):
        if self.picking_type_id.code == 'incoming':
            vendor_num = self.partner_id.ref
            if vendor_num and self.partner_id.supplier:
                for move in self.move_ids_without_package:
                    product_vendor_num = move.product_id.vendor_num
                    if product_vendor_num and vendor_num != product_vendor_num:
                        raise ValidationError(_('The product %s is not belong to this partner' %self.product_id.display_name))

    @api.constrains('picking_type_id','move_ids_without_package')
    def check_internal_transfer(self):
        if self.picking_type_id.code == 'internal':
            for move in self.move_ids_without_package:
                if move.product_uom_qty < move.quantity_done :
                    raise ValidationError(_('Initial demand can not be less than quantity done'))

