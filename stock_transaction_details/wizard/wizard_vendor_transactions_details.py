# -*- coding: utf-8 -*-
""" Vendor Transactions Details """

import xlwt
import xlsxwriter
import base64
from io import BytesIO
from datetime import datetime
from odoo import fields, models, api, _, tools, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError

import logging

LOGGER = logging.getLogger(__name__)


class VendorTransactions(models.TransientModel):
    _name = 'wizard.vendor.transaction.details'
    _description = 'Vendor Transactions Details '

    start_date = fields.Date(
        required=True
    )
    end_date = fields.Date(
        required=True
    )
    partner_ids = fields.Many2many(
        comodel_name="res.partner",
        string="Vendors",
        domain=[('supplier', '=', True)]
    )

    season_ids = fields.Many2many(
        comodel_name="product.season",
    )

    category_ids = fields.Many2many(
        comodel_name='product.category',
    )

    warehouse_ids = fields.Many2many(comodel_name="stock.warehouse", required=True,)
    vendor_type = fields.Selection(selection=[('consignment', 'Consignment'), ('cash', 'Cash'), ])

    @api.constrains('vendor_type', 'partner_ids')
    def _check_partner_values(self):
        if not self.partner_ids and not self.vendor_type or (self.partner_ids and self.vendor_type):
            raise ValidationError(_("You should specify vendors or vendor type."))

    @api.model
    def get_warehouse_locations(self, warehouses, usage='internal'):
        location_obj = self.env['stock.location']
        domain = [('usage', '=', usage), ('location_id', 'child_of', warehouses.mapped('view_location_id').ids)]
        return location_obj.search(domain)

    def get_report_data(self):
        data = []
        stock_move = self.env['stock.move']
        partner = self.env['res.partner']

        vendors = (self.partner_ids and self.partner_ids) or \
                  (self.vendor_type and partner.search(
                      [('vendor_type', '=', self.vendor_type), ('supplier', '=', True)]))
        start_date = str(fields.Datetime.from_string(self.start_date))
        end_date = str(fields.Datetime.from_string(self.end_date))
        seasons = self.season_ids
        categories = self.category_ids and \
                     self.env['product.category'].search([('id', 'child_of', self.category_ids.ids)])
        warehouses = self.warehouse_ids or self.env['stock.warehouse'].search([])
        partners_refs = vendors and list(set(vendors.mapped('ref')))
        locations = self.get_warehouse_locations(warehouses)
        query = """
           select p.id  As product_id, m.id from 
           product_product p join product_template t on (p.product_tmpl_id=t.id)
           join stock_move m on (p.id = m.product_id)
           WHERE m.date between %s and %s and m.state = 'done'
        """
        query += seasons and " and p.season_id in %s" or ""
        query += categories and " and t.categ_id in %s" or ""
        query += partners_refs and " and p.vendor_num in %s" or ""
        query += " and (m.location_id in %s or m.location_dest_id in %s)"
        args = [start_date, end_date, ]
        args += seasons and [tuple(seasons.ids)]
        args += categories and [tuple(categories.ids)]
        args += partners_refs and [tuple(partners_refs)]
        args += [tuple(locations.ids), tuple(locations.ids)]
        self.env.cr.execute(query, args)
        product_ids = [x[0] for x in self.env.cr.fetchall()]
        product_ids = list(set(product_ids))
        products = self.env['product.product'].browse(product_ids)
        loss_locations = self.env['stock.location'].search([('usage', '=', 'inventory')])
        data = []
        for product in products:
            locations_data = {}
            for location in locations:
                if location.id not in locations_data.keys():
                    locations_data[location.id] = {
                        "total_qty": product.with_context(location=location.id, date_to=end_date).qty_available,
                        "purchase_qty": 0.0,
                        "sale_qty": 0.0,
                        "total_purchase": 0.0,
                        "total_sale": 0.0,
                        "transfer_qty": 0.0,
                    }

            query = """
                       select sum(m.product_uom_qty) As sale_qty , l.id as loc_id from
                       stock_move m join stock_location l ON m.location_id = l.id
                       join stock_location dest ON dest.id = m.location_dest_id
                       where m.product_id = %s and dest.usage = 'customer' and
                       m.date between %s and %s and m.state = 'done'
                       and l.id in %s
                       group by loc_id
                      """

            self.env.cr.execute(query, [product.id, start_date, end_date, tuple(locations.ids)])
            sales = self.env.cr.fetchall()
            if sales:
                for location in sales:
                    loc = list(location)
                    locations_data[loc[1]]["sale_qty"] = loc[0]
                    locations_data[loc[1]]["total_sale"] = loc[0] * product.sale_price
            query = """
                     select sum(m.product_uom_qty) As purchase_qty , dest.id as loc_id from
                     stock_move m join stock_location l ON m.location_id = l.id
                     join stock_location dest ON dest.id = m.location_dest_id
                     where m.product_id = %s and l.usage = 'supplier' and
                     m.date between %s and %s and m.state = 'done'
                     and dest.id in %s
                     group by loc_id
                    """

            self.env.cr.execute(query, [product.id, start_date, end_date, tuple(locations.ids)])
            purchases = self.env.cr.fetchall()
            if purchases:
                for location in purchases:
                    loc = list(location)
                    locations_data[loc[1]]['purchase_qty'] = loc[0]
                    locations_data[loc[1]]["total_purchase"] = loc[0] * product.standard_price

            query = """
                      select sum(m.product_uom_qty) As transfer_qty , dest.id as loc_id from
                      stock_move m  join stock_location l ON m.location_id = l.id
                      join stock_location dest ON dest.id = m.location_dest_id
                      where m.product_id = %s and l.usage = 'internal' and
                      m.date between %s and %s and m.state = 'done' and
                      dest.id in %s
                      group by loc_id
            """

            self.env.cr.execute(query, [product.id, start_date, end_date, tuple(locations.ids)])
            internal = self.env.cr.fetchall()
            if internal:
                for location in internal:
                    loc = list(location)
                    locations_data[loc[1]]["transfer_qty"] = loc[0]
            count_qty = 0
            mov_qty = 0

            if loss_locations:
                query = """
                          select sum(m.product_uom_qty) As count_qty  from
                          stock_move m join stock_location l ON m.location_id = l.id
                          join stock_location dest ON dest.id = m.location_dest_id
                          where m.product_id = %s and
                          m.date between %s and %s and m.state = 'done' and
                          dest.id in %s
                          and l.id in %s
                """

                self.env.cr.execute(query,
                                    [product.id, start_date, end_date, tuple(loss_locations.ids), tuple(locations.ids)])
                count_qty = list(self.env.cr.fetchone())[0]
                count_qty = count_qty and count_qty or 0.0
                query = """
                          select sum(m.product_uom_qty) As mov_qty  from
                          stock_move m join stock_location l ON m.location_id = l.id
                          join stock_location dest ON dest.id = m.location_dest_id
                          where m.product_id = %s and
                          m.date between %s and %s and m.state = 'done' and
                          dest.id in %s
                          and l.id in %s
                """

                self.env.cr.execute(query,
                                    [product.id, start_date, end_date, tuple(locations.ids),
                                     tuple(loss_locations.ids), ])
                mov_qty = list(self.env.cr.fetchone())[0]
                mov_qty = mov_qty and mov_qty or 0.0
            data.append({
                'product_barcode': product.barcode or '',
                'product_code': product.default_code or '',
                'product_name': product.name,
                'season': product.season_id and product.season_id.name or ' ',
                'cost_price': product.standard_price,
                'sale_price': product.sale_price,
                'total_qty': product.with_context(date_to=end_date).qty_available,
                'count_qty': count_qty,
                'mov_qty': mov_qty,
                'locations_data': locations_data
            })

        return data

    def action_print_report(self):
        self.ensure_one()
        data = self.get_report_data()
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)

        worksheet = workbook.add_worksheet()
        row = 0
        col = 0

        TABLE_HEADER = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 20,
            'font_name': 'Georgia',
        })
        header_format = workbook.add_format({
            'bold': 1, 'align': 'center', 'font_color': '#000000', 'font_name': 'Georgia'
        })
        location_header_format = workbook.add_format({
            'bold': 1, 'align': 'center', 'font_color': '#000000', 'font_name': 'Georgia','border':6,
        })
        content_format = workbook.add_format({
            'align': 'center', 'font_color': '#000000', 'font_name': 'Georgia'
        })
        format_right_to_left = workbook.add_format({
            'reading_order': 2,
            'align': 'center',
            'font_color': '#000000',
            'font_name': 'AlHor',
        })
        worksheet.set_column(0, 3, 30)

        worksheet.merge_range('A1:D3', _('Vendor Transactions Details'), TABLE_HEADER)
        row += 3
        worksheet.write(row, col, _('Date From'), header_format)
        col += 1
        worksheet.write(row, col, datetime.strftime(self.start_date, '%d/%m/%Y'), header_format)
        col += 1
        worksheet.write(row, col, _('To'), header_format)
        col += 1
        worksheet.write(row, col, datetime.strftime(self.end_date, '%d/%m/%Y'), header_format)
        if data:
            col = 0
            row += 2

            worksheet.write(row, col, _('Barcode'), header_format)
            col += 1
            worksheet.write(row, col, _('Product Name'), header_format)
            col += 1
            worksheet.write(row, col, _('Internal ref'), header_format)
            col += 1
            worksheet.write(row, col, _('Season name'), header_format)
            col += 1
            worksheet.write(row, col, _('رصيد آخر مده'), header_format)
            col += 1

            worksheet.write(row, col, _('Purchase Price'), header_format)
            col += 1

            worksheet.write(row, col, _('Count Qty'), header_format)
            col += 1

            worksheet.write(row, col, _('Mov Qty'), header_format)
            col += 1

            worksheet.write(row, col, _('Sales Price'), header_format)
            worksheet.set_column(4, col, 15)

            locations = self.get_warehouse_locations(self.warehouse_ids)
            locations = locations and locations.sorted('id')
            row -= 1
            col += 1
            locations_totals = {}
            for location in locations:
                worksheet.set_column(col, col + 3, 20)
                # worksheet.write(row, col + 3, location.display_name, header_format)
                worksheet.merge_range(row, col, row , col + 5, location.display_name, location_header_format)
                row += 1
                worksheet.write(row, col, _('رصيد آخر مده'), header_format)
                col += 1

                worksheet.write(row, col, _('Sales Qty'), header_format)
                col += 1

                worksheet.write(row, col, _('Total Sales Amount'), header_format)
                col += 1

                worksheet.write(row, col, _('Purchase Qty'), header_format)

                col += 1
                worksheet.set_column(col, col + 2, 25)
                worksheet.write(row, col, _('Total Purchase Amount'), header_format)
                col += 1

                worksheet.write(row, col, _('Transfer Qty'), header_format)

                col += 1
                row -= 1
                locations_totals[location.id] = {
                    "total_qty": 0.0,
                    "total_sale_qty": 0.0,
                    "total_sales_amount": 0.0,
                    "total_purchase_qty": 0.0,
                    "total_purchase_amount": 0.0,
                    "total_transfer_qty": 0.0
                }

            col = 0
            row += 2
            length = len(data)

            intial_row = row
            total_qty = 0
            count_qty = 0
            mov_qty = 0
            cost_price = 0
            sale_price = 0

            for prod in data:
                worksheet.write(row, col, prod['product_barcode'], content_format)
                col += 1
                worksheet.write_string(row, col, prod['product_name'], format_right_to_left)
                col += 1
                worksheet.write(row, col, prod['product_code'], content_format)

                col += 1
                worksheet.write(row, col, prod['season'], content_format)

                col += 1
                worksheet.write(row, col, prod['total_qty'], content_format)
                total_qty += prod['total_qty']

                col += 1
                worksheet.write(row, col, prod['cost_price'], content_format)
                cost_price += prod['cost_price']
                col += 1
                worksheet.write(row, col, prod['count_qty'], content_format)
                count_qty += prod['count_qty']
                col += 1
                worksheet.write(row, col, prod['mov_qty'], content_format)
                mov_qty += prod['mov_qty']
                col += 1
                worksheet.write(row, col, prod['sale_price'], content_format)

                sale_price += prod['sale_price']

                for loc in sorted(prod['locations_data'].keys()):
                    col += 1
                    worksheet.write(row, col, prod['locations_data'][loc]['total_qty'], content_format)
                    locations_totals[loc]['total_qty'] += prod['locations_data'][loc]['total_qty']
                    col += 1
                    worksheet.write(row, col, prod['locations_data'][loc]['sale_qty'], content_format)
                    locations_totals[loc]['total_sale_qty'] += prod['locations_data'][loc]['sale_qty']

                    col += 1
                    worksheet.write(row, col, prod['locations_data'][loc]['total_sale'], content_format)
                    locations_totals[loc]['total_sales_amount'] += prod['locations_data'][loc]['total_sale']

                    col += 1
                    worksheet.write(row, col, prod['locations_data'][loc]['purchase_qty'], content_format)
                    locations_totals[loc]['total_purchase_qty'] += prod['locations_data'][loc]['purchase_qty']

                    col += 1
                    worksheet.write(row, col, prod['locations_data'][loc]['total_purchase'], content_format)
                    locations_totals[loc]['total_purchase_amount'] += prod['locations_data'][loc]['total_purchase']

                    col += 1
                    worksheet.write(row, col, prod['locations_data'][loc]['transfer_qty'], content_format)
                    locations_totals[loc]['total_transfer_qty'] += prod['locations_data'][loc]['transfer_qty']

                row += 1
                col = 0
            col = 0
            worksheet.write(row, col, 'Total', header_format)
            col += 4
            worksheet.write(row, col, total_qty, header_format)
            col += 1
            worksheet.write(row, col, cost_price, header_format)

            col += 1
            worksheet.write(row, col, count_qty, header_format)
            col += 1
            worksheet.write(row, col, mov_qty, header_format)

            col += 1
            worksheet.write(row, col, sale_price, header_format)

            for loc in sorted(locations_totals.keys()):
                col += 1
                worksheet.write(row, col,locations_totals[loc]['total_qty'], header_format)

                col += 1
                worksheet.write(row, col, locations_totals[loc]['total_sale_qty'], header_format)

                col += 1
                worksheet.write(row, col, locations_totals[loc]['total_sales_amount'], header_format)

                col += 1

                worksheet.write(row, col, locations_totals[loc]['total_purchase_qty'], header_format)

                col += 1

                worksheet.write(row, col, locations_totals[loc]['total_purchase_amount'], header_format)
                col += 1

                worksheet.write(row, col, locations_totals[loc]['total_transfer_qty'], header_format)

            workbook.close()
            xls_file_path = (_('حركه الاصناف.xls'))
            attachment_model = self.env['ir.attachment']
            attachment_model.search(
                [('res_model', '=', 'wizard.vendor.transaction.details'), ('res_id', '=', self.id)]).unlink()
            attachment_obj = attachment_model.create({
                'name': xls_file_path,
                'res_model': 'wizard.vendor.transaction.details',
                'res_id': self.id,
                'type': 'binary',
                'db_datas': base64.b64encode(output.getvalue()),
            })
            output.close()

            url = '/web/content/%s/%s' % (attachment_obj.id, xls_file_path)
            return {'type': 'ir.actions.act_url', 'url': url, 'target': 'new'}
