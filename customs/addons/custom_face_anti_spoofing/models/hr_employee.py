# models/hr_employee.py
from odoo import models, fields, api
import base64
import pickle
import io
import numpy as np
from PIL import Image
from odoo.exceptions import ValidationError

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
    
    def _validate_face_image(self, image_data):
        """
        return (True, None) หรือ (False, error_message)
        """
        try:
            image = face_recognition.load_image_file(io.BytesIO(image_data))
        except Exception:
            return False, "ไม่สามารถอ่านไฟล์รูปได้"

        # ตรวจตำแหน่งใบหน้า
        face_locations = face_recognition.face_locations(image)

        if not face_locations:
            return False, "ไม่พบใบหน้าในรูป"

        if len(face_locations) > 1:
            return False, "พบหลายใบหน้า กรุณาใช้รูปที่มีหน้าเดียว"

        # ตรวจขนาดใบหน้า (กันรูปเล็ก/ไกลเกิน)
        top, right, bottom, left = face_locations[0]
        face_width = right - left
        face_height = bottom - top

        if face_width < 80 or face_height < 80:
            return False, "ใบหน้ามีขนาดเล็กเกินไป"
        
        # หลังจากโหลด image
        if not self._is_face_frontal(image):
            return False, "กรุณาหันหน้าตรง ไม่เอียงหรือหันข้าง"

        return True, None
    
    def _is_face_frontal(self, image):
        landmarks_list = face_recognition.face_landmarks(image)

        if not landmarks_list:
            return False

        landmarks = landmarks_list[0]

        # ต้องมีตาและจมูกครบ
        if 'left_eye' not in landmarks or 'right_eye' not in landmarks or 'nose_bridge' not in landmarks:
            return False

        left_eye = np.mean(landmarks['left_eye'], axis=0)
        right_eye = np.mean(landmarks['right_eye'], axis=0)
        nose = np.mean(landmarks['nose_bridge'], axis=0)

        # ระยะตาซ้าย-ขวา
        eye_distance = np.linalg.norm(left_eye - right_eye)

        # ระยะ nose ถึงกึ่งกลางตา
        eye_center = (left_eye + right_eye) / 2
        nose_offset = abs(nose[0] - eye_center[0])

        # ถ้าจมูกเบี่ยงจากกลางมาก = หน้าหัน
        if nose_offset > eye_distance * 0.15:
            return False

        return True

    def _compute_face_descriptor(self):
        for rec in self:
            if not rec.image_1920 or not face_recognition:
                rec.face_descriptor_json = False
                continue

            try:
                image_data = base64.b64decode(rec.image_1920)

                is_valid, error = rec._validate_face_image(image_data)
                if not is_valid:
                    rec.face_descriptor_json = False
                    raise ValidationError(error)

                image = face_recognition.load_image_file(io.BytesIO(image_data))
                encodings = face_recognition.face_encodings(image)

                if encodings:
                    descriptor = encodings[0].astype(np.float32)
                    rec.face_descriptor_json = base64.b64encode(
                        descriptor.tobytes()
                    ).decode()
                else:
                    rec.face_descriptor_json = False

            except ValidationError:
                # ปล่อยให้ Odoo แสดง error ให้ user
                raise

            except Exception as e:
                rec.face_descriptor_json = False
                raise ValidationError("เกิดข้อผิดพลาดในการประมวลผลรูปใบหน้า")


