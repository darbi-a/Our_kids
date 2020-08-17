#-*- coding: utf-8 -*-
import os
import base64
import tempfile
from odoo.exceptions import UserError
from odoo import api, fields, models, _, SUPERUSER_ID
import xlrd



class ImportProductVariant(models.TransientModel):
    _name = "wizard.import.product.variant"

    file_data = fields.Binary('Archive', required=True,)
    file_name = fields.Char('File Name')
    # res_ids = fields.Integer('Resource IDs', readonly=True,)



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
        # Number of columns
        num_cols = worksheet.ncols
        # archive_lines = []
        # for line in workbook:
        #     archive_lines.append(line)
        # header
        headers = []
        for col_idx in range(0, num_cols):
            cell_obj = worksheet.cell(0, col_idx)
            headers.append(cell_obj.value)

        name_field = False
        barcode_field = False
        headers_lower = []
        attributes_dict = {}
        fields_dict = {}
        template_attributes = {}
        tag_att = {}
        attribute_obj = self.env['product.attribute']
        tag_obj = self.env['product.tag']
        count_items=[]
        count_variant=[]
        count_edit=[]
        item_edit=[]
        x=0
        last_id = self.env['product.product'].search([], order='id desc', limit=1).id
        new_id = last_id
        create=0
        ndx=new_id
        attribute_value_obj = self.env['product.attribute.value']
        i = 0
        product_idx = None
        for h in headers:
            lower = h.lower()
            headers_lower.append(lower)
            lower_split = lower.split(':') if lower else ''
            if lower == 'barcode':
                barcode_field =True

            if lower == 'name':
                name_field = True
                fields_dict[i] = lower
                product_idx = i
            elif len(lower_split) == 2 and lower_split[0].strip() == 'attribute':
                attribute_name = h.split(':')[1].strip()
                attribute = attribute_obj.search([('name','=',attribute_name)],limit=1)
                if not attribute:
                    attribute = attribute_obj.create({'name':attribute_name})
                attributes_dict[i] = attribute.id
            elif len(lower_split) == 1:
                fields_dict[i] = lower
            else:
                raise UserError(_('Invalid column name'))
            i += 1

        if not name_field:
            raise UserError(_('No name field found!'))
        if not barcode_field:
            raise UserError(_('No Barcode field found!'))
        import_data = {}
        ddd = 1
        xl_values = {}
        lst_field={}
        lstxx=[]
        for row_idx in range(1, worksheet.nrows):
            ddd +=1

            # Iterate through rows
            row_dict = {}
            product_name = None
            product_code = None
            prod_ref = None
            values = {}
            attribute_values = []

            for col_idx in range(0, num_cols):  # Iterate through columns
                cell_obj = worksheet.cell(row_idx, col_idx)  # Get cell object by row, col
                if cell_obj.value:
                    if col_idx in fields_dict:
                        field_name = fields_dict[col_idx]
                        values[field_name] = cell_obj.value
                        if col_idx == product_idx :
                            product_name = values[field_name]

                        elif fields_dict[col_idx] == 'barcode':
                            barcode = cell_obj.value
                            if isinstance(barcode, float):
                                barcode = int(cell_obj.value)
                                prod_code = str(barcode).split()
                            else:
                                prod_code = str(barcode).strip()
                            if isinstance(prod_code, list):
                                prod_code =prod_code[0]
                            product_code = prod_code

                            product2 = self.env['product.product'].search([('barcode', '=', product_code)])
                            # if product2:
                            #     count_edit = list(set(count_edit + product2.ids))
                            values[field_name] = product_code

                        elif fields_dict[col_idx] == 'default_code':
                            c =cell_obj.value
                            if isinstance(c, float):
                                c =  int(c)
                            values[field_name] = str(c)
                            prod_ref=values[field_name]
                        elif fields_dict[col_idx] == 'season_id':
                            season_id=self.env['product.season'].search([('name','=',cell_obj.value)])
                            if not season_id:
                                season_id = self.env['product.season'].create({'name':cell_obj.value})
                            values[field_name] = season_id.id

                        elif fields_dict[col_idx] == 'categ_id':
                            cat_id = cell_obj.value
                            categ_name = worksheet.cell(row_idx, col_idx + 1)
                            if isinstance(cat_id, float) or isinstance(cat_id, int) or isinstance(cat_id, str) :
                                category=self.env['product.category'].search([('id','=',int(cell_obj.value))])

                                if not category :
                                    if fields_dict[col_idx +1] == 'categ_name':
                                        category = self.env['product.category'].search([('name', '=', categ_name.value)],limit=1)
                                        if not category:
                                            raise UserError(_('Product category %s not exist!' %categ_name.value))
                                        else:
                                            values[field_name] = category.id
                                else:
                                    values[field_name] = category.id
                            else: raise UserError(_('The categ_id of  Product category %s  must be integer!' %categ_name.value))
                        elif fields_dict[col_idx] == 'tag_ids':
                            tags = cell_obj.value.split(',')
                            tag_ids = []
                            for t in tags:
                                tag_opj = tag_obj.search([('name', '=', t)], limit=1)
                                if tag_opj:
                                    tag_ids.append(tag_opj.id)
                                else:
                                    tag_opj = self.env['product.tag'].create({'name': t})
                                    tag_ids.append(tag_opj.id)

                            product = self.env['product.product'].search([('name', '=',product_name)]).ids
                            if x >= len(product):
                                 x=0
                            if product:
                                tag_att[product[x]] = tag_ids
                                new_id = ndx = product[x]
                                x+=1

                            else:
                                new_id += 1
                                tag_att[new_id] = tag_ids
                            tags_ids = tag_obj.browse(tag_ids)

                            values[field_name]=tag_ids
                        elif fields_dict[col_idx] == 'vendor_num':
                            vend_num = cell_obj.value
                            if isinstance(vend_num, float) or isinstance(vend_num, int) :
                                vend_num=int(vend_num)
                                values[field_name] = vend_num
                            else:
                                values[field_name] = vend_num
                    elif col_idx in attributes_dict:
                        attribute_id = attributes_dict[col_idx]
                        attribute_value_name = cell_obj.value
                        attribute_value = attribute_value_obj.search([('name','=',str(attribute_value_name)),('attribute_id','=',attribute_id)])
                        if not attribute_value:
                            attribute_value = attribute_value_obj.create({'name':str(attribute_value_name),'attribute_id':attribute_id})
                        attribute_values.append(attribute_value.id)
                        if product_code:
                            if product_code not in xl_values:
                                xl_values[product_code]=[]
                            xl_values[product_code] = list(set(xl_values[product_code] + attribute_values))


                            if not prod_ref in template_attributes:
                                template_attributes[prod_ref] = {}
                            if attribute_id and not attribute_id in template_attributes[prod_ref]:
                                template_attributes[prod_ref][attribute_id] = []
                            template_attributes[prod_ref][attribute_id].append(attribute_value.id)

                if col_idx == (num_cols -1):
                    if not prod_ref:
                        raise UserError(_('Empty Product Name!'))

                    if prod_ref not in import_data:
                        import_data[prod_ref] = {}
                    if not attribute_values:
                        import_data[prod_ref] = values.copy()
                    else:
                        attribute_values = list(set(attribute_values.copy()))
                        lstxx.append(attribute_values)
                        values['attribute'] = attribute_values
                        import_data[prod_ref][product_code] = values.copy()
                    if values['barcode'] not in lst_field:
                        lst_field[values['barcode']]= values



        x = 0
        temp_barcode=''
        if not template_attributes:
            for code in lst_field:
                x += 1
                fld = lst_field[code]
                default_code = fld.get('default_code')
                sale_price = fld.get('sale_price')
                prod_name = fld.get('name')
                barcode = fld.get('barcode')
                field_vals = lst_field[barcode]
                if fld.get('tag_ids'):
                    field_vals['tag_ids'] = [(6, 0, fld.get('tag_ids'))]
                product = self.env['product.product'].search([('barcode', '=', code)], limit=1)

                if not product:
                    product = self.env['product.product'].create(field_vals)
                    product_templ = product.product_tmpl_id
                    product_templ.default_code = default_code
                    # product_templ.list_price = sale_price
                    product_templ.list_price = 0
                    if product_templ.id not in count_items:
                        count_items.append(product_templ.id)
                    # if product.id not in count_variant:
                    #     count_variant.append(product.id)
                else:

                    product.write(field_vals)
                    product_templ = product.product_tmpl_id

                    # product_templ.list_price= sale_price
                    product_templ.list_price= 0
                    if product_templ.id not in item_edit:
                        item_edit.append(product_templ.id)

                    # if product.id not in count_variant:
                    #     count_variant.append(product.id)
        else:
            new_value=False
            for line in import_data:
                product_templ = self.env['product.product']
                vals = {}
                for code in import_data[line]:
                    x += 1
                    fld = import_data[line][code]
                    default_code =fld.get('default_code')
                    barcode = fld.get('barcode')
                    field_vals = lst_field[barcode]
                    field_vals['attribute_value_ids'] = [(6, 0, fld['attribute'])]
                    field_vals['list_price'] = 0
                    if fld.get('tag_ids'):
                        field_vals['tag_ids'] = [(6, 0, fld.get('tag_ids'))]

                    product = self.env['product.product'].search([('default_code', '=', default_code)],limit=1)
                    product_templ = product.product_tmpl_id
                    product_by_barcode = self.env['product.product'].search([('barcode', '=', barcode)])
                    if not product_by_barcode and product_templ:
                        new_value=True
                    if product_by_barcode:
                        product_templ = product_by_barcode.product_tmpl_id
                        field_vals['product_tmpl_id']= product_templ.id
                        product_by_barcode.write(field_vals)
                        if product_templ.id not in item_edit:
                            item_edit.append(product_templ.id)
                        if product_by_barcode.id not in count_edit:
                            count_edit.append(product_by_barcode.id)
                        continue

                    if not product_templ:
                        product = self.env['product.product'].create(field_vals)
                        product_templ = product.product_tmpl_id
                        product_templ.default_code = default_code
                        if product_templ.id not in count_items:
                            count_items.append(product_templ.id)
                        if product.id not in count_variant:
                            count_variant.append(product.id)
                        continue
                    else:
                        field_vals['product_tmpl_id'] = product_templ.id

                        product = self.env['product.product'].create(field_vals)
                        if product_templ.id not in item_edit and new_value:
                            item_edit.append(product_templ.id)

                        if product.id not in count_variant:
                            count_variant.append(product.id)
                        continue


                if product_templ and product_templ.product_variant_count > 1:
                    product_templ.attribute_line_ids = False
                    att = {}
                    variants = product_templ.with_prefetch().product_variant_ids
                    for vart in variants:
                        for line in vart.attribute_value_ids:
                            if line.attribute_id.id not in att:
                                att[line.attribute_id.id] = []
                                att[line.attribute_id.id].append(line.id)
                            else:
                                if line.id not in att[line.attribute_id.id]:
                                    att[line.attribute_id.id].append(line.id)
                    vals = {}
                    for v in att:
                        vals['attribute_line_ids'] = []
                        vals['attribute_line_ids'].append(
                            (0, 0, {'attribute_id': v, 'value_ids': [], })
                        )
                        for att_val in att[v]:
                            vals['attribute_line_ids'][-1][2]['value_ids'].append((4, att_val))
                        product_templ.sudo().write(vals)


                # if product_templ.attribute_line_ids:
                #     exist_val={}
                #     # if new_value:
                #     for lin in product_templ.attribute_line_ids:
                #         exist_val[lin.attribute_id.id]=[]
                #         for v in lin.value_ids:
                #             exist_val[lin.attribute_id.id].append(v.id)
                #
                #
                #     print("has temp ***",product_templ.attribute_line_ids)
                #     print("exist_val ***",exist_val)
                #     product_templ.attribute_line_ids = False
                #     if exist_val:
                #         temp_att=template_attributes[line]
                #         for ex in exist_val:
                #             for l in temp_att:
                #                 if ex == l:
                #                     x = list(set(exist_val[ex] +temp_att[l]))
                #                     template_attributes[line][l]=x
                # print("New line ***", template_attributes[line])
                # for att in template_attributes[line]:
                #     print("att == ",att)
                #     vals['attribute_line_ids'] = []
                #     vals['attribute_line_ids'].append(
                #         (0, 0, {'attribute_id':att, 'value_ids': [], })
                #     )
                #     for att_val in template_attributes[line][att]:
                #         print("att_val == ", att_val)
                #         vals['attribute_line_ids'][-1][2]['value_ids'].append((4, att_val))
                #     print("vals == ", vals)
                #     if product_templ:
                #         print("*** att == ", att)
                #         product_templ.sudo().write(vals)

        context = dict(self._context) or {}
        context['default_count_variant'] = len(count_variant)
        context['lst_count_variant'] = count_variant

        context['default_count_items'] = len(count_items)
        context['lst_count_items'] = count_items

        context['default_count_edit'] = len(count_edit)
        context['lst_count_edit'] = count_edit

        context['default_count_items_edit'] = len(item_edit)
        context['lst_count_items_edit'] = item_edit
        return {
            'name': 'Import Resalt',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.resalt.variant',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': self.env.ref('import_product_variant.resalt_import_product_variant').id,
            'context': context,
            'target': 'new',
        }

    @api.model
    def csv_validator(self, xml_name):
        name, extension = os.path.splitext(xml_name)
        return True if extension == '.xls' or extension == '.xlsx' else False

    def get_attributes(self):

        temp_ids = self.env['product.template'].search([('attribute_line_ids','=',False),('product_variant_count','>',1)])

        for rec in temp_ids:
            if rec.product_variant_count > 1:
                att = {}
                variants = rec.with_prefetch().product_variant_ids
                for vart in variants:
                    for line in vart.attribute_value_ids:
                        if line.attribute_id.id not in att:
                            att[line.attribute_id.id] = []
                            att[line.attribute_id.id].append(line.id)
                        else:
                            if line.id not in att[line.attribute_id.id]:
                                att[line.attribute_id.id].append(line.id)
                vals={}
                for v in att:
                    vals['attribute_line_ids'] = []
                    vals['attribute_line_ids'].append(
                        (0, 0, {'attribute_id': v, 'value_ids': [], })
                    )
                    for att_val in att[v]:
                        vals['attribute_line_ids'][-1][2]['value_ids'].append((4, att_val))
                    rec.sudo().write(vals)

    def assin_seller(self):
        temp_ids = self.env['product.product'].search([('vendor_num','!=',False),('seller_ids','=',False),('variant_seller_ids','=',False)],limit=1000)
        print("#temp_ids ==> ",len(temp_ids))
        x=1
        for rec in temp_ids:
            print("xx= => ",x," ** ",rec.id)
            x+=1
            if rec.vendor_num and not rec.seller_ids and not rec.variant_seller_ids:
                vendor = self.env['res.partner'].search([('ref', '=', rec.vendor_num)], limit=1)
                if vendor:
                    self.env['product.supplierinfo'].create({
                        'product_tmpl_id': rec.product_tmpl_id.id,
                        'name': vendor.id,
                    })
    def delete_all_sellers(self):
        sellers = self.env['product.supplierinfo']
        sql = "delete from %s" % sellers._table
        self._cr.execute(sql)

