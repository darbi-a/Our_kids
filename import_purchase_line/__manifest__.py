# coding: utf-8

{
    'name': 'Import Purchase Order Lines XLS',
    'version': '12.3',
    'author': 'Ahmed Amen',
    'license': 'AGPL-3',
    'category': 'Sales',
    'summary': 'Import Purchase Order Lines XLS',
    'depends': ['base',
                'purchase',
                'sale',
                ],
    'data': [

        'wizard/wizard_import_purchase_lines.xml',
        'views/purchase.xml',
    ],
    'installable': True,
    'application': True,
    'demo': [],
    'test': []
}
