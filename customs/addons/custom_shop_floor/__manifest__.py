{
    'name': 'Custom Shopfloor',
    'version': '1.0.0',
    'summary': 'Manufacturing Shopfloor',
    'description': """
        Custom Shopfloor application for manufacturing.
        Touch-friendly, full screen, real-time production control.
    """,
    'category': 'Manufacturing',
    'author': 'KIHO',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mrp',
    ],
    'depends': [
        'base',
        'web',
        'mrp',
        'hr',
        'barcodes',
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/shopfloor_templates.xml',
        'views/shopfloor_menu.xml',
        'views/shopfloor_workorder_kanban.xml',
        'views/shopfloor_workorder_form.xml',
        'views/shopfloor_button.xml'
    ],

    'assets': {
        'web.assets_frontend': [
            'shopfloor/static/src/js/shopfloor.js',
            'shopfloor/static/src/css/shopfloor.css',
        ],
        'web.assets_qweb': [
            'shopfloor/static/src/xml/shopfloor.xml',
        ],
    },

    'installable': True,
    'application': True,
    'auto_install': False,
}
