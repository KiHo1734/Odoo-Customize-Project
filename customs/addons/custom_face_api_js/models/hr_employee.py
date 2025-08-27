# models/hr_employee.py
from odoo import models, fields, api
import base64
import pickle
import io
import numpy as np
from PIL import Image

try:
    import face_recognition
except ImportError:
    face_recognition = None

class HREmployee(models.Model):
    _inherit = "hr.employee"

    face_descriptor_json = fields.Text("Face Descriptor JSON") 
    face_encoding = fields.Binary("Face Encoding (serialized)", readonly=True)  

    @api.model
    def create(self, vals):
        rec = super().create(vals)
        if vals.get("image_1920"):
            rec._compute_face_descriptor()
        return rec

    def write(self, vals):
        res = super().write(vals)
        if vals.get("image_1920"):
            for rec in self:
                rec._compute_face_descriptor()
        return res

    def _compute_face_descriptor(self):
        for rec in self:
            if not rec.image_1920 or not face_recognition:
                rec.face_descriptor_json = False
                continue
            try:
                image_data = base64.b64decode(rec.image_1920)
                image = face_recognition.load_image_file(io.BytesIO(image_data))
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    descriptor = encodings[0].astype(np.float32) 
                    rec.face_descriptor_json = base64.b64encode(descriptor.tobytes()).decode()
                else:
                    rec.face_descriptor_json = False
            except Exception:
                rec.face_descriptor_json = False
