# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp
class purchase_order(models.Model):
    _inherit = 'purchase.order'

    tax_lines = fields.Many2many(comodel_name="account.tax", string="Line Tax",domain=[('type_tax_use', '=', 'purchase')],readonly=True,states={'draft': [('readonly', False)]} )

    @api.multi
    def action_view_invoice(self):
        # Add code here
        result = super(purchase_order, self).action_view_invoice()
        result['context']['default_tax_lines'] = [(6, 0, self.tax_lines.ids)]
        print('result == ',result)
        return result



    @api.onchange("tax_lines")
    def onchange_line_tax_lines(self):
        for rec in self:
            for line in rec.order_line:
                print("line ",line)
                line.taxes_id =[(6, 0, self.tax_lines.ids)]
                # line.sudo().write({'tax_id':[(6, 0, self.tax_lines.ids)]})
                print("line tax_id ", line.taxes_id)

class purchaseorder_line(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('product_id')
    def onchange_product_id(self):
        super(purchaseorder_line, self).onchange_product_id()
        print("self.order_id",self.order_id)
        print("self.order_id bb",self.order_id.tax_lines.ids)
        if self.order_id.tax_lines:
            ids = self.order_id.tax_lines.ids
            self.taxes_id = [(6, 0, ids)]
            # self.sudo().write({'tax_id' : [(6, 0, ids)]})
            print("line tax_id ", self.taxes_id)
