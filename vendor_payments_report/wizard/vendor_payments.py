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


class VendorPaymentsWizard(models.TransientModel):
    _name = 'vendor.payments.report.wizard'
    _description = 'vendor.payments.report.wizard'

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    type = fields.Selection(string="Report Type",default="xls", selection=[('xls', 'XLS'), ('pdf', 'PDF'), ], required=True, )


    def get_report_data(self):
        data = []
        totals = {
            'bank': 0,
            'cash': 0,
            'total': 0,
        }
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValidationError(_('Date from must be before date to!'))
        end_date = self.date_to
        end_time = datetime.max.time()
        end_date = datetime.combine(end_date, end_time)
        _sql_query = """
        SELECT p.partner_id , sum(CASE j.type WHEN 'cash' THEN p.amount ELSE 0 END) as cash,
         sum(CASE j.type WHEN 'bank' THEN p.amount ELSE 0 END) as bank
            FROM account_payment p
            JOIN account_journal j ON p.journal_id = j.id
            WHERE p.state in ('posted','reconciled') AND p.payment_type = 'outbound' AND p.partner_type = 'supplier' 
                AND p.partner_id IS NOT NULL AND j.downpayment_report IS TRUE AND j.type in ('bank','cash')
                AND p.payment_date >= %s AND p.payment_date <= %s
        GROUP BY p.partner_id
        ORDER BY p.partner_id
        """
        self._cr.execute(_sql_query, (self.date_from, end_date))
        for r in self._cr.fetchall():
            partner_id = r[0]
            cash = r[1]
            bank = r[2]
            partner = self.env['res.partner'].browse(partner_id)
            data.append({
                'partner': partner.name,
                'cash': cash,
                'bank': bank,
            })
            totals['cash'] += cash
            totals['bank'] += bank

        totals['total'] = totals['cash'] + totals['bank']
        return data, totals



    @api.multi
    def action_print_excel_file(self):
        self.ensure_one()
        data, totals = self.get_report_data()
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

        worksheet = workbook.add_sheet(_('تقرير دفعات الموردين'))
        lang = self.env.user.lang
        worksheet.cols_right_to_left = 1

        row = 0
        col = 0
        worksheet.write_merge(row, row, col, col + 3, _('تقرير دفعات الموردين'), STYLE_LINE_Data)
        row += 1
        worksheet.write(row, col, _('التاريخ من'), STYLE_LINE_Data)
        col += 1
        worksheet.write(row, col, str(self.date_from), STYLE_LINE_Data)
        col += 1
        worksheet.write(row, col, _('التاريخ الى'), STYLE_LINE_Data)
        col += 1
        worksheet.write(row, col, str(self.date_to), STYLE_LINE_Data)
        row += 2

        col = 0
        row += 1
        worksheet.write_merge(row, row, col, col+3,_('تقرير بدفعات الموردين سواء نقدي او امانات'),header_format)

        col = 0
        row += 1
        worksheet.write_merge(row,row+1,col,col,_('تسلسل'),header_format)
        col += 1
        worksheet.write_merge(row,row+1,col,col,_('اسم المورد'),header_format)
        col += 1
        worksheet.write_merge(row,row,col,col+1,_('الدفعة'),header_format)

        col = 2
        worksheet.write(row+1, col, _('نقدي'), header_format)
        col += 1
        worksheet.write(row+1, col, _('شيك'), header_format)
        row += 1
        for i,record in enumerate(data):
            row += 1
            col = 0
            worksheet.write(row, col, i+1, STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, record['partner'], STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, record['cash'], STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, record['bank'], STYLE_LINE_Data)

        row += 1
        col = 0
        worksheet.write_merge(row, row, col, col + 1, _('الاجمالي'), header_format)
        col += 2
        worksheet.write(row,col,totals['cash'],header_format)
        col += 1
        worksheet.write(row,col,totals['bank'],header_format)


        output = BytesIO()
        if data:
            workbook.save(output)
            xls_file_path = (_('تقرير دفعات الموردين.xls'))
            attachment_model = self.env['ir.attachment']
            attachment_model.search([('res_model', '=', 'vendor.payments.report.wizard'), ('res_id', '=', self.id)]).unlink()
            attachment_obj = attachment_model.create({
                'name': xls_file_path,
                'res_model': 'vendor.payments.report.wizard',
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
                'name': _(' Vendor Payments Report'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'vendor.payments.report.wizard',
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'target': 'new',
                'context': self.env.context,
            }

            return view_action


    @api.multi
    def action_print_pdf(self):
        data,totals = self.get_report_data()
        result={
            'data':data,
            'totals':totals,
            'date_from':self.date_from,
            'date_to':self.date_to,
        }
        return self.env.ref('vendor_payments_report.vendor_payments_report').report_action(self, data=result)



    def action_print(self):
        if self.type == 'xls':
            return self.action_print_excel_file()

        elif self.type == 'pdf':
            return self.action_print_pdf()

