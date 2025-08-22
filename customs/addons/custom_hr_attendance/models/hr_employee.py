from odoo import models, fields, api
import face_recognition
import numpy as np
import io
from PIL import Image
import json
import logging

_logger = logging.getLogger(__name__)

class HREmployee(models.Model):
    _inherit = 'hr.employee'

    face_encoding = fields.Text("Face Encoding")

    @api.model
    def _image_to_encoding(self, image_binary):
        """แปลงรูป binary เป็น face encoding"""
        try:
            image = Image.open(io.BytesIO(image_binary))
            rgb = np.array(image.convert("RGB"))
            encodings = face_recognition.face_encodings(rgb)
            if encodings:
                return encodings[0].tolist()
        except Exception as e:
            _logger.warning(f"Face encoding failed: {e}")
        return None

    @api.onchange('image_1920')
    def _onchange_image(self):
        if self.image_1920:
            encoding = self._image_to_encoding(self.image_1920)
            if encoding:
                self.face_encoding = json.dumps(encoding)

    def action_regenerate_face_encodings(self):
        """Regenerate manually"""
        for rec in self:
            if rec.image_1920:
                encoding = self._image_to_encoding(rec.image_1920)
                if encoding:
                    rec.face_encoding = json.dumps(encoding)
        return True
