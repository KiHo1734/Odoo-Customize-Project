{
    'name': 'HR Employee Customization',
    'version': '1.0',
    'depends': ['hr', 'hr_skills'],
    'data': [
        'views/hr_employee_detail_view.xml',
        'views/position_history_view.xml',
        'security/ir.model.access.csv', 
        'views/hr_private_info_view.xml',
        'reports/employees_property_report.xml',
        'reports/employees_property_template.xml',
        'views/employee_skill_search.xml',
        'views/employee_skill_graph_view.xml',
        'reports/employees_skills_report.xml',
        'reports/employees_skills_template.xml',
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
