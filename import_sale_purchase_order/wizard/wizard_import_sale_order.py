#-*- coding: utf-8 -*-

import logging
import os
import csv
import tempfile
import base64
from odoo.exceptions import UserError
from odoo import api, fields, models, _, SUPERUSER_ID
from datetime import datetime, timedelta, date

_logger = logging.getLogger(__name__)

class ImportSaleOrder(models.TransientModel):
    _name = "wizard.import.sale.order"

    file_data = fields.Binary('Archive', required=True,)
    file_name = fields.Char('File Name')
    partner_id = fields.Many2one('res.partner', string='Cliente', required=True)


    def import_button(self):
        if not self.csv_validator(self.file_name):
            raise UserError(_("The file must be a .csv extension"))
        file_path = tempfile.gettempdir()+'/file.csv'
        data = self.file_data
        f = open(file_path,'wb')
        f.write(base64.b64decode(data))
        #f.write(data.decode('base64'))
        f.close() 
        archive = csv.DictReader(open(file_path))
        
        sale_order_obj = self.env['sale.order']
        product_obj = self.env['product.product']
        product_template_obj = self.env['product.template']
        sale_order_line_obj = self.env['sale.order.line']
        
        archive_lines = []
        for line in archive:
            archive_lines.append(line)
            
        self.valid_columns_keys(archive_lines)
        self.valid_product_code(archive_lines, product_obj)
        self.valid_prices(archive_lines)

        vals = {
            'partner_id': self.partner_id.id,
            'apply_odc': False,
        }
        sale_order_id = sale_order_obj.create(vals)
        cont = 0
        for line in archive_lines:
            cont += 1
            code = str(line.get('code',"")).strip()
            product_id = product_obj.search([('default_code','=',code)])
            
            quantity = line.get('quantity',0)
            price_unit = self.get_valid_price(line.get('price',""),cont)
            product_uom = product_template_obj.search([('default_code','=',code)])
            if sale_order_id and product_id:
                vals = {
                    'order_id': sale_order_id.id,
                    'product_id': product_id.id,
                    'product_uom_qty': float(quantity),
                    'price_unit': price_unit,
                    'product_uom': product_id.product_tmpl_id.uom_po_id.id,
                    'name': product_id.name,
                }
                sale_order_line_obj.create(vals)
        return {'type': 'ir.actions.act_window_close'}
        

    @api.model
    def valid_prices(self, archive_lines):
        cont = 0
        for line in archive_lines:
            cont += 1
            price = line.get('price',"")
            if price != "":
                price = price.replace("$","").replace(",",".")
            try:
                price_float = float(price)
            except:
                raise UserError('The product price of the %s line does not have an adequate format. Suitable formats, example: "$100,00"-"100,00"-"100"'%cont)
        return True

    @api.model
    def get_valid_price(self, price, cont):
        if price != "":
            price = price.replace("$","").replace(",",".")
        try:
            price_float = float(price)
            return price_float
        except:
            raise UserError('The product price of the %s line does not have an adequate format. Suitable formats, example: "$100,00"-"100,00"-"100"'%cont)
        return False
    
    @api.model
    def valid_product_code(self, archive_lines, product_obj):
        cont=0
        for line in archive_lines:
            cont += 1
            code = str(line.get('code',"")).strip()
            product_id = product_obj.search([('default_code','=',code)])
            if len(product_id) > 1:
                raise UserError("The product code of line %s, is duplicated in the system." % cont)
            if not product_id:
                raise UserError("The product code of line %s is not found in the system" % cont)

    @api.model
    def valid_columns_keys(self, archive_lines):
        columns = archive_lines[0].keys()
        #print "columns>>",columns
        text = "El Archivo csv debe contener las siguientes columnas: code, quantity y price. \nNo se encuentran las siguientes columnas en el Archivo:"; text2 = text
        if not 'code' in columns:
            text +="\n[ code ]"
        if not 'quantity' in columns:
            text +="\n[ quantity ]"
        if not 'price' in columns:
            text +="\n[ price ]"
        if text !=text2:
            raise UserError(text)
        return True
            
    @api.model
    def csv_validator(self, xml_name):
        name, extension = os.path.splitext(xml_name)
        return True if extension == '.csv' else False
