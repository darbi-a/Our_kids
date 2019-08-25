# coding: utf-8
##############################################################################
#
#
##############################################################################

{
    'name': 'Import product Variants',
    'version': '12.0.5',
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
        'views/product_product.xml',
    ],
    'installable': True,
    'application': True,
    'demo': [],
    'test': []
}
