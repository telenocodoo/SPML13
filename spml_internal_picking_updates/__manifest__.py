# -*- coding: utf-8 -*-
{
    'name': "Spml Internal Picking",
    'summary': """Spml Internal Picking""",
    'description': """Spml Internal Picking""",
    'author': "Magdy,TeleNoc",
    'website': "https://telenoc.org",
    'category': 'stock',
    'version': '0.13',
    'depends': ['base', 'material_purchase_requisitions'],
    'data': [
        # 'security/ir.model.access.csv',
        # 'security/security.xml',
        'views/purchase_requisition_setting.xml',
        'views/purchase_requisition.xml',
    ],
}
