{
    "name": "HR Anti Spoof Face Scan",
    "version": "1.0",
    "summary": "Face Recognition Attendance System with Kiosk Mode by using mediapie and silent face spoofing",
    "category": "Human Resources",
    "depends": [
        "base",
        "hr_attendance",
        "mail",
        "web",
    ],
    "data": [
        "views/kiosk_camera_scan.xml",
    ],
    "external_dependencies": {
        "python": ["face_recognition", "cv2", "numpy", "Pillow"]
    },
    "installable": True,
    "application": False,
    "auto_install": False,
    "description": """
        Custom HR Anti Spoof Face Scan (Kiosk Mode)
        ============================================

        This module integrates mediapie and silent face spoofing for real-time face detection and recognition in kiosk-style attendance.

        Assets and resources:
        - Silent-Face-Anti-Spoofing library is loaded from `customs/addons/custom_face_anti_spoofing/static/lib/Silent-Face-Anti-Spoofing-master`.

        Development and reference:
        - Silent-Face-Anti-Spoofing repository: https://github.com/minivision-ai/Silent-Face-Anti-Spoofing :contentReference[oaicite:0]{index=0}
    """,
}
