# -*- coding: utf-8 -*-
"""Purchase Order Global Discount Wizard"""

from odoo import api , models, fields


class POGlobalDiscountWizard(models.TransientModel):
    """PO Global Discount Wizard

    Assign discount as a fixed value or a percentage value on the total of PO.
    """
    _name = "purchase.order.global.discount.wizard"
    _description = 'Purchase Order Global Discount'

    discount_type = fields.Selection(
        [('percentage', 'Percentage'),
         ('fixed_amount', 'Fixed Amount'), ],
        required=True,
        default='percentage',
        )
    amount = fields.Float(
        'Discount',
        required=True,
    )

    def action_set_global_discount(self):
        """Assign value of discount on the active PO."""
        for record in self:
            purchase_order = self.env['purchase.order'].browse(self._context.get('active_id', False))
            if purchase_order:
                for line in purchase_order.order_line:
                    if record.discount_type == 'percentage':
                        line.write({'discount': record.amount})
                    else:
                        line.write({'fixed_discount': record.amount})
