{
    "name": "HR Attendance Custom",
    "version": "1.0",
    'depends': [
        'base',
        'hr_attendance', 
        'mail',
        'web',
    ],
    "data": [
        "views/kiosk_camera_scan.xml",
    ],
    'installable': True,
    'application': False,
    'auto_install': True,
}
