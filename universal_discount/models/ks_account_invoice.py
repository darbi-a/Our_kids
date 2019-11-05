from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp


class KsGlobalDiscountInvoice(models.Model):
    _inherit = "account.invoice"

    ks_global_discount_type = fields.Selection([('percent', 'Percentage'), ('amount', 'Amount')],
                                               string='Universal Discount Type',
                                               readonly=True, states={'draft': [('readonly', False)],
                                                                      'sent': [('readonly', False)]}, default='percent')
    ks_global_discount_rate = fields.Float('Universal Discount',readonly=True,states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    line_discount = fields.Float('Line Discount',readonly=True,states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    ks_amount_discount = fields.Monetary(string='Universal Discount', readonly=True, compute='_compute_amount',store=True, track_visibility='always')
    total_line_discount = fields.Monetary(string='Total Lines Discount',
                                          readonly=True, compute='compute_amount_disc',store=True,track_visibility='always')
    amount_without_disc = fields.Monetary(string='Amount Without Disc', readonly=True, compute='compute_amount_disc',store=True, track_visibility='always')
    ks_enable_discount = fields.Boolean(compute='ks_verify_discount')
    ks_sales_discount_account = fields.Text(compute='ks_verify_discount')
    line_sales_discount_account = fields.Text(compute='ks_verify_discount')
    ks_purchase_discount_account = fields.Text(compute='ks_verify_discount')
    line_purchase_discount_account = fields.Text(compute='ks_verify_discount')

    @api.multi
    @api.depends('invoice_line_ids.price_subtotal', 'invoice_line_ids.quantity','line_discount',
                 'invoice_line_ids.discount','invoice_line_ids.price_unit')
    def compute_amount_disc(self):
        for rec in self:
            total_disc=0.0
            total_without_disc=0.0
            for line in rec.invoice_line_ids:
                total_disc += (line.quantity * line.price_unit) * (line.discount / 100)
                total_without_disc += (line.quantity * line.price_unit)
            rec.total_line_discount = total_disc
            rec.amount_without_disc = total_without_disc

        pass



    @api.onchange("line_discount")
    # @api.multi
    # @api.depends('line_discount','invoice_line_ids.product_id')
    def onchange_line_discount(self):
        for rec in self:
            if rec.line_discount < 0:
                raise ValidationError(
                    'The Discount Can not be Negative Amount !')

            for line in rec.invoice_line_ids:
                line.discount = rec.line_discount

    @api.multi
    @api.depends('name')
    def ks_verify_discount(self):
        for rec in self:
            rec.ks_enable_discount = rec.env['ir.config_parameter'].sudo().get_param('ks_enable_discount')
            rec.ks_sales_discount_account = rec.env['ir.config_parameter'].sudo().get_param('ks_sales_discount_account')
            rec.line_sales_discount_account = rec.env['ir.config_parameter'].sudo().get_param('line_sales_discount_account')
            rec.ks_purchase_discount_account = rec.env['ir.config_parameter'].sudo().get_param('ks_purchase_discount_account')
            rec.line_purchase_discount_account = rec.env['ir.config_parameter'].sudo().get_param('line_purchase_discount_account')

    @api.multi
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'tax_line_ids.amount_rounding',
                 'currency_id', 'company_id', 'date_invoice', 'type', 'ks_global_discount_type',
                 'ks_global_discount_rate')
    def _compute_amount(self):
        for rec in self:

            res = super(KsGlobalDiscountInvoice, rec)._compute_amount()
            if not ('ks_global_tax_rate' in rec):
                rec.ks_calculate_discount()
            sign = rec.type in ['in_refund', 'out_refund'] and -1 or 1
            rec.amount_total_company_signed = rec.amount_total * sign
            rec.amount_total_signed = rec.amount_total * sign
        return res

    @api.multi
    def ks_calculate_discount(self):
        for rec in self:
            if rec.ks_global_discount_type == "amount":
                rec.ks_amount_discount = rec.ks_global_discount_rate if rec.amount_untaxed > 0 else 0
            elif rec.ks_global_discount_type == "percent":
                if rec.ks_global_discount_rate != 0.0:
                    rec.ks_amount_discount = (rec.amount_untaxed + rec.amount_tax) * rec.ks_global_discount_rate / 100
                else:
                    rec.ks_amount_discount = 0
            rec.amount_total = rec.amount_tax + rec.amount_untaxed - rec.ks_amount_discount

    @api.constrains('ks_global_discount_rate')
    def ks_check_discount_value(self):
        if self.ks_global_discount_type == "percent":
            if self.ks_global_discount_rate > 100 or self.ks_global_discount_rate < 0:
                raise ValidationError('You cannot enter percentage value greater than 100.')
        else:
            if self.ks_global_discount_rate < 0 or self.amount_untaxed < 0:
                raise ValidationError(
                    'You cannot enter discount amount greater than actual cost or value lower than 0.')

    @api.onchange('purchase_id')
    def ks_get_purchase_order_discount(self):
        self.ks_global_discount_rate = self.purchase_id.ks_global_discount_rate
        self.ks_global_discount_type = self.purchase_id.ks_global_discount_type


    def _compute_line_discount(self):
        total_disc_line = 0.0
        if self.invoice_line_ids:
            for line in self.invoice_line_ids:
                if line.discount:
                    total_disc_line += (line.quantity * line.price_unit) * (line.discount / 100)

        return total_disc_line





    @api.model
    def invoice_line_move_line_get(self):
        ks_res = super(KsGlobalDiscountInvoice, self).invoice_line_move_line_get()
        disc_line = self._compute_line_discount()
        disc_line_name='Discount Line '
        if disc_line != 0.0 and ks_res:
            for i in range(0,len(ks_res)):
                ks_res[i]['price'] = ks_res[i]['quantity'] * ks_res[i]['price_unit']
            if self.line_discount:
                disc_line_name = disc_line_name + str(self.line_discount) +" %"

            if self.line_sales_discount_account and (self.type == "out_invoice" or self.type == "out_refund"):
                dict = {
                    'invl_id': self.number,
                    'type': 'src',
                    'name': disc_line_name,
                    'price_unit': disc_line,
                    'quantity': 1,
                    'price': -disc_line,
                    'account_id': int(self.line_sales_discount_account),
                    'invoice_id': self.id,
                }
                ks_res.append(dict)
            elif self.line_purchase_discount_account and (self.type == "in_invoice" or self.type == "in_refund"):

                dict = {
                    'invl_id': self.number,
                    'type': 'src',
                    'name': disc_line_name,
                    'price_unit': disc_line,
                    'quantity': 1,
                    'price': -disc_line,
                    'account_id': int(self.line_purchase_discount_account),
                    'invoice_id': self.id,
                }
                ks_res.append(dict)

        if self.ks_amount_discount > 0:
            ks_name = "Universal Discount"
            if self.ks_global_discount_type == "percent":
                ks_name = ks_name + " (" + str(self.ks_global_discount_rate) + "%)"
            ks_name = ks_name + " for " + (self.origin if self.origin else ("Invoice No " + str(self.id)))
            if self.ks_sales_discount_account and (self.type == "out_invoice" or self.type == "out_refund"):

                dict = {
                    'invl_id': self.number,
                    'type': 'src',
                    'name': ks_name,
                    'price_unit': self.ks_amount_discount,
                    'quantity': 1,
                    'price': -self.ks_amount_discount,
                    'account_id': int(self.ks_sales_discount_account),
                    'invoice_id': self.id,
                }
                ks_res.append(dict)


            elif self.ks_purchase_discount_account and (self.type == "in_invoice" or self.type == "in_refund"):
                dict = {
                    'invl_id': self.number,
                    'type': 'src',
                    'name': ks_name,
                    'price_unit': self.ks_amount_discount,
                    'quantity': 1,
                    'price': -self.ks_amount_discount,
                    'account_id': int(self.ks_purchase_discount_account),

                    'invoice_id': self.id,
                }
                ks_res.append(dict)


        return ks_res

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None, description=None, journal_id=None):
        ks_res = super(KsGlobalDiscountInvoice, self)._prepare_refund(invoice, date_invoice=None, date=None,
                                                                      description=None, journal_id=None)
        ks_res['ks_global_discount_rate'] = self.ks_global_discount_rate
        ks_res['ks_global_discount_type'] = self.ks_global_discount_type
        return ks_res



class account_invoice_line(models.Model):
    _inherit = 'account.invoice.line'
    def get_disc(self):
        parent = self._context.get('active_id', False)
        deisc = self.invoice_id.line_discount
        return deisc

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.invoice_id.line_discount:
            self.discount = self.invoice_id.line_discount

