# coding: utf-8
##############################################################################
#
#
##############################################################################

{
    'name': 'Import product Variants',
    'version': '12.4.7',
    'author': 'Ahmed Amen ,Mahmoud Naguib',
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
        'data/migrate.xml',
        'wizard/wizard_import_product_variant.xml',
        'wizard/wizard_resalt_variant.xml',
        'views/product_template.xml',
        'views/product_product.xml',

    ],
    'installable': True,
    'application': True,
    'demo': [],
    'test': []
}
