import json
from odoo import http
from odoo.http import request
from datetime import datetime
import base64
import cv2
import numpy as np
from ..services.liveness_service import run_antispoof

class HREmployeeAPI(http.Controller):
    @http.route('/hr_employee/get_descriptors', type='json', auth='public', methods=['POST'])
    def get_descriptors(self):
        employees = request.env['hr.employee'].sudo().search([('face_descriptor_json', '!=', False)])
        data = []
        for emp in employees:
            data.append({
                'id': emp.id,
                'name': emp.name,
                'descriptor': emp.face_descriptor_json
            })
        return data

    @http.route('/hr_attendance/face_check', type='http', auth='public', methods=['POST'], csrf=False)
    def face_check(self):
        try:
            data = json.loads(request.httprequest.data.decode('utf-8'))
        except Exception:
            return request.make_json_response({
                'success': False,
                'message': 'Invalid JSON body'
            })

        employee_id = data.get('employee_id')
        image_base64 = data.get('image')
        challenge_passed = data.get('challenge_passed')

        if not image_base64:
            return request.make_json_response({
                'success': False,
                'message': 'Missing image'
            })

        try:
            img_bytes = base64.b64decode(image_base64.split(',')[1])
            np_img = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
        except Exception:
            return request.make_json_response({
                'success': False,
                'message': 'Invalid image data'
            })

        is_challenge_passed = challenge_passed
        if not is_challenge_passed:
            return request.make_json_response({
                'success': False,
                'message': 'Challenge failed'
            })

        is_real_face = run_antispoof(frame, None)
        if not is_real_face:
            return request.make_json_response({
                'success': False,
                'message': 'Liveness check failed'
            })

        
        #ใช้ตรวจสอบ Id พนังงานว่าตรวจพบหรือไม่ เพื่อทำการ Check IN/OUT การเข้าทำงาน
        if not employee_id:
            return {'success': False, 'message': 'Missing employee information'}

        now = datetime.now()
        employee = request.env['hr.employee'].sudo().browse(int(employee_id))
        if not employee.exists():
            return {'success': False, 'message': 'Employee not found'}

        Attendance = request.env['hr.attendance'].sudo()
        
        # หา attendance ล่าสุดของวันนี้
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_attendance = Attendance.search([
            ('employee_id', '=', employee.id),
            ('check_in', '>=', today_start)
        ], order="check_in desc", limit=1)
        
        # ตรวจสอบสถานะปัจจุบัน
        if not today_attendance:
            # ยังไม่มี attendance วันนี้ -> Check In
            Attendance.create({
                'employee_id': employee.id,
                'check_in': now
            })

            return request.make_json_response({
                'success': True,
                'message': f'Good morning, {employee.name}! Check-in recorded at {now.strftime("%H:%M")}',
                'action': 'check_in',
                'verification': {
                    'challenge_passed': is_challenge_passed,
                    'liveness_passed': is_real_face,
                }
            })
                    
        elif not today_attendance.check_out:
            # มี check_in แล้วแต่ยังไม่ check_out -> Check Out
            today_attendance.write({'check_out': now})
            return request.make_json_response({
                'success': True,
                'message': f'Goodbye, {employee.name}! Check-out recorded at {now.strftime("%H:%M")}.',
                'action': 'check_out',
                'verification': {
                    'challenge_passed': is_challenge_passed,
                    'liveness_passed': is_real_face,
                }
            })
        
        else:
            # มี check_in และ check_out แล้ว -> ไม่อนุญาต
            return request.make_json_response({
                'success': False, 
                'message': f'{employee.name}, you have already completed attendance for today.',
                'action': 'already_completed',
                'verification': {
                    'challenge_passed': is_challenge_passed,
                    'liveness_passed': is_real_face,
                }
            })

    @http.route('/hr_attendance/get_employee_info', type='json', auth='public', methods=['POST'], csrf=False)
    def get_employee_info(self, **kwargs):
        employee_id = kwargs.get('employee_id')
        if not employee_id:
            return {'success': False, 'error': 'Missing employee_id'}

        employee = request.env['hr.employee'].sudo().browse(int(employee_id))
        if not employee.exists():
            return {'success': False, 'error': 'Employee not found'}

        Attendance = request.env['hr.attendance'].sudo()
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        att = Attendance.search([
            ('employee_id', '=', employee.id), 
            ('check_in', '>=', today)
        ], limit=1)

        return {
            'success': True,
            'employee': {
                'id': employee.id,
                'name': employee.name,
                'attendance': {
                    'check_in': att.check_in.strftime('%H:%M:%S') if att and att.check_in else None,
                    'check_out': att.check_out.strftime('%H:%M:%S') if att and att.check_out else None,
                    'status': 'checked_out' if att and att.check_out else ('checked_in' if att else 'not_started')
                }
            }
        }
    
