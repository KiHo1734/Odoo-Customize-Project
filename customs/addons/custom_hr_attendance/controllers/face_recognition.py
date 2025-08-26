# -*- coding: utf-8 -*-
import base64
import pickle
from io import BytesIO
from PIL import Image
import numpy as np
from odoo import http
from odoo.http import request

try:
    import face_recognition
except ImportError:
    face_recognition = None

class FaceScanController(http.Controller):

    @http.route('/hr_attendance/scan_face', type='json', auth='public', csrf=False, methods=['POST'])
    def scan_face(self, **post):
        if not face_recognition:
            return {'success': False, 'error': 'face_recognition library not available'}

        image_base64 = post.get('image_base64')
        if not image_base64:
            return {'success': False, 'error': 'No image provided'}

        try:
            img_bytes = base64.b64decode(image_base64)
            img = Image.open(BytesIO(img_bytes)).convert('RGB')
            img_np = np.array(img)
        except Exception as e:
            return {'success': False, 'error': f'Invalid image: {e}'}

        # หา encoding ของใบหน้าในภาพ
        face_locations = face_recognition.face_locations(img_np)
        if not face_locations:
            return {'success': False, 'error': 'No face detected'}
        encodings = face_recognition.face_encodings(img_np, face_locations)
        if not encodings:
            return {'success': False, 'error': 'No face encoding'}
        probe = encodings[0]

        # โหลด encoding ของพนักงาน
        employees = request.env['hr.employee'].sudo().search([('face_encoding','!=',False)])
        known_encodings = []
        known_names = []
        known_ids = []

        for emp in employees:
            try:
                vec = pickle.loads(base64.b64decode(emp.face_encoding))
                known_encodings.append(vec)
                known_names.append(emp.name)
                known_ids.append(emp.id)
            except Exception:
                continue

        if not known_encodings:
            return {'success': False, 'error': 'No enrolled employees'}

        # เปรียบเทียบ
        distances = face_recognition.face_distance(np.array(known_encodings), probe)
        best_idx = int(np.argmin(distances))
        best_distance = float(distances[best_idx])

        if best_distance <= 0.5:  # tolerance
            return {
                'success': True,
                'employee_id': known_ids[best_idx],
                'employee_name': known_names[best_idx],
                'distance': best_distance
            }

        return {'success': False, 'error': 'No match', 'distance': best_distance}
