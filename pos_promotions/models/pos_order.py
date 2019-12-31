# -*- coding: utf-8 -*-
""" init object """
from odoo import fields, models, api, _


class PosOrder(models.Model):
    _inherit = 'pos.order'

    pos_promotion_ids = fields.Many2many(comodel_name="pos.promotion", relation="pos_order_promotion_rel", column1="order_id", column2="promo_id")

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(PosOrder, self)._order_fields(ui_order)

        if ui_order.get('pos_promotion_ids', False):
            order_fields.update({
                'pos_promotion_ids': ui_order['pos_promotion_ids']
            })

        return order_fields


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    is_promotion = fields.Boolean(string="Is Promotion ?", default=False,readonly=True )
    applied_promotion_id = fields.Many2one(comodel_name="pos.promotion", string="", required=False, )
    promotion_id = fields.Many2one(comodel_name="pos.promotion", string="", required=False, )
