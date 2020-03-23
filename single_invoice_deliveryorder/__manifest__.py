# -*- coding: utf-8 -*-

{
    'name': 'Single Invoice for Multiple Delivery Order',
    'category': 'Stock',
    'summary': 'This module will create single invoice for multiple delivery orders.',
    'version': '13.0',
    'website': 'http://www.HITechSolutions.com',
    'author': 'HITechSolutions',
    'description': 'Create single invoice for multiple delivery orders',
    'license': "AGPL-3",
    'depends': ['account','stock'],
    'data': [
        'wizard/single_vendor_bill_wizard_view.xml'
    ],

    'images': [
        '/static/description/image/delivery.jpg',
    ],

    'installable': True,
}



