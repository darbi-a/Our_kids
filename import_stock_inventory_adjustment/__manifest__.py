# coding: utf-8

{
    'name': 'Import Stock Inventory Adjustment XLS',
    'version': '11.0.1.0.0',
    'author': 'Mahmoud Naguib, itss',
    'website': 'http://www.itss-c.com',
    'license': 'AGPL-3',
    'category': 'Stock',
    'summary': 'Import Stock Inventory Adjustment CSV',
    'depends': [
                'stock'
                ],
    'data': [

        'wizard/wizard_import_stock_inventory.xml',
        'views/stock_inventory.xml',
    ],
    'installable': True,
    'application': True,
    'demo': [],
    'test': []
}
