# -*- encoding: utf-8 -*-
{
    'name': 'spml purchase quality',
    'version': '1.0',
    'category': 'Purchases',
    'author':'magdy,telenoc',
    'description': """
    spml purchase quality
    """,
    'summary': 'spml purchase quality',
    'website': '',
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner.xml',
        'views/quality_control.xml',
    ],
    'depends': ['purchase', 'stock'],
}
