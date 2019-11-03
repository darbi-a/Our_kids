# -*- coding: utf-8 -*-
""" init object """
import pytz
import xlwt
import base64
from io import BytesIO
from psycopg2.extensions import AsIs
from babel.dates import format_date, format_datetime, format_time
from odoo import fields, models, api, _ ,tools, SUPERUSER_ID
from odoo.exceptions import ValidationError,UserError
from datetime import datetime , date ,timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from dateutil.relativedelta import relativedelta
from odoo.fields import Datetime as fieldsDatetime
import calendar
from odoo import http
from odoo.http import request
from odoo import tools

import logging

LOGGER = logging.getLogger(__name__)


class VendorAgedPayableCashWizard(models.TransientModel):
    _name = 'vendor.aged.payable.cash.report.wizard'
    _description = 'vendor.aged.payable.cash.report.wizard'

    date_to = fields.Date(required=True)
    date_from = fields.Date(required=True)
    type = fields.Selection(string="Report Type",default="xls", selection=[('xls', 'XLS'), ('pdf', 'PDF'), ], required=True, )
    partner_ids = fields.Many2many(comodel_name="res.partner", string="Vendors", domain=[('supplier','=',True),('vendor_type','=','cash')] )
    tag_ids = fields.Many2many(comodel_name="res.partner.category", string="Tags", )

    @api.model
    def get_partner_balance(self,partner,end_date):
        partner_accounts = [partner.property_account_payable_id.id, partner.property_account_receivable_id.id]
        journal_items = self.env['account.move.line'].search([
            ('partner_id','=',partner.id),
            ('date','<',end_date),
            ('account_id','in',partner_accounts),
        ])
        balance = sum([(item.debit - item.credit) for item in journal_items])
        return balance,journal_items

    @api.model
    def get_partner_purchases(self,partner,inv_type):
        partner_accounts = [partner.property_account_payable_id.id, partner.property_account_receivable_id.id]
        bills = self.env['account.invoice'].search([
            ('partner_id','=',partner.id),
            ('date_invoice','>=',self.date_from),
            ('date_invoice','<=',self.date_to),
            ('state','in',['open','in_payment','paid']),
            # ('type','in',['in_invoice']),
            ('type','in',inv_type),
        ])

        bills_total = sum([b.amount_total for b in bills])
        tax_lines = bills.mapped('tax_line_ids')
        with_holding_tax = sum([l.amount_total for l in tax_lines if l.amount_total < 0])
        journal_items = bills.mapped('move_id.line_ids').filtered(lambda l:l.partner_id.id == partner.id and l.account_id.id in partner_accounts)

        return bills_total,with_holding_tax,journal_items

    @api.model
    def get_partner_total_due(self,partner):
        total_due = 0
        partner_accounts = [partner.property_account_payable_id.id, partner.property_account_receivable_id.id]
        # journal_items = self.env['account.move.line'].search([
        #     ('partner_id','=',partner.id),
        #     ('date_maturity','<=',self.date_to),
        #     ('account_id','in',partner_accounts),
        # ])
        # balance = sum([(item.debit - item.credit) for item in journal_items])
        bills = self.env['account.invoice'].search([
            ('partner_id','=',partner.id),
            # ('date_invoice','>=',self.date_from),
            # ('date_invoice','<=',self.date_to),
            ('date_due','<=',self.date_to),
            ('state','in',['open','in_payment']),
            ('type','in',['in_invoice']),
        ])
        total_due = sum([b.residual for b in bills])
        # for b in bills:
        #     bill_move = b.move_id
        #     move_lines = bill_move.line_ids.filtered(lambda l:l.account_id.id in partner_accounts and l.partner_id == partner and l.date_maturity > self.date_to)
        #     total_not_due = sum((m.debit - m.credit) for m in move_lines)
        #     # bill_due = max( b.residual - total_not_due , 0)
        #     bill_due = b.residual + total_not_due
        #     total_due += bill_due
        return -1*total_due

    @api.model
    def get_partner_payments(self,partner):
        partner_accounts = [partner.property_account_payable_id.id, partner.property_account_receivable_id.id]
        payments = self.env['account.payment'].search([
            ('partner_id', '=', partner.id),
            ('payment_date', '>=', self.date_from),
            ('payment_date', '<=', self.date_to),
            ('state', 'in', ['posted', 'reconciled']),
            ('payment_type', 'in', ['inbound', 'outbound']),
        ])

        journal_items = payments.mapped('move_line_ids').filtered(lambda l:l.partner_id.id == partner.id and l.account_id.id in partner_accounts)
        total_payments = sum([(item.debit - item.credit) for item in journal_items])
        return total_payments,journal_items

    def get_report_data(self):
        data = []
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValidationError(_('Date from must be before date to'))
        if self.partner_ids and self.tag_ids:
            raise ValidationError(_('You have to select either partners or tags!'))
        # end_time = datetime.max.time()
        # start_date = datetime.combine(start, end_time)
        partners = self.env['res.partner']
        if self.partner_ids:
            partners = self.partner_ids
        elif self.tag_ids:
            partners = partners.search([('category_id','in',self.tag_ids.ids),('vendor_type','=','cash')])
        else:
            partners = partners.search([('supplier','=',True),('vendor_type','=','cash')])

        for partner in partners:
            starting_balance,starting_items = self.get_partner_balance(partner,self.date_from) if self.date_from else 0
            payment_term = partner.property_supplier_payment_term_id.name
            purchases_total,with_holding_tax_purchase,purchase_journal_items = self.get_partner_purchases(partner,['in_invoice'])
            refund_total,with_holding_tax_refund,refund_journal_items = self.get_partner_purchases(partner,['in_refund'])
            with_holding_tax = abs(with_holding_tax_purchase) - abs(with_holding_tax_refund)
            date_to = fields.Datetime.from_string(self.date_to) + relativedelta(days=1)
            end_balance,all_items = self.get_partner_balance(partner, str(date_to)) if self.date_to else 0
            total_payments,payment_items = self.get_partner_payments(partner)

            manual_items = all_items - starting_items - refund_journal_items - purchase_journal_items - payment_items
            total_manual_amount = sum([(item.debit - item.credit) for item in manual_items])
            total_due = self.get_partner_total_due(partner)
            tags = ' - '.join(partner.mapped('category_id.name'))
            data.append({
                'name': partner.name,
                'payment_term': payment_term,
                'starting_balance': round(starting_balance,2),
                'purchases_total': round(purchases_total,2),
                'refund_total': round(refund_total,2),
                'total_manual_amount': round(total_manual_amount,2),
                'total_payments': round(total_payments,2),
                'total_due': round(total_due,2),
                'with_holding_tax': round(with_holding_tax,2),
                'tags': tags,
                'end_balance': round(end_balance,2),
            })

        return data

    @api.multi
    def action_print_excel_file(self):
        self.ensure_one()
        data = self.get_report_data()
        workbook = xlwt.Workbook()
        TABLE_HEADER = xlwt.easyxf(
            'font: bold 1, name Tahoma, color-index black,height 160;'
            'align: vertical center, horizontal center, wrap off;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_fore_colour tan, pattern_back_colour tan'
        )

        TABLE_HEADER_batch = xlwt.easyxf(
            'font: bold 1, name Tahoma, color-index black,height 160;'
            'align: vertical center, horizontal center, wrap off;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_fore_colour light_green, pattern_back_colour light_green'
        )
        header_format = xlwt.easyxf(
            'font: bold 1, name Aharoni , color-index black,height 160;'
            'align: vertical center, horizontal center, wrap off;'
            'alignment: wrap 1;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_fore_colour gray25, pattern_back_colour gray25'
        )
        TABLE_HEADER_payslib = xlwt.easyxf(
            'font: bold 1, name Tahoma, color-index black,height 160;'
            'align: vertical center, horizontal center, wrap off;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_fore_colour silver_ega, pattern_back_colour silver_ega'
        )
        TABLE_HEADER_Data = TABLE_HEADER
        TABLE_HEADER_Data.num_format_str = '#,##0.00_);(#,##0.00)'
        STYLE_LINE = xlwt.easyxf(
            'align: vertical center, horizontal center, wrap off;',
            'borders: left thin, right thin, top thin, bottom thin; '
            # 'num_format_str: General'
        )
        STYLE_Description_LINE = xlwt.easyxf(
            'align: vertical center, horizontal left, wrap 1;',
            'borders: left thin, right thin, top thin, bottom thin;'
        )

        TABLE_data = xlwt.easyxf(
            'font: bold 1, name Aharoni, color-index black,height 150;'
            'align: vertical center, horizontal center, wrap off;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_fore_colour white, pattern_back_colour white'
        )
        TABLE_data.num_format_str = '#,##0.00'
        xlwt.add_palette_colour("gray11", 0x11)
        workbook.set_colour_RGB(0x11, 222, 222, 222)
        TABLE_data_tolal_line = xlwt.easyxf(
            'font: bold 1, name Aharoni, color-index white,height 200;'
            'align: vertical center, horizontal center, wrap off;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_fore_colour blue_gray, pattern_back_colour blue_gray'
        )

        TABLE_data_tolal_line.num_format_str = '#,##0.00'
        TABLE_data_o = xlwt.easyxf(
            'font: bold 1, name Aharoni, color-index black,height 150;'
            'align: vertical center, horizontal center, wrap off;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_fore_colour gray11, pattern_back_colour gray11'
        )
        STYLE_LINE_Data = STYLE_LINE
        STYLE_LINE_Data.num_format_str = '#,##0.00_);(#,##0.00)'

        worksheet = workbook.add_sheet(_('تقرير مديونية موردي النقددي'))
        lang = self.env.user.lang
        worksheet.cols_right_to_left = 1

        row = 0
        col = 0
        worksheet.write_merge(row, row, col, col + 3, _('تقرير مديونية موردي النقدي'), STYLE_LINE_Data)
        row += 1
        worksheet.write(row, col, _('التاريخ من'), STYLE_LINE_Data)
        col += 1
        worksheet.write(row, col,datetime.strftime(self.date_from, '%d/%m/%Y') , STYLE_LINE_Data)
        col += 1
        worksheet.write(row, col, _('التاريخ الى'), STYLE_LINE_Data)
        col += 1
        worksheet.write(row, col,datetime.strftime(self.date_to, '%d/%m/%Y') , STYLE_LINE_Data)
        col += 1
        if self.tag_ids:
            worksheet.write(row, col, _('نوع الموردين'), STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, ' - '.join(self.tag_ids.mapped('name')), STYLE_LINE_Data)

        row += 2
        col = 0
        worksheet.write(row,col,_('تسلسل'),header_format)
        col += 1
        worksheet.write(row,col,_('اسم المورد'),header_format)
        col += 1
        worksheet.write(row,col,_('فترة الائتمان'),header_format)
        col += 1
        worksheet.write(row,col,_('رصيد اول المدة'),header_format)
        col += 1
        worksheet.write(row,col,_('المشتريات'),header_format)
        col += 1
        worksheet.write(row,col,_('المرتجعات'),header_format)
        col += 1
        worksheet.write(row,col,_('خصومات او تسويات'),header_format)
        col += 1
        worksheet.write(row,col,_('اشعارات خصم وضريبة'),header_format)
        col += 1
        worksheet.write(row,col,_('دفعات'),header_format)
        col += 1
        worksheet.write(row,col,_('رصيد اخر المدة'),header_format)
        col += 1
        worksheet.write(row,col,_('يستحق'),header_format)
        col += 1
        worksheet.write(row,col,_('نوع المورد'),header_format)
        col += 1


        for i,record in enumerate(data):
            row += 1
            col = 0
            worksheet.write(row, col, str(i+1), STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, record['name'], STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, record['payment_term'], STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, record['starting_balance'], STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, record['purchases_total'], STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, record['refund_total'], STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, record['total_manual_amount'], STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, record['with_holding_tax'], STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, record['total_payments'], STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, record['end_balance'], STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, record['total_due'], STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, record['tags'], STYLE_LINE_Data)

        # row += 1
        # col = 0
        # worksheet.write_merge(row, row, col, col + 4, _('الاجمالي'), header_format)
        # col += 5
        # worksheet.write(row,col,total_deserved,header_format)
        # col += 1
        # worksheet.write_merge(row,row,col,col,'',header_format)


        output = BytesIO()
        if data:
            workbook.save(output)
            xls_file_path = (_('تقرير مديونية موردي النقدي.xls'))
            attachment_model = self.env['ir.attachment']
            attachment_model.search([('res_model', '=', 'vendor.aged.payable.cash.report.wizard'), ('res_id', '=', self.id)]).unlink()
            attachment_obj = attachment_model.create({
                'name': xls_file_path,
                'res_model': 'vendor.aged.payable.cash.report.wizard',
                'res_id': self.id,
                'type': 'binary',
                'db_datas': base64.b64encode(output.getvalue()),
            })

            # Close the String Stream after saving it in the attachments
            output.close()
            url = '/web/content/%s/%s' % (attachment_obj.id, xls_file_path)
            return {'type': 'ir.actions.act_url', 'url': url, 'target': 'new'}

        else:

            view_action = {
                'name': _(' Vendor Balance Report'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'vendor.aged.payable.cash.report.wizard',
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'target': 'new',
                'context': self.env.context,
            }

            return view_action


    @api.multi
    def action_print_pdf(self):
        data = self.get_report_data()
        result={
            'data':data,
            'date_from':datetime.strftime(self.date_from, '%d/%m/%Y'),
            'date_to':datetime.strftime(self.date_to, '%d/%m/%Y'),
            'tags': ' - '.join(self.tag_ids.mapped('name')),
        }
        return self.env.ref('vendor_aged_payable_cash_report.vendor_aged_payable_cash_report').report_action(self, data=result)



    def action_print(self):
        if self.type == 'xls':
            return self.action_print_excel_file()

        elif self.type == 'pdf':
            return self.action_print_pdf()

