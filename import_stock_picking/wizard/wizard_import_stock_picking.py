#-*- coding: utf-8 -*-

import os
import csv
import tempfile
import base64
from odoo.exceptions import UserError
from odoo import api, fields, models, _, SUPERUSER_ID
from datetime import datetime, timedelta, date
import xlrd, mmap, xlwt



class ImportStockPicking(models.TransientModel):
    _name = "wizard.import.stock.picking"
    _description = "Import Stock Picking"


    file_data = fields.Binary('Archive', required=True,)
    file_name = fields.Char('File Name')
    result = fields.Html(sanitize_attributes=False)

    def import_button(self):
        if not self.csv_validator(self.file_name):
            raise UserError(_("The file must be an .xls/.xlsx extension"))

        file_path = tempfile.gettempdir() + '/file.xlsx'
        data = self.file_data
        f = open(file_path, 'wb')
        f.write(base64.b64decode(data))
        #f.write(data.decode('base64'))
        f.close()
        workbook = xlrd.open_workbook(file_path, on_demand=True)
        worksheet = workbook.sheet_by_index(0)
        first_row = []
        archive = csv.DictReader(open(file_path))

        # f.write(data.decode('base64'))

        for col in range(worksheet.ncols):
            first_row.append(worksheet.cell_value(0, col))
        # transform the workbook to a list of dictionaries
        archive_lines = []
        vals_list = []
        for row in range(1, worksheet.nrows):
            elm = {}
            for col in range(worksheet.ncols):
                elm[first_row[col]] = worksheet.cell_value(row, col)

            archive_lines.append(elm)

        stock_move_obj = self.env['stock.move']
        product_obj = self.env['product.product']
        stock_picking_id = self.env.context.get('active_id')
        not_exist = []
        if stock_picking_id:
            stock_picking = self.env['stock.picking'].browse(stock_picking_id)

            self.valid_columns_keys(archive_lines)
            self.valid_quantity(archive_lines)
            head_col = archive_lines[0].keys()
            cont = 0
            for line in archive_lines:
                cont += 1
                quantity = line.get('quantity',0)
                if 'barcode' in head_col:
                    barcode = line.get('barcode',0)
                    products = product_obj.search([('barcode','=',str(barcode))])

                else:
                    product_name = line.get('product',0)
                    products = product_obj.search([('display_name','ilike',product_name)])
                    products = products.filtered(lambda p: p.display_name == product_name)

                if products:
                    vals_list.append({
                        'name': products[0].display_name ,
                        'picking_id': stock_picking.id,
                        'product_id': products[0].id,
                        'product_uom_qty': float(quantity),
                        'product_uom': products[0].product_tmpl_id.uom_po_id.id,
                        'location_id': stock_picking.location_id.id,
                        'location_dest_id': stock_picking.location_dest_id.id,
                    })
                    # stock_move_obj.create(vals)

                else:
                    not_exist.append({
                        'count': cont,
                        'product': line.get('product',''),
                        'barcode': line.get('barcode',''),
                    })

        if not_exist:
            # self.env.cr.rollback()
            self.result= """
            
            <h2>Some Rows Could not be imported</h2>
            <br/>
            <table style="color:red;" class="table table-bordered">
                <tr>
                    <th>Number</th>
                    <th>Product</th>
                    <th>Barcode</th>
                </tr>
                %s
            </table>
            
            """ %(self.get_table_rows(not_exist))

            view_action = {
                'name': self._description,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': self._name,
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'target': 'new',
                'context': self.env.context,
            }

            return view_action

        else:
            # i = 0
            for vals in vals_list:
                # print(i)
                stock_move_obj.create(vals)
                # i += 1
            return {'type': 'ir.actions.act_window_close'}
        
    @api.model
    def valid_quantity(self, archive_lines):
        cont = 0
        for line in archive_lines:
            cont += 1
            quantity = line.get('quantity',"")

            try:
                quantity_float = float(quantity)
            except:
                raise UserError('The product quantity of the %s line does not have an adequate format.'%cont)
        return True


    @api.model
    def valid_columns_keys(self, archive_lines):
        columns = archive_lines[0].keys()
        text = "The csv file must contain the following columns: barcode ,product and quantity. \nThese columns are not found in the File:"; text2 = text
        found = False
        not_found_column = ''
        if 'product' in columns:
            found = True
        else:
            not_found_column = "\n[ product ]"

        if 'barcode' in columns:
            found = True
        else:
            not_found_column = "\n[ barcode ]"

        if not found:
            text += not_found_column

        if text !=text2:
            raise UserError(text)
        return True

    @api.model
    def csv_validator(self, xml_name):
        name, extension = os.path.splitext(xml_name)
        print("extension == ",extension)
        return True if extension == '.xls' or extension == '.xlsx' else False

    def get_table_rows(self,not_exist):
        res = ""
        for d in not_exist:
            res += """
            <tr>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
            </tr>
            """ %(d['count'],d['product'],d['barcode'])

        return res

        
