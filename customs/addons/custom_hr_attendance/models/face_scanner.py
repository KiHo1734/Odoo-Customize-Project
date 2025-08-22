from odoo import models, api
import face_recognition, base64, json, io
import numpy as np
from PIL import Image
import logging

_logger = logging.getLogger(__name__)

class FaceScanner(models.TransientModel):
    _name = "face.scanner"
    _description = "Scan face and find matching employee"

    @api.model
    def find_employee_by_image(self, image_base64, tolerance=0.6):
        try:
            img_data = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(img_data)).convert("RGB")
            rgb = np.array(image)
            unknown_encoding = face_recognition.face_encodings(rgb)
            if not unknown_encoding:
                return ["ไม่พบใบหน้าในรูป"]
            unknown_encoding = unknown_encoding[0]
        except Exception as e:
            _logger.error(f"Failed to decode image: {e}")
            return ["ไม่สามารถประมวลผลรูปภาพได้"]

        employees = self.env['hr.employee'].sudo().search([('face_encoding','!=',False)])
        known_encodings = []
        employee_names = []

        for emp in employees:
            try:
                enc = json.loads(emp.face_encoding)
                known_encodings.append(enc)
                employee_names.append(emp.name)
            except Exception as e:
                _logger.warning(f"Failed to load face_encoding for {emp.name}: {e}")

        matches = face_recognition.compare_faces(known_encodings, unknown_encoding, tolerance=tolerance)
        if True in matches:
            idx = matches.index(True)
            return [employee_names[idx]]
        else:
            return ["ไม่พบพนักงานที่ตรงกัน"]
