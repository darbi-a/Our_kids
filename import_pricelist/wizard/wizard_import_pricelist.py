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

class ImportPriceList(models.TransientModel):
    _name = "wizard.import.price.list"

    file_data = fields.Binary('Archive', required=True, )
    file_name = fields.Char('File Name')

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
            first_row.append(worksheet.cell_value(0, col))
        # transform the workbook to a list of dictionaries
        archive_lines = []
        for row in range(1, worksheet.nrows):
            elm = {}
            for col in range(worksheet.ncols):
                elm[first_row[col]] = worksheet.cell_value(row, col)

            archive_lines.append(elm)

        pricelist_obj = self.env['product.pricelist']
        categ_obj = self.env['product.category']
        product_template_obj = self.env['product.template']
        product_obj = self.env['product.product']
        pricelist_line_obj = self.env['product.pricelist.item']

        cont = 1
        for line in archive_lines:
            cont += 1
            if archive_lines.count(line) > 1:
                raise UserError(_('The line Number %s :  Is a duplicate!.') % (str(cont)))


            name = line.get('name', "")
            if not name:
                raise UserError(_('The line Number %s : Name not Set!.') % (str(cont)))
            applied = line.get('applied_on', "")
            if applied not in ['global','product','category','variant']:
                raise UserError(_('The line Number %s : The Value of "applied_on" Must be one of this: [global,product,category,variant] !.') % (str(cont)))

            compute_price = line.get('compute_price', "")
            if compute_price not in ['fixed', 'percentage']:
                raise UserError(_(
                    'The line Number %s : The Value of "compute_price" Must be one of this: [fixed,percentage] !.') % (
                                    str(cont)))

            pricelist_id = pricelist_obj.search([('name', '=', name)])
            if not pricelist_id:
                pricelist_id = pricelist_obj.create({'name':name,'item_ids':False})
            else:
                if pricelist_obj.check_item_value(pricelist_id,line):
                    raise UserError(_('The line Number %s :  Is a duplicate!.') % (str(cont)))

            vals = {
                # 'base': 'pricelist',
                'pricelist_id': pricelist_id.id,
            }

            if applied == 'global':
                applied ='3_global'
                vals.update({'applied_on':applied})
            if applied == 'category':
                applied ='2_product_category'
                categ = line.get('categ_id', "")
                categ_id = categ_obj.search([('name','=',categ)])
                if not categ_id:
                    raise UserError(_('The Category %s in line Number %s is not in the system!.') % (categ, str(cont)))
                vals.update({'applied_on': '2_product_category','categ_id':categ_id.id})


            if applied == 'product':
                applied ='1_product'
                code =line.get('product_barcode', "")
                barcode = self.get_code(code)
                prod_code = product_template_obj.search([('barcode', '=', barcode)],limit=1)
                if not prod_code:
                    raise UserError(_('The Barcode %s in line Number %s is not in the system!.') % (barcode, str(cont)))
                vals.update({'applied_on': applied,'product_tmpl_id':prod_code.id})


            if applied == 'variant':
                applied ='0_product_variant'
                code = line.get('variant_barcode', "")
                barcode = self.get_code(code)
                var_code = product_obj.search([('barcode', '=', barcode)], limit=1)
                if not var_code:
                    raise UserError(_('The Barcode %s in line Number %s is not in the system!.') % (barcode, str(cont)))
                vals.update({'applied_on': applied, 'product_id': var_code.id,})

            if compute_price == 'fixed':
                fixed_price = line.get('fixed', "")
                vals.update({'compute_price': compute_price,'fixed_price':fixed_price,})
            if compute_price == 'percentage':
                percent_price = line.get('percentage', "")
                vals.update({'compute_price': compute_price,'percent_price':percent_price,})

            qty = line.get('qty', "")
            if qty:
                vals.update({'min_quantity': qty,})
            date_s = line.get('date_start', "")
            date_start = self.check_date(date_s,workbook)
            if date_start:
                vals.update({'date_start': date_start, })
            date_e = line.get('date_end', "")
            date_end = self.check_date(date_e,workbook)
            if date_end:
                vals.update({'date_end': date_end, })
            pricelist_line_obj.create(vals)


        return {'type': 'ir.actions.act_window_close'}



    @api.model
    def csv_validator(self, xml_name):
        name, extension = os.path.splitext(xml_name)
        return True if extension == '.xls' or extension == '.xlsx' else False

    def check_date(self,date_str_from_excel,workbook):
        if date_str_from_excel:
            str_date = datetime(*xlrd.xldate_as_tuple(date_str_from_excel, workbook.datemode))
            return str_date

    def get_code(self,barcode):
        if isinstance(barcode, float):
            code = int(barcode)
            prod_code = str(code).split()
        else:
            prod_code = str(barcode).strip()
        if isinstance(prod_code, list):
            prod_code = prod_code[0]
        return prod_code
# class pricelist(models.Model):
#     _inherit = 'product.pricelist.item'
#
#     @api.model
#     def create(self, values):
#         print("**values== ",values)
#         return super(pricelist, self).create(values)
#     @api.multi
#     def write(self, values):
#         print("**values11== ",values)
#         return super(pricelist, self).write(values)