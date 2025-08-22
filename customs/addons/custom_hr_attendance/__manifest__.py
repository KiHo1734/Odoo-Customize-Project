{
    "name": "HR Attendance Customization",
    "version": "1.0",
    "summary": "Face Recognition Attendance System with Kiosk Mode",
    "category": "Human Resources",
    "depends": [
        "base",
        "hr_attendance",
        "mail",
        "web",
    ],
    "data": [
        "views/kiosk_camera_scan.xml",
        "views/hr_employee_views.xml",
    ],
    "external_dependencies": {
        "python": ["face_recognition", "cv2", "numpy", "Pillow"]
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
