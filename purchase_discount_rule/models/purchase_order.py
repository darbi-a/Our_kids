# -*- coding: utf-8 -*-
"""Purchase Order Discount"""

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import odoo.addons.decimal_precision as dp


class PurchaseOrder(models.Model):
    """Purchase Order Model

    Apply discount rules on PO Lines.
    """
    _inherit = 'purchase.order'

    rule_ids = new_field_ids = fields.Many2many(
        comodel_name="purchase.discount.rule.line",
        string="Applied Rules",
    )

    @api.multi
    def _unlink_applied_rules(self):
        """ """
        self.ensure_one()
        for rule in self.rule_ids:
            rule.expired = False
        self.write({'rule_ids': [(5,)]})

    @api.multi
    def _apply_discount_rules(self):
        """Apply discount rules configured previously to match the nearest target."""
        self.ensure_one()
        self._unlink_applied_rules()
        partner_id = self.partner_id
        date_order = self.date_order
        applied_rules = []
        if partner_id and date_order:
            for product_id in self.order_line.mapped('product_id'):
                rule_lines = self.env['purchase.discount.rule.line'].search(
                    [('rule_id.vendor_id', '=', partner_id.id), ('rule_id.date_from', '<=', date_order),
                     ('rule_id.date_to', '>=', date_order),
                     ('rule_id.state', '=', 'confirmed'), ('product_id', '=', product_id.id)],
                    order='min_value desc')
                valid_rule_lines = rule_lines.filtered(lambda line: not line.expired)
                for rule_line in valid_rule_lines:
                    min_value = rule_line.min_value
                    order_lines = self.env['purchase.order.line'].search([
                        ('order_id.partner_id', '=', partner_id.id),
                        ('order_id.date_order', '>=', rule_line.rule_id.date_from),
                        ('order_id.date_order', '<=', rule_line.rule_id.date_to),
                        ('order_id.state', '=', 'purchase'),
                        ('product_id', '=', product_id.id)])

                    purchased_quantity = sum(line.product_qty for line in order_lines)
                    if purchased_quantity >= min_value:
                        order_line = self.order_line.filtered(lambda line: line.product_id == product_id)[-1]
                        if rule_line.discount_type == 'quantity':
                            discounted_value = 0
                            rules_expired = rule_lines.filtered(
                                lambda line: line.expired and line.discount_type == 'quantity')
                            if rules_expired:
                                discounted_value = max(min for min in rules_expired.mapped('discount_value'))
                            order_line.discount_qty = discounted_value < rule_line.discount_value and \
                                rule_line.discount_value - discounted_value
                        elif rule_line.discount_type == 'fixed':
                            order_line.fixed_discount = rule_line.discount_value
                        else:
                            order_line.discount = rule_line.discount_value

                        ex_rules = valid_rule_lines.filtered(
                            lambda rule: rule.min_value <= min_value and not rule.expired
                        )
                        applied_rules += ex_rules
                        break
        return applied_rules

    @api.multi
    def button_cancel(self):
        result = super(PurchaseOrder, self).button_cancel()
        self._unlink_applied_rules()
        return result

    @api.multi
    def action_apply_discount_rules(self):
        applied_rules = self._apply_discount_rules()
        for rule in applied_rules:
            rule.expired = True
            self.write({'rule_ids': [(4, rule.id)]})
        return True


class PurchaseOrderLine(models.Model):
    """ Purchase Order Line Model

    Apply fixed and percentage subtotal discount and quantity discount on PO lines.
    """
    _inherit = "purchase.order.line"

    discount = fields.Float(
        string='Discount (%)',
        digits=dp.get_precision('Discount'),
    )
    discount_qty = fields.Float(
        digits=dp.get_precision('Product Unit of Measure'),
    )
    fixed_discount = fields.Float(
        digits=dp.get_precision('Discount'),
    )
    discounted_unit_price = fields.Monetary(
        compute='_compute_discounted_unit_price',
        store=True,
    )

    @api.constrains('discount')
    def _check_discount_percentage(self):
        if self.discount and self.discount >= 100.0:
            raise ValidationError(_("Discount percentage must be lower than or equal 100%."))

    @api.depends('fixed_discount', 'price_unit', 'discount_qty', 'discount')
    def _compute_discounted_unit_price(self):
        """Get discounted unit price after applying one or more discount.

        :rtype: float
        :return: Unit price after discount(s).
        """
        for line in self:
            discounted_unit_price = line.discounted_unit_price if line.discounted_unit_price \
                else line.price_unit
            if line.product_qty and line.price_unit:
                if line.discount_qty:
                    percent = 100 * line.discount_qty / line.product_qty
                    discounted_unit_price = discounted_unit_price * (1 - percent / 100)
                if line.discount:
                    percent = line.discount
                    discounted_unit_price = discounted_unit_price * (1 - percent / 100)
                if line.fixed_discount:
                    subtotal = discounted_unit_price * line.product_qty
                    if subtotal:
                        percent = line.fixed_discount * 100 / subtotal
                    discounted_unit_price = discounted_unit_price * (1 - percent / 100)
            line.discounted_unit_price = discounted_unit_price

    @api.depends('discounted_unit_price')
    def _compute_amount(self):
        """Compute price unit after applying discount."""
        for line in self:
            taxes = line.taxes_id.compute_all(line.discounted_unit_price, line.order_id.currency_id,
                                              line.product_qty, product=line.product_id,
                                              partner=line.order_id.partner_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal':taxes['total_excluded']
            })

    @api.multi
    def _get_stock_move_price_unit(self):
        """override to get price unit after discount."""
        line = self[0]
        order = line.order_id
        price_unit = line.discounted_unit_price
        if line.taxes_id:
            price_unit = line.taxes_id.with_context(round=False).compute_all(
                price_unit, currency=line.order_id.currency_id, quantity=1.0, product=line.product_id,
                partner=line.order_id.partner_id)['total_excluded']
        if line.product_uom.id != line.product_id.uom_id.id:
            price_unit *= line.product_uom.factor / line.product_id.uom_id.factor
        if order.currency_id != order.company_id.currency_id:
            price_unit = order.currency_id.compute(price_unit, order.company_id.currency_id, round=False)
        return price_unit
