#-*- coding: utf-8 -*-

import logging
import os
import csv
import tempfile
import base64
from odoo.exceptions import UserError
from odoo import api, fields, models, _, SUPERUSER_ID
from datetime import datetime, timedelta, date
import xlrd, mmap, xlwt

_logger = logging.getLogger(__name__)

class ImportPurchaseLines(models.TransientModel):
    _name = "wizard.import.purchase.line"

    file_data = fields.Binary('Archive', required=True,)
    file_name = fields.Char('File Name')
    order_id = fields.Many2one('purchase.order', string='Order', required=True)
    # partner_id = fields.Many2one('res.partner', string='Customer',related='order_id.partner_id', required=True)

    def import_button(self):
        if not self.csv_validator(self.file_name):
            raise UserError(_("The file must be an .xls/.xlsx extension"))

        file_path = tempfile.gettempdir() + '/file.xlsx'
        data = self.file_data
        f = open(file_path, 'wb')
        f.write(base64.b64decode(data))
        # f.write(data.decode('base64'))
        f.close()
        workbook = xlrd.open_workbook(file_path, on_demand=True)
        worksheet = workbook.sheet_by_index(0)
        first_row = []
        archive = csv.DictReader(open(file_path))

        # f.write(data.decode('base64'))

        for col in range(worksheet.ncols):
            print("",)
            first_row.append(worksheet.cell_value(0, col))
        # transform the workbook to a list of dictionaries
        archive_lines = []
        for row in range(1, worksheet.nrows):
            print("",)
            elm = {}
            for col in range(worksheet.ncols):
                print("",)
                elm[first_row[col]] = worksheet.cell_value(row, col)

            archive_lines.append(elm)

        purchase_order_obj = self.env['purchase.order']
        product_obj = self.env['product.product']
        product_template_obj = self.env['product.template']
        purchase_line_obj = self.env['purchase.order.line']

        # archive_lines = []
        # for line in archive:
        #     archive_lines.append(line)

        self.valid_columns_keys(archive_lines)
        self.valid_product_code(archive_lines, product_obj)
        self.valid_prices(archive_lines)


        purchase_order_obj = self.order_id
        cont = 0
        for line in archive_lines:
            cont += 1
            code = str(line.get('barcode', ""))
            product_id = product_obj.search([('barcode', '=', code)])
            print("line =>",line)
            quantity = line.get('quantity', 0)
            print("quantity =>", quantity)
            price_unit = self.get_valid_price(line.get('price', ""), cont)
            product_uom = product_template_obj.search([('barcode', '=', code)])
            # ids = self.order_id.tax_lines.ids
            # self.taxes_id = [(6, 0, ids)]
            if purchase_order_obj and product_id:
                vals = {
                    'order_id': purchase_order_obj.id,
                    'product_id': product_id.id,
                    'taxes_id': [(6, 0, purchase_order_obj.tax_lines.ids)],
                    'product_qty': float(quantity),
                    'price_unit': price_unit,
                    'date_planned': datetime.now(),
                    'product_uom': product_id.uom_id.id,
                    'name': product_id.name,
                }
                purchase_line_obj.create(vals)
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def valid_prices(self, archive_lines):
        cont = 0
        for line in archive_lines:
            print("Line == ", line)
            cont += 1
            price = line.get('price', "")
            print("price", price)
            # if price != "":
            #     price = price.replace("$","").replace(",",".")
            try:
                price_float = float(price)
            except:
                raise UserError(
                    'The product price of the %s line does not have an adequate format. Suitable formats, example: "$100,00"-"100,00"-"100"' % cont)
        return True

    @api.model
    def get_valid_price(self, price, cont):
        # if price != "":
        #     price = price.replace("$","").replace(",",".")
        try:
            price_float = float(price)
            return price_float
        except:
            raise UserError(
                'The product price of the %s line does not have an adequate format. Suitable formats, example: "$100,00"-"100,00"-"100"' % cont)
        return False

    @api.model
    def valid_product_code(self, archive_lines, product_obj):
        cont = 0
        for line in archive_lines:
            cont += 1
            ref = ''
            code = line.get('barcode', "")
            print("code == >> ", code)
            if isinstance(code, float):
                c = int(line.get('barcode', ""))
                ref = str(c).strip()
                print("c == >> ", c)
                print("ref == >> ", ref)
            else:
                ref = str(code).strip()
                print("ref2 == >> ", ref)
            product_id = product_obj.search([('barcode', '=', ref)])
            if len(product_id) > 1:
                raise UserError("The product barcode of line %s, is duplicated in the system." % cont)
            if not product_id:
                raise UserError("The product barcode of line %s is not found in the system" % cont)

    @api.model
    def valid_columns_keys(self, archive_lines):
        columns = archive_lines[0].keys()
        text = "El Archivo csv debe contener las siguientes columnas: barcode, quantity y price. \nNo se encuentran las siguientes columnas en el Archivo:";
        text2 = text
        if not 'barcode' in columns:
            text += "\n[ barcode ]"
        if not 'quantity' in columns:
            text += "\n[ quantity ]"
        if not 'price' in columns:
            text += "\n[ price ]"
        if text != text2:
            raise UserError(text)
        return True

    @api.model
    def csv_validator(self, xml_name):
        name, extension = os.path.splitext(xml_name)
        print("extension == ", extension)
        return True if extension == '.xls' or extension == '.xlsx' else False
