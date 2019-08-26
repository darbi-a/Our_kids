# -*- coding: utf-8 -*-
"""Purchase Order Discount"""

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PORule(models.Model):
    """Purchase Order Rule Model

    Create discount rules to apply on vendor's purchase orders within specific period.
    """
    _name = 'purchase.discount.rule'

    name = fields.Char(required=True)

    vendor_id = fields.Many2one(
        comodel_name="res.partner",
        required="True",
        string='vendor'
    )
    category_ids =fields.Many2many(
        comodel_name="product.category",
        string="Products Categories",
        copy=True
    )
    date_from = fields.Date(
        default=lambda self: fields.Date.today(),
        required=True,
    )
    date_to = fields.Date(
        default=lambda self: fields.Date.today(),
        required=True,
    )
    state = fields.Selection(
        default="draft",
        selection=[('draft', 'Draft'), ('confirmed', 'Confirmed'), ],
        required=True,
    )
    rule_line_ids = fields.One2many(
        comodel_name="purchase.discount.rule.line",
        inverse_name="rule_id",
        string="Discount Rules",
        copy=True
    )
    description = fields.Text()

    @api.constrains('date_from', 'date_to')
    def _check_rule_dates(self):
        if any(self.filtered(lambda record: record.date_from > record.date_to)):
            raise ValidationError(_("Error! 'Date From' must be before 'Date To'."))

    @api.onchange('category_ids')
    def _onchange_category_ids(self):
        """ Reassign the rule lines."""
        self.rule_line_ids = False

    @api.multi
    def action_confirm_discount_rule(self):
        for record in self:
            record.state = 'confirmed'

    @api.multi
    def unlink(self):
        for rule in self:
            if rule.state == 'confirmed':
               raise ValidationError(_("Can't delete confirmed discount rules."))
        return super(PORule, self).unlink()


class PORuleLine(models.Model):
    """Purchase Order Rule Line Model

    Create discount rule lines to specify the discounts' types with its values.
    """

    _name = 'purchase.discount.rule.line'

    product_id = fields.Many2one(
        comodel_name="product.product",
        required=True,
    )
    min_value = fields.Float(required=True, )
    discount_type = fields.Selection(
        default="percentage",
        selection=[('percentage', 'Percentage'),
                   ('fixed', 'Fixed'),
                   ('quantity', 'Quantity'), ],
        required=True,
        ondelete='cascade',
    )
    discount_value = fields.Float(required=True, )
    rule_id = fields.Many2one(
        comodel_name="purchase.discount.rule",
        ondelete='cascade',
    )
    expired = fields.Boolean()

    @api.constrains('discount_value', 'min_value')
    def _check_discount_values(self):
        if not self.discount_value or not self.min_value:
            raise ValidationError(_("Discount rule values must be greater than 0.0"))

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Change product domain with changing the products' categories """
        domain = []
        if self.rule_id.category_ids:
            domain.append(('categ_id', 'in', self.rule_id.category_ids.ids))
        return {'domain': {'product_id': domain}}
