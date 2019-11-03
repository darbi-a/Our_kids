# coding: utf-8

{
    'name': 'Import Stock Picking XLS',
    'version': '11.0.1.0.0',
    'author': 'Mahmoud Naguib, itss',
    'website': 'http://www.itss-c.com',
    'license': 'AGPL-3',
    'category': 'Sales',
    'summary': 'Import Stock Picking from CSV',
    'depends': [
                'stock'
                ],
    'data': [

        'wizard/wizard_import_stock_picking.xml',
        'views/stock_picking.xml',
    ],
    'installable': True,
    'application': True,
    'demo': [],
    'test': []
}
