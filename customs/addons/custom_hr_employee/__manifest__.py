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
             'custom_hr_employee/static/src/scss/employee_style.scss',
        ],
    },
    'installable': True,
    'application': False,
}
