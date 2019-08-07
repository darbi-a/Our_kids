# coding: utf-8
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2017 Marlon Falcón Hernandez
#    (<http://www.falconsolutions.cl>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Import product Variants',
    'version': '1.0.0',
    'author': 'Ahmed Amin ,Mahmoud Naguib',
    'maintainer': 'ITSS',
    'license': 'AGPL-3',
    'category': 'Stock',
    'summary': 'Import product Variants by CSV or xls file',
    'depends': ['base',
                'stock',
                'sale',
                'product_tags',
                'product_season',
                ],
    'data': [

        'wizard/wizard_import_product_variant.xml',
    ],
    'installable': True,
    'application': True,
    'demo': [],
    'test': []
}
