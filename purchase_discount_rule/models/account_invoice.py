# -*- coding: utf-8 -*-
"""Purchase Order Discount"""

from odoo import api, models , fields


class AccountInvoice(models.Model):
    """Account Invoice Model

    Override to get price unit after discount.
    """
    _inherit = "account.invoice"

    @api.onchange('currency_id')
    def _onchange_currency_id(self):
        if self.currency_id:
            for line in self.invoice_line_ids.filtered(lambda r: r.purchase_line_id):
                date = self.date or self.date_invoice or fields.Date.today()
                company = self.company_id
                line.price_unit = line.purchase_id.currency_id._convert(
                    line.purchase_line_id.discounted_unit_price, self.currency_id, company, date, round=False)

    def _prepare_invoice_line_from_po_line(self, line):
        price = line.discounted_unit_price
        data = super(AccountInvoice, self)._prepare_invoice_line_from_po_line(line)
        data['price_unit'] = line.order_id.currency_id.with_context(date=self.date_invoice).\
                                 compute(price, self.currency_id, round=False)
        return data
