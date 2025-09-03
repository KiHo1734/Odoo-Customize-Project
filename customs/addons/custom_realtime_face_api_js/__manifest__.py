{
    "name": "HR Realtime Face API JS",
    "version": "1.0",
    "summary": "Face Recognition Attendance System with Kiosk Mode by using FaceAPI-JS",
    "category": "Human Resources",
    "depends": [
        "base",
        "hr_attendance",
        "mail",
        "web",
    ],
    "data": [
        "views/kiosk_camera_scan.xml",
        "views/hr_attendance_settings_views.xml",
    ],
    "external_dependencies": {
        "python": ["face_recognition", "cv2", "numpy", "Pillow"]
    },
    "installable": True,
    "application": False,
    "auto_install": False,
    "description": """
        Custom Realtime Face API JS (Kiosk Mode)
        ============================================

        This module integrates face-api.js for real-time face detection and recognition in kiosk-style attendance.

        Assets and resources:
        - face-api.js library is loaded from `static/lib/face-api.min.js`.
        - Models (tinyFaceDetector, face_landmark_68, face_recognition) must be placed under `static/models/`.

        Development and reference:
        - Official face-api.js repository: https://github.com/justadudewhohacks/face-api.js :contentReference[oaicite:0]{index=0}
    """,
}
