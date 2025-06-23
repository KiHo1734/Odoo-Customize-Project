{
    'name': 'HR Employee Customization',
    'version': '1.0',
    'depends': ['hr'],
    'data': [
        'views/hr_employee_view.xml',
        'views/position_history_view.xml',
        'security/ir.model.access.csv', 
    ],
    'assets': {
        'web.assets_backend': [
            'custom_hr_employee/static/src/js/position_history.js',
            'custom_hr_employee/static/src/scss/position_history.scss',
        ],
    },
    'installable': True,
    'application': False,
}
