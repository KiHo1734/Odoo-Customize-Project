import base64
import io
import pickle
import numpy as np
from PIL import Image
import face_recognition

from odoo import models, fields, api

class HREmployee(models.Model):
    _inherit = "hr.employee"

    face_encoding = fields.Binary("Face Encoding (serialized)", readonly=True)

    @api.model
    def create(self, vals):
        rec = super().create(vals)
        if vals.get("image_1920"):
            rec._compute_face_encoding_from_image()
        return rec

    def write(self, vals):
        res = super().write(vals)
        if vals.get("image_1920"):
            for rec in self:
                rec._compute_face_encoding_from_image()
        return res

    def _compute_face_encoding_from_image(self):
        """แปลง image_1920 → face encoding → serialize เก็บ"""
        for rec in self:
            if not rec.image_1920:
                rec.face_encoding = False
                continue

            try:
                # 1) decode base64 image
                image_data = base64.b64decode(rec.image_1920)
                image = Image.open(io.BytesIO(image_data)).convert("RGB")

                # 2) convert to numpy
                img_array = np.array(image)

                # 3) generate face encodings
                face_encodings = face_recognition.face_encodings(img_array)

                if face_encodings:
                    encoding = face_encodings[0]  # ใช้แค่ face แรก
                    serialized = pickle.dumps(encoding)  # serialize numpy array
                    rec.face_encoding = base64.b64encode(serialized)
                else:
                    rec.face_encoding = False

            except Exception as e:
                rec.face_encoding = False
                self.env["ir.logging"].create({
                    "name": "Face Encoding Error",
                    "type": "server",
                    "level": "ERROR",
                    "message": f"Error generating face encoding: {str(e)}",
                    "path": "hr_employee",
                    "line": "0",
                    "func": "_compute_face_encoding_from_image",
                })

    def action_check_face(self):
        """ทดสอบ load face encoding กลับมา"""
        for rec in self:
            if rec.face_encoding:
                encoding = pickle.loads(base64.b64decode(rec.face_encoding))
                print("Decoded face encoding shape:", encoding.shape)

    def action_regenerate_face_encodings(self):
        """ปุ่มกด regenerate face encoding"""
        for rec in self:
            rec._compute_face_encoding_from_image()
        return True
