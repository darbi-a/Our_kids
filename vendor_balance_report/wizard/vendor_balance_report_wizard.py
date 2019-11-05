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


class VendorBalanceWizard(models.TransientModel):
    _name = 'vendor.balance.report.wizard'
    _description = 'vendor.balance.report.wizard'

    date = fields.Date(required=True)
    type = fields.Selection(string="Report Type",default="xls", selection=[('xls', 'XLS'), ('pdf', 'PDF'), ], required=True, )
    partner_ids = fields.Many2many(comodel_name="res.partner", string="Vendors",domian=[('vendor_type','=','consignment')] )
    tag_ids = fields.Many2many(comodel_name="res.partner.category", string="Tags", )
    season_ids = fields.Many2many(comodel_name="product.season" )

    @api.model
    def get_cost_from_entries(self,account_moves):
        total_debit = 0
        total_qty = 0
        for move in account_moves:
            for line in move.line_ids:
                total_debit += line.debit if line.debit else 0
                total_qty += line.quantity if line.debit else 0

        if total_qty:
            return (total_debit/total_qty)
        else:
            return 0.0

    @api.model
    def get_stock_valuation_partner(self,partner):
        total_eval = 0
        stock_pickings = self.env['stock.picking'].search([
            ('partner_id','=',partner.id),
            ('state','in',['done']),
            ('picking_type_id.code','in',['incoming']),
        ])
        max_date = datetime.combine(self.date , datetime.max.time())
        move_lines = stock_pickings.mapped('move_line_ids').filtered(lambda l:l.date <= max_date)
        products = move_lines.mapped('product_id')
        if self.season_ids:
            products = products.filtered(lambda p:p.season_id in self.season_ids)
        for product in products:
            # moves_other_vendors = self.env['stock.move'].search([
            #     ('picking_id.partner_id','!=',partner.id),
            #     ('picking_id.partner_id','!=',False),
            #     ('state','in',['done']),
            #     ('picking_type_id.code','in',['incoming']),
            #     ('product_id','=',product.id),
            #     ('date','<=',max_date),
            # ])
            total_eval += product.with_context(to_date=str(max_date)).stock_value
            # if moves_other_vendors:
            #     eval_product_partner = 0.0
            #     incoming_moves = []
            #     remain_from_move = {}
            #     product_move_lines = self.env['stock.move.line'].search([
            #         ('state','in',['done']),
            #         ('move_id.picking_type_id.code','in',['incoming','outgoing']),
            #         ('product_id','=',product.id),
            #         ('date','<=',max_date),
            #     ],order='date')
            #
            #     for mvl in product_move_lines:
            #         if mvl.move_id.picking_type_id.code == 'incoming':
            #             incoming_moves.append(mvl)
            #             remain_from_move[mvl] = mvl.qty_done
            #         else:
            #             self.remove_from_quantity(incoming_moves,remain_from_move,mvl.qty_done)
            #
            #     for ml in remain_from_move.keys():
            #         if ml.move_id.picking_id.partner_id == partner:
            #             qty = remain_from_move[ml]
            #             cost = self.get_cost_from_entries(ml.move_id.account_move_ids)
            #             eval_product_partner += qty * cost
            #
            #     total_eval += eval_product_partner
            # else:
            #     total_eval += product.with_context(to_date=str(max_date)).stock_value

        return total_eval

    @api.model
    def remove_from_quantity(self,incoming_moves,remain_from_move,out_qty):
        remaining = -1*out_qty
        while remaining < 0:
            if remain_from_move and incoming_moves:
                current_move = incoming_moves[0]
                remaining = remain_from_move[current_move] + remaining
                if remaining <= 0:
                    del remain_from_move[current_move]
                    del incoming_moves[0]
                elif remaining > 0:
                    remain_from_move[current_move] = remaining

    def get_report_data(self):
        data = []
        total_deserved = 0
        if self.partner_ids and self.tag_ids:
            raise ValidationError(_('You have to select either partners or tags!'))
        start = self.date
        # end_time = datetime.max.time()
        # start_date = datetime.combine(start, end_time)
        partners = self.env['res.partner']
        if self.partner_ids:
            partners = self.partner_ids
        elif self.tag_ids:
            partners = partners.search([('category_id','in',self.tag_ids.ids),('vendor_type','=','consignment')])
        else:
            partners = partners.search([('vendor_type','=','consignment')])

        flds = ['debit', 'partner_id', 'credit']
        for partner in partners:
            accounts = [partner.property_account_payable_id.id,partner.property_account_receivable_id.id]
            domain = [('partner_id', '=', partner.id),('account_id', 'in', accounts), ('date', '<=', start)]
            stock_valuation_partner = self.get_stock_valuation_partner(partner)
            if not self.season_ids:
                entries_by_partner = self.env['account.move.line'].read_group(domain, fields=flds, groupby=['partner_id'])

                balance = entries_by_partner[0]['debit'] - entries_by_partner[0]['credit'] if entries_by_partner else 0
            else:
                payments = self.env['account.payment'].search([
                    ('partner_id','=',partner.id),
                    ('season_id','in',self.season_ids.ids),
                    ('state','in',['posted','reconciled']),
                ])
                balance = 0
                for pay in payments:
                    if pay.payment_type == 'inbound':
                        balance += pay.amount
                    elif pay.payment_type == 'outbound':
                        balance -= pay.amount

            due = balance - stock_valuation_partner if balance >= 0 else (balance + stock_valuation_partner)
            tags = partner.category_id.mapped('name')
            data.append({
                'partner_name': partner.name,
                'vendor_num': partner.ref,
                'balance': balance,
                'stock_evaluation':stock_valuation_partner,
                'due': due,
                'tags': ' - '.join(tags)
            })
            total_deserved += due

        return data,total_deserved



    @api.multi
    def action_print_excel_file(self):
        self.ensure_one()
        data, total_deserved = self.get_report_data()
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

        worksheet = workbook.add_sheet(_('تقرير مديونية موردي الامانات'))
        lang = self.env.user.lang
        worksheet.cols_right_to_left = 1

        row = 0
        col = 0
        worksheet.write_merge(row, row, col, col + 3, _('تقرير مديونية موردي الامانات'), STYLE_LINE_Data)
        row += 1
        worksheet.write(row, col, _('التاريخ '), STYLE_LINE_Data)
        col += 1
        worksheet.write(row, col,datetime.strftime(self.date, '%d/%m/%Y') , STYLE_LINE_Data)
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
        worksheet.write(row,col,_('رقم المورد'),header_format)
        col += 1
        if self.season_ids:
            worksheet.write(row, col, _('مدفوعات السيزون'), header_format)
        else:
            worksheet.write(row,col,_('الرصيد'),header_format)
        col += 1
        worksheet.write(row,col,_('الجرد'),header_format)
        col += 1
        worksheet.write(row,col,_('المستحق'),header_format)
        col += 1
        worksheet.write(row,col,_('النوع'),header_format)

        for i,record in enumerate(data):
            row += 1
            col = 0
            worksheet.write(row, col, str(i+1), STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, record['partner_name'], STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, record['vendor_num'], STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, record['balance'], STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, record['stock_evaluation'], STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, record['due'], STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, record['tags'], STYLE_LINE_Data)

        row += 1
        col = 0
        worksheet.write_merge(row, row, col, col + 4, _('الاجمالي'), header_format)
        col += 5
        worksheet.write(row,col,total_deserved,header_format)
        col += 1
        worksheet.write_merge(row,row,col,col,'',header_format)


        output = BytesIO()
        if data:
            workbook.save(output)
            xls_file_path = (_('تقرير مديونية موردي الامانات.xls'))
            attachment_model = self.env['ir.attachment']
            attachment_model.search([('res_model', '=', 'vendor.balance.report.wizard'), ('res_id', '=', self.id)]).unlink()
            attachment_obj = attachment_model.create({
                'name': xls_file_path,
                'res_model': 'vendor.balance.report.wizard',
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
                'res_model': 'vendor.balance.report.wizard',
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'target': 'new',
                'context': self.env.context,
            }

            return view_action


    @api.multi
    def action_print_pdf(self):
        data,total_deserved = self.get_report_data()
        result={
            'data':data,
            'season':True if self.season_ids else False,
            'total_deserved':total_deserved,
            'date':datetime.strftime(self.date, '%d/%m/%Y'),
            'tags': ' - '.join(self.tag_ids.mapped('name')),
        }
        return self.env.ref('vendor_balance_report.report_vendor_balance').report_action(self, data=result)



    def action_print(self):
        if self.type == 'xls':
            return self.action_print_excel_file()

        elif self.type == 'pdf':
            return self.action_print_pdf()

