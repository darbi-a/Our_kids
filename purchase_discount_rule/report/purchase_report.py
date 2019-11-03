# -*- coding: utf-8 -*-
"""Purchase Order Discount"""

from odoo import api, fields, models, tools
import odoo.addons.decimal_precision as dp


class PurchaseReport(models.Model):
    """Purchase Report Inherit

    Inherit to add discount fields.
    """
    _inherit = "purchase.report"

    discount = fields.Float(
        string='Discount (%)',
        digits=dp.get_precision('Discount'),
        group_operator="avg",
    )
    discount_qty = fields.Float(
        digits=dp.get_precision('Product Unit of Measure'),
        group_operator="sum",
    )
    fixed_discount = fields.Float(
        digits=dp.get_precision('Discount'),
        group_operator="sum",
    )
    qty_invoiced = fields.Float(
        string="Billed Qty",
        digits=dp.get_precision('Product Unit of Measure'),
        group_operator="sum",
    )
    qty_received = fields.Float(
        string="Received Qty",
        digits=dp.get_precision('Product Unit of Measure'),
        group_operator="sum",
    )

    def _select_purchase_discount(self):
        return """
            , l.discount AS discount
            , l.discount_qty AS discount_qty
            , l.fixed_discount AS fixed_discount
            , l.qty_received As qty_received
            , l.qty_invoiced As qty_invoiced
            """

    def _group_by_purchase_discount(self):
        return ", l.discount, l.discount_qty, l.fixed_discount, l.qty_received, l.qty_invoiced"

    @api.model_cr
    def init(self):
        super(PurchaseReport, self).init()
        self._cr.execute("SELECT pg_get_viewdef(%s, true)", (self._table,))
        view_def = self._cr.fetchone()[0]
        if view_def[-1] == ';':
            view_def = view_def[:-1]
        view_def = view_def.replace(
            "FROM purchase_order_line",
            "{} FROM purchase_order_line".format(
                self._select_purchase_discount()
            ),
        )
        view_def += self._group_by_purchase_discount()
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("create or replace view {} as ({})".format(
            self._table, view_def,
        ))
