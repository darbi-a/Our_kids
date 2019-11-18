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
        for row_idx in range(1, worksheet.nrows):
            ddd +=1

            # Iterate through rows
            row_dict = {}
            product_name = None
            product_code = None
            values = {}
            attribute_values = []
            for col_idx in range(0, num_cols):  # Iterate through columns
                cell_obj = worksheet.cell(row_idx, col_idx)  # Get cell object by row, col

                if not cell_obj.value:
                    raise UserError(_('Empty Row value!'))
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
                            if product2:
                                count_edit = list(set(count_edit + product2.ids))
                            values[field_name] = product_code

                        elif fields_dict[col_idx] == 'default_code':
                            values[field_name] = str(cell_obj.value)
                        elif fields_dict[col_idx] == 'season_id':
                            season_id=self.env['product.season'].search([('name','=',cell_obj.value)],limit=1)
                            if not season_id:
                                season_id = self.env['product.season'].create({'name':cell_obj.value})
                            values[field_name] = season_id.id

                        elif fields_dict[col_idx] == 'categ_id':
                            category=self.env['product.category'].search([('name','=',cell_obj.value)],limit=1)
                            if not category:
                                raise UserError(_('Product category %s not exist!' %cell_obj.value))
                            else:    # season_id = self.env['product.season'].create({'name':cell_obj.value})
                                values[field_name] = category.id
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
                    elif col_idx in attributes_dict:
                        attribute_id = attributes_dict[col_idx]
                        attribute_value_name = cell_obj.value
                        attribute_value = attribute_value_obj.search([('name','=',str(attribute_value_name)),('attribute_id','=',attribute_id)])
                        if not attribute_value:
                            attribute_value = attribute_value_obj.create({'name':str(attribute_value_name),'attribute_id':attribute_id})
                        attribute_values.append(attribute_value.id)
                        if product_name:
                            if not product_name in template_attributes:
                                template_attributes[product_name] = {}
                            if attribute_id and not attribute_id in template_attributes[product_name]:
                                template_attributes[product_name][attribute_id] = []
                            template_attributes[product_name][attribute_id].append(attribute_value.id)

                if col_idx == (num_cols -1):
                    if not product_name:
                        raise UserError(_('Empty Product Name!'))
                    if not product_code:
                        raise UserError(_('Empty Product Barcode!'))
                    if product_code not in import_data:
                        import_data[product_code] = {}
                    if not attribute_values:
                        import_data[product_code] = values.copy()

                    else:
                        attribute_values = list(set(attribute_values.copy()))
                        import_data[product_code][tuple(attribute_values)] = values.copy()



        x = 0

        temp_barcode=''
        for code in import_data:
            x +=1
            if not template_attributes:
                prod_name = import_data[code]['name']
                default_code = import_data[code]['default_code']
                product_templ = self.env['product.template'].search([('barcode', '=', code)])
            else:
                value = next(iter(import_data[code]))
                prod_name = import_data[code][value]['name']
                default_code = import_data[code][value]['default_code']

                product_templ = self.env['product.template'].search([('default_code', '=', default_code)],limit=1)

                if not product_templ:
                    product = self.env['product.product'].search([('default_code', '=', default_code)], limit=1)
                    product_templ =product.product_tmpl_id
            if not product_templ:
                print("xx == ", x, "product_templ = ", product_templ)
                vals = {}
                vals['name'] = prod_name
                vals['barcode'] = code
                vals['default_code'] = default_code
                vals['attribute_line_ids'] = []
                temp_barcode=code
                if prod_name in template_attributes:
                    for tmp_attrib in template_attributes[prod_name]:
                        vals['attribute_line_ids'].append(
                            (0, 0, {'attribute_id': tmp_attrib,
                                    'value_ids': [], })
                        )

                        for att_val in set(template_attributes[prod_name][tmp_attrib]):
                            vals['attribute_line_ids'][-1][2]['value_ids'].append((4, att_val))

                product_templ = self.env['product.template'].create(vals)

                if product_templ.id not in count_items:

                    count_items.append(product_templ.id)


            else:
                temp_atts  = product_templ.attribute_line_ids.mapped('attribute_id')
                product_templ.default_code = default_code
                if template_attributes:
                    for tmp_attrib in template_attributes[prod_name]:
                        tmp_att_vals = []
                        for att_val in set(template_attributes[prod_name][tmp_attrib]):
                            tmp_att_vals.append((4, att_val))
                        if tmp_attrib not in temp_atts.ids:
                            vals = {
                                'product_tmpl_id': product_templ.id,
                                'attribute_id': tmp_attrib,
                                'value_ids': tmp_att_vals,
                            }

                            # self.env['product.template.attribute.line'].create({
                            #     'product_tmpl_id': product_templ.id,
                            #     'attribute_id': tmp_attrib,
                            #     'value_ids': tmp_att_vals,
                            # })

                            product_templ.write({'attribute_line_ids':[(0,0,vals)],'default_code':default_code})
                            # product_templ.write({'attribute_line_ids':[(0,0,vals)]})

                        else:
                            product_templ.write({'default_code':default_code})

                            for att_tmpl_line in product_templ.attribute_line_ids:

                                if att_tmpl_line.attribute_id.id == tmp_attrib:
                                    att_tmpl_line.write({'value_ids': tmp_att_vals})
                                    break


                product_templ.create_variant_ids()
                if product_templ.id not in item_edit and product_templ.barcode == code:
                    item_edit.append(product_templ.id)

            prod_obj = self.env['product.product'].search([('barcode','=',code)])
            if not prod_obj:
                prod_obj= self.env['product.product'].search([('barcode','=',False),('name','=',prod_name)],limit=1,order='id')
            if not prod_obj:
                prod_obj = self.env['product.product'].search(
                    [('barcode', '=', False), ('product_tmpl_id', '=', product_templ.id)],limit=1,order='id')
            lst_vrnt=prod_obj.ids

            if lst_vrnt not in count_variant and count_items:
                count_variant = list(set(count_variant + lst_vrnt))
            # for prod in product_templ.product_variant_ids:
            if prod_obj:
                if not prod_obj.barcode or prod_obj.barcode != code :
                    prod_obj.write({'barcode':code})
                    if not prod_obj.barcode:
                        prod_obj.barcode = code
                if not template_attributes:
                    tags=import_data[prod_obj.barcode]['tag_ids']
                else:
                    value = next(iter(import_data[prod_obj.barcode]))
                    tags = import_data[prod_obj.barcode][value]['tag_ids']
                if tag_att:
                    prod_obj.write({'tag_ids': [(6, 0, tags)]})

                prod_att_values = set(prod_obj.attribute_value_ids.ids or [])

                for att_value_ids in import_data[prod_obj.barcode].keys():
                    if not template_attributes:
                        product_values = import_data[prod_obj.barcode]
                    else:
                        product_values = import_data[prod_obj.barcode][att_value_ids]
                    prod_obj.write(product_values.copy())

        context = dict(self._context) or {}
        context['default_count_variant'] = len(count_variant)
        context['default_count_items'] = len(count_items)
        context['default_count_edit'] = len(count_edit)
        context['default_count_items_edit'] = len(item_edit)
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

# {'809020001': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '6058.0', 'name': 'toykraft- Make Designer Drops', 'barcode': '809020001', 'standard_price': 71.92, 'lst_price': 89.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Accessory Making', 'vendor_color': 'Non'}}, '809020002': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '4801.0', 'name': 'toykraft-الهند- برواز صور', 'barcode': '809020002', 'standard_price': 108.0, 'lst_price': 135.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Accessory Making', 'vendor_color': 'Non'}}, '809020003': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '39608', 'name': 'toykraft Make Chic Creations', 'barcode': '809020003', 'standard_price': 71.92, 'lst_price': 89.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Accessory Making', 'vendor_color': 'Non'}}, '809020004': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '6102.0', 'name': 'toykraft- Jewelry Bash', 'barcode': '809020004', 'standard_price': 71.92, 'lst_price': 89.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Accessory Making', 'vendor_color': 'Non'}}, '809020005': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '3705.0', 'name': 'الهند- ميكانوصغيرtoykraft', 'barcode': '809020005', 'standard_price': 63.92, 'lst_price': 85.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Assembly Sets', 'vendor_color': 'Non'}}, '809020006': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '3712.0', 'name': 'لهند- ميكانوصغير طيارةtoykraft', 'barcode': '809020006', 'standard_price': 68.0, 'lst_price': 85.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Assembly Sets', 'vendor_color': 'Non'}}, '809020007': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '11903', 'name': 'baby doll35cm drink&wet&accessories (china)فراولة', 'barcode': '809020007', 'standard_price': 172.0, 'lst_price': 215.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Baby Doll', 'vendor_color': 'Non'}}, '809020008': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '11206', 'name': '12 inch doll with skateboard shoesروز', 'barcode': '809020008', 'standard_price': 180.0, 'lst_price': 225.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Baby Doll', 'vendor_color': 'Non'}}, '809020009': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '11867', 'name': 'baby doll30drink&wet&baby carriers(china)روز', 'barcode': '809020009', 'standard_price': 220.0, 'lst_price': 275.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Baby Doll', 'vendor_color': 'Non'}}, '809020010': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '11006', 'name': '18 inch doll with cry drink .pee&poo(china)', 'barcode': '809020010', 'standard_price': 383.2, 'lst_price': 479.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Baby Doll', 'vendor_color': 'Non'}}, '809020011': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '11825', 'name': 'baby doll40drink&wet&(china)clothing stickerبينك', 'barcode': '809020011', 'standard_price': 295.92, 'lst_price': 369.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Baby Doll', 'vendor_color': 'Non'}}, '809020012': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '11206', 'name': '12 inch doll with skateboard shoesازرق', 'barcode': '809020012', 'standard_price': 180.0, 'lst_price': 225.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Baby Doll', 'vendor_color': 'Non'}}, '809020013': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '11207', 'name': '12 inch dolls with make up set (china)موف', 'barcode': '809020013', 'standard_price': 204.0, 'lst_price': 255.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Baby Doll', 'vendor_color': 'Non'}}, '809020014': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '11903', 'name': 'baby doll35cm drink&wet&accessories (china)يونيكورن', 'barcode': '809020014', 'standard_price': 172.0, 'lst_price': 215.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Baby Doll', 'vendor_color': 'Non'}}, '809020015': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '11924', 'name': 'baby doll30cm with accessories (china)ابيض', 'barcode': '809020015', 'standard_price': 196.0, 'lst_price': 245.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Baby Doll', 'vendor_color': 'Non'}}, '809020016': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '11924', 'name': 'baby doll30cm with accessories (china)روز', 'barcode': '809020016', 'standard_price': 196.0, 'lst_price': 245.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Baby Doll', 'vendor_color': 'Non'}}, '809020017': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '11872', 'name': 'baby doll30drink&wet&(china)swimming ringبينك', 'barcode': '809020017', 'standard_price': 239.92, 'lst_price': 299.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Baby Doll', 'vendor_color': 'Non'}}, '809020018': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '11903', 'name': 'baby doll35cm drink&wet&accessories (china)فيل', 'barcode': '809020018', 'standard_price': 172.0, 'lst_price': 215.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Baby Doll', 'vendor_color': 'Non'}}, '809020019': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '11888', 'name': 'styling head doll (china)', 'barcode': '809020019', 'standard_price': 295.92, 'lst_price': 369.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Baby Doll', 'vendor_color': 'Non'}}, '809020020': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '11005', 'name': '18 inch doll with cry drink .pee&poo(china)', 'barcode': '809020020', 'standard_price': 383.2, 'lst_price': 479.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Baby Doll', 'vendor_color': 'Non'}}, '809020021': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '11903', 'name': 'baby doll35cm drink&wet&accessories (china)بطوط', 'barcode': '809020021', 'standard_price': 172.0, 'lst_price': 215.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Baby Doll', 'vendor_color': 'Non'}}, '809020022': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '11003', 'name': '18 inch doll with cry drink .pee&poo(china)', 'barcode': '809020022', 'standard_price': 383.92, 'lst_price': 479.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Baby Doll', 'vendor_color': 'Non'}}, '809020023': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '11872', 'name': 'baby doll30drink&wet&(china)swimming ringاخضر', 'barcode': '809020023', 'standard_price': 239.92, 'lst_price': 299.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Baby Doll', 'vendor_color': 'Non'}}, '809020024': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '11990', 'name': 'baby doll 40cm soft baby with ic(china)بينك', 'barcode': '809020024', 'standard_price': 215.92, 'lst_price': 269.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Baby Doll', 'vendor_color': 'Non'}}, '809020025': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '11903', 'name': 'baby doll35cm drink&wet&accessories (china)اناناس', 'barcode': '809020025', 'standard_price': 172.0, 'lst_price': 215.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Baby Doll', 'vendor_color': 'Non'}}, '809020026': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '11903', 'name': 'baby doll35cm drink&wet&accessories (china)ارنوب', 'barcode': '809020026', 'standard_price': 172.0, 'lst_price': 215.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Baby Doll', 'vendor_color': 'Non'}}, '809020027': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '11207', 'name': '12 inch dolls with make up set (china)روز', 'barcode': '809020027', 'standard_price': 204.0, 'lst_price': 255.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Baby Doll', 'vendor_color': 'Non'}}, '809020028': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '11825', 'name': 'baby doll40drink&wet&(china)clothing stickerلبني', 'barcode': '809020028', 'standard_price': 295.92, 'lst_price': 369.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Baby Doll', 'vendor_color': 'Non'}}, '809020029': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '11990', 'name': 'baby doll 40cm soft baby with ic(china)لبني', 'barcode': '809020029', 'standard_price': 215.92, 'lst_price': 269.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Baby Doll', 'vendor_color': 'Non'}}, '809020030': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '11867', 'name': 'baby doll30drink&wet&baby carriers(china)ابيض*بينك', 'barcode': '809020030', 'standard_price': 220.0, 'lst_price': 275.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Baby Doll', 'vendor_color': 'Non'}}, '809020031': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '203', 'name': 'عجلة ثلاث عجلات بيد china', 'barcode': '809020031', 'standard_price': 799.9, 'lst_price': 999.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Bicycles', 'vendor_color': 'Non'}}, '809020032': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '202', 'name': 'عجلة بيد وشمشية 3*1 china', 'barcode': '809020032', 'standard_price': 1439.92, 'lst_price': 1799.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Bicycles', 'vendor_color': 'Non'}}, '809020033': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '353', 'name': 'عجلة بلاستيك بشنطة-اسبانياinjusa', 'barcode': '809020033', 'standard_price': 479.2, 'lst_price': 599.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Bicycles', 'vendor_color': 'Non'}}, '809020034': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '350', 'name': 'عجلة بلاستيك -اسبانياinjusa', 'barcode': '809020034', 'standard_price': 447.2, 'lst_price': 559.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Bicycles', 'vendor_color': 'Non'}}, '809020035': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '22119', 'name': '22119  jugle chess العاب جماعية frank india', 'barcode': '809020035', 'standard_price': 60.0, 'lst_price': 75.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Board Games', 'vendor_color': 'Non'}}, '809020036': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '7072.0', 'name': 'stencil art', 'barcode': '809020036', 'standard_price': 63.92, 'lst_price': 79.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Coloring Sets', 'vendor_color': 'Non'}}, '809020037': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '214.0', 'name': 'coloring art', 'barcode': '809020037', 'standard_price': 63.92, 'lst_price': 79.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Coloring Sets', 'vendor_color': 'Non'}}, '809020038': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '1571.0', 'name': 'china artkid تلوين+ مروحة', 'barcode': '809020038', 'standard_price': 68.0, 'lst_price': 85.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Coloring Sets', 'vendor_color': 'Non'}}, '809020039': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '8172.0', 'name': 'toykraft- ماسك -الهند', 'barcode': '809020039', 'standard_price': 127.92, 'lst_price': 159.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Coloring Sets', 'vendor_color': 'Non'}}, '809020040': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '77166', 'name': 'عروسة روز +اكسسوارت safia', 'barcode': '809020040', 'standard_price': 151.92, 'lst_price': 189.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Doll', 'vendor_color': 'Non'}}, '809020041': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '7108', 'name': 'safia عروسة روز +اكسسوارت', 'barcode': '809020041', 'standard_price': 79.92, 'lst_price': 99.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Doll', 'vendor_color': 'Non'}}, '809020042': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '77177', 'name': 'عروسة بنطلون رمادى+اكسسوارت safia', 'barcode': '809020042', 'standard_price': 159.92, 'lst_price': 199.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Doll', 'vendor_color': 'Non'}}, '809020043': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '77116', 'name': 'safia عروسة لبني مشجر +اكسسوارت', 'barcode': '809020043', 'standard_price': 87.92, 'lst_price': 109.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Doll', 'vendor_color': 'Non'}}, '809020044': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '77202', 'name': 'عروسة بنطلون منقط+اكسسوارت safia', 'barcode': '809020044', 'standard_price': 95.92, 'lst_price': 119.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Doll', 'vendor_color': 'Non'}}, '809020045': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '7717', 'name': 'safia عروسة روز*بينك +اكسسوارت', 'barcode': '809020045', 'standard_price': 103.92, 'lst_price': 129.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Doll', 'vendor_color': 'Non'}}, '809020046': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '77166', 'name': 'عروسة موف +اكسسوارت safia', 'barcode': '809020046', 'standard_price': 151.92, 'lst_price': 189.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Doll', 'vendor_color': 'Non'}}, '809020047': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '7734', 'name': 'safia عروسه  طباخه روز اكسسوار', 'barcode': '809020047', 'standard_price': 116.0, 'lst_price': 145.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Doll', 'vendor_color': 'Non'}}, '809020048': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '3099.0', 'name': 'safia عروسة بنطلون منقط +اكسسوارت', 'barcode': '809020048', 'standard_price': 95.92, 'lst_price': 119.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Doll', 'vendor_color': 'Non'}}, '809020049': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '77129', 'name': 'safia عروسة بنطلون مخطط+اكسسوارت', 'barcode': '809020049', 'standard_price': 87.92, 'lst_price': 109.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Doll', 'vendor_color': 'Non'}}, '809020050': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '7744', 'name': 'safia عروسة بنطلون مخطط+اكسسوارت', 'barcode': '809020050', 'standard_price': 95.92, 'lst_price': 119.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Doll', 'vendor_color': 'Non'}}, '809020051': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '77129', 'name': 'safia عروسة بنطلون سيلفر+اكسسوارت', 'barcode': '809020051', 'standard_price': 87.92, 'lst_price': 109.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Doll', 'vendor_color': 'Non'}}, '809020052': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '7757', 'name': 'safia عروسة لبنى +اكسسوارت', 'barcode': '809020052', 'standard_price': 95.92, 'lst_price': 119.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Doll', 'vendor_color': 'Non'}}, '809020053': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '7738', 'name': 'safia عروسة جيب منقط+اكسسوارت', 'barcode': '809020053', 'standard_price': 95.92, 'lst_price': 119.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Doll', 'vendor_color': 'Non'}}, '809020054': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '77780', 'name': 'safia عروسة  لبني قصير+اكسسوارت', 'barcode': '809020054', 'standard_price': 79.92, 'lst_price': 99.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Doll', 'vendor_color': 'Non'}}, '809020055': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '7756', 'name': 'safia عروسة بينك +اكسسوارت', 'barcode': '809020055', 'standard_price': 79.92, 'lst_price': 99.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Doll', 'vendor_color': 'Non'}}, '809020056': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '7756', 'name': 'safia عروسة بينك مشجر +اكسسوارت', 'barcode': '809020056', 'standard_price': 79.92, 'lst_price': 99.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Doll', 'vendor_color': 'Non'}}, '809020057': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '77129', 'name': 'safia عروسة بنطلون روز+اكسسوارت', 'barcode': '809020057', 'standard_price': 87.92, 'lst_price': 109.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Doll', 'vendor_color': 'Non'}}, '809020058': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '7108', 'name': 'safia عروسة سيلفر*بينك +اكسسوارت', 'barcode': '809020058', 'standard_price': 79.92, 'lst_price': 99.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Doll', 'vendor_color': 'Non'}}, '809020059': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '77780', 'name': 'safia عروسة لبني طويل +اكسسوارت', 'barcode': '809020059', 'standard_price': 79.92, 'lst_price': 99.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Doll', 'vendor_color': 'Non'}}, '809020060': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '7772', 'name': 'عروسة بينك*اسود +اكسسوارت safia', 'barcode': '809020060', 'standard_price': 159.92, 'lst_price': 199.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Doll', 'vendor_color': 'Non'}}, '809020061': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '7757', 'name': 'safia عروسة اخضر +اكسسوارت', 'barcode': '809020061', 'standard_price': 95.92, 'lst_price': 119.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Doll', 'vendor_color': 'Non'}}, '809020062': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '77780', 'name': 'safia عروسة موف+اكسسوارت', 'barcode': '809020062', 'standard_price': 79.92, 'lst_price': 99.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Doll', 'vendor_color': 'Non'}}, '809020063': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '7772', 'name': 'عروسة بينك*سيلفر+اكسسوارت safia', 'barcode': '809020063', 'standard_price': 159.92, 'lst_price': 199.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Doll', 'vendor_color': 'Non'}}, '809020064': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '7716', 'name': 'safia  عروسة مخطط*موف+اكسسوارت', 'barcode': '809020064', 'standard_price': 119.92, 'lst_price': 149.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Doll', 'vendor_color': 'Non'}}, '809020065': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '7734', 'name': 'safia عروسه طباخه مخطط اكسسوار', 'barcode': '809020065', 'standard_price': 116.0, 'lst_price': 145.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Doll', 'vendor_color': 'Non'}}, '809020066': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '77202', 'name': 'عروسة بنطلون رمادى+اكسسوارت safia', 'barcode': '809020066', 'standard_price': 95.92, 'lst_price': 119.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Doll', 'vendor_color': 'Non'}}, '809020067': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '7108', 'name': 'safia عروسة بينك*اسود +اكسسوارت', 'barcode': '809020067', 'standard_price': 79.92, 'lst_price': 99.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Doll', 'vendor_color': 'Non'}}, '809020068': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '77116', 'name': 'safia عروسة لبني*سيلفر+اكسسوارت', 'barcode': '809020068', 'standard_price': 87.92, 'lst_price': 109.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Doll', 'vendor_color': 'Non'}}, '809020069': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '7738', 'name': 'safia عروسة جيب ساده+اكسسوارت', 'barcode': '809020069', 'standard_price': 95.92, 'lst_price': 119.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Doll', 'vendor_color': 'Non'}}, '809020070': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '7711', 'name': 'safia عروسة لبني*سيلفر +اكسسوارت', 'barcode': '809020070', 'standard_price': 127.92, 'lst_price': 159.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Doll', 'vendor_color': 'Non'}}, '809020071': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '7713', 'name': 'safia عروسة بينك*روز +اكسسوارت', 'barcode': '809020071', 'standard_price': 103.92, 'lst_price': 129.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Doll', 'vendor_color': 'Non'}}, '809020072': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '5230.0', 'name': 'faro- تسريحة', 'barcode': '809020072', 'standard_price': 239.2, 'lst_price': 299.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Dressing Tables', 'vendor_color': 'Non'}}, '809020073': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '5209.0', 'name': 'faro-table vanity mirror', 'barcode': '809020073', 'standard_price': 368.0, 'lst_price': 460.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Dressing Tables', 'vendor_color': 'Non'}}, '809020074': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '1250', 'name': 'بتش بجى4 عجلات صغير-اسبانيا injusa', 'barcode': '809020074', 'standard_price': 1512.0, 'lst_price': 1890.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Electric Buggy', 'vendor_color': 'Non'}}, '809020075': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '663', 'name': '663 بتش باجى 4عجلات كبير INJUSA', 'barcode': '809020075', 'standard_price': 5596.0, 'lst_price': 6995.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Electric Buggy', 'vendor_color': 'Non'}}, '809020076': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '66055', 'name': 'بتيش بيجى وسط 12 فولت-اسبانيا injusa', 'barcode': '809020076', 'standard_price': 3676.0, 'lst_price': 4595.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Electric Buggy', 'vendor_color': 'Non'}}, '809020077': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '25', 'name': '25 عربية jy20L8  Jeep', 'barcode': '809020077', 'standard_price': 2918.5, 'lst_price': 4085.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Electric Cars', 'vendor_color': 'Non'}}, '809020078': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '9694.0', 'name': '20 عربيه بي ام دابليو', 'barcode': '809020078', 'standard_price': 2485.0, 'lst_price': 3630.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Electric Cars', 'vendor_color': 'Non'}}, '809020079': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '6811', 'name': 'موتوسيكل  12 فولت 2 موتور-اسبانيا injusa', 'barcode': '809020079', 'standard_price': 3996.0, 'lst_price': 4995.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Electric Motorbikes', 'vendor_color': 'Non'}}, '809020080': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': 'jy20a8', 'name': 'موتسيكل شحن 4 عجلات jy20a8', 'barcode': '809020080', 'standard_price': 1592.5, 'lst_price': 2229.5, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Electric Motorbikes', 'vendor_color': 'Non'}}, '809020081': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '6775', 'name': 'موتوسيكل كوزاكي 6 فولت-اسبانيا injusa', 'barcode': '809020081', 'standard_price': 3720.0, 'lst_price': 4650.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Electric Motorbikes', 'vendor_color': 'Non'}}, '809020082': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '3449.0', 'name': 'faro work center h.80', 'barcode': '809020082', 'standard_price': 600.0, 'lst_price': 750.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Engineer', 'vendor_color': 'Non'}}, '809020083': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '243', 'name': 'work center hotweel faro', 'barcode': '809020083', 'standard_price': 632.0, 'lst_price': 790.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Engineer', 'vendor_color': 'Non'}}, '809020084': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '5938.0', 'name': 'toykraft- Sequin Pictures - Pups', 'barcode': '809020084', 'standard_price': 71.92, 'lst_price': 89.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Gift Making', 'vendor_color': 'Non'}}, '809020085': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '4399.0', 'name': '39439 صندوق الهدايا', 'barcode': '809020085', 'standard_price': 55.92, 'lst_price': 69.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Gift Making', 'vendor_color': 'Non'}}, '809020086': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '6003.0', 'name': 'toykraft- Stylish Hair Bands', 'barcode': '809020086', 'standard_price': 124.0, 'lst_price': 155.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Hair Styling', 'vendor_color': 'Non'}}, '809020087': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '2503.0', 'name': 'faro  trolly with  tolla &car', 'barcode': '809020087', 'standard_price': 423.2, 'lst_price': 529.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'kitchen Tools', 'vendor_color': 'Non'}}, '809020088': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '4214.0', 'name': 'toykraft- Make A Candle Stand', 'barcode': '809020088', 'standard_price': 71.92, 'lst_price': 89.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Molding', 'vendor_color': 'Non'}}, '809020089': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '4986.0', 'name': 'toykreft-hobby family-india', 'barcode': '809020089', 'standard_price': 60.0, 'lst_price': 75.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Molding', 'vendor_color': 'Non'}}, '809020090': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '6133.0', 'name': "toykraft- Mould 'n' Paint", 'barcode': '809020090', 'standard_price': 159.9, 'lst_price': 199.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Molding', 'vendor_color': 'Non'}}, '809020091': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '4803.0', 'name': 'modeling clay 15pcs', 'barcode': '809020091', 'standard_price': 36.0, 'lst_price': 45.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Molding', 'vendor_color': 'Non'}}, '809020092': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '5921.0', 'name': 'toykraft Sequin Pictures  Birds', 'barcode': '809020092', 'standard_price': 71.92, 'lst_price': 89.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Mosaic', 'vendor_color': 'Non'}}, '809020093': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '4580.0', 'name': 'toykraft- الهند-صندوق مجوهرات صدف', 'barcode': '809020093', 'standard_price': 127.92, 'lst_price': 159.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Mosaic', 'vendor_color': 'Non'}}, '809020094': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '6201.0', 'name': 'toykraft-Egg carton craft', 'barcode': '809020094', 'standard_price': 108.0, 'lst_price': 135.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Paper Crafting', 'vendor_color': 'Non'}}, '809020095': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '5280.0', 'name': '39528 العاب ورقيه', 'barcode': '809020095', 'standard_price': 52.0, 'lst_price': 65.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Paper Crafting', 'vendor_color': 'Non'}}, '809020096': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '5334.0', 'name': '39533 paper quilling finger', 'barcode': '809020096', 'standard_price': 63.2, 'lst_price': 79.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Paper Crafting', 'vendor_color': 'Non'}}, '809020097': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '5396.0', 'name': 'toykraft- Celebrate With Greeting', 'barcode': '809020097', 'standard_price': 159.92, 'lst_price': 199.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Paper Crafting', 'vendor_color': 'Non'}}, '809020098': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '6688.0', 'name': 'صلصال بيتيزا FARO', 'barcode': '809020098', 'standard_price': 120.0, 'lst_price': 150.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Play Dough', 'vendor_color': 'Non'}}, '809020099': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '9419.0', 'name': 'frank indiaبذل اجزاء الجسم عربى', 'barcode': '809020099', 'standard_price': 39.9, 'lst_price': 49.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Puzzles', 'vendor_color': 'Non'}}, '809020100': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '1121.0', 'name': 'puzzle candid coloursartkraft', 'barcode': '809020100', 'standard_price': 63.92, 'lst_price': 79.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Puzzles', 'vendor_color': 'Non'}}, '809020101': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '9631.0', 'name': 'jy2c903-926 2لون زحافة', 'barcode': '809020101', 'standard_price': 419.3, 'lst_price': 588.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Ride-ons', 'vendor_color': 'Non'}}, '809020102': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '60429.0', 'name': 'artkids weaving', 'barcode': '809020102', 'standard_price': 151.92, 'lst_price': 189.9, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Sewing', 'vendor_color': 'Non'}}, '809020103': {('default_code', 'name', 'barcode', 'standard_price', 'lst_price', 'type', 'tag_ids', 'season_id', 'vendor_num', 'categ_num', 'vendor_color'): {'default_code': '2002', 'name': 'زحليقه 5 درجة- اسبانياinjusa', 'barcode': '809020103', 'standard_price': 2800.0, 'lst_price': 3500.0, 'type': 'product', 'tag_ids': [(6, 0, [18])], 'season_id': 14, 'vendor_num': '10015', 'categ_num': 'Slides', 'vendor_color': 'Non'}}}
