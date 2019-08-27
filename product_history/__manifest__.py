# coding: utf-8
##############################################################################
#
#
##############################################################################

{
    'name': 'Product History',
    'version': '12.0.1',
    'author': 'Ahmed Amin ',
    'maintainer': 'ITSS',
    'license': 'AGPL-3',
    'category': 'Stock',
    'summary': 'Report for product show product history',
    'depends': ['base',
                'stock',
                'product',
                ],
    'data': [

        # 'wizard/wizard_import_product_variant.xml',
        'views/product.xml',
        'reports/report_template.xml',
    ],
    'installable': True,
    'application': True,
    'demo': [],
    'test': []
}
