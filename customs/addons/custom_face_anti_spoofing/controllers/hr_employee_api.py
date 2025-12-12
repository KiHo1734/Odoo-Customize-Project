from odoo import http
from odoo.http import request
from datetime import datetime, time, timedelta

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

    @http.route('/hr_attendance/face_check', type='json', auth='public', methods=['POST'], csrf=False)
    def face_check(self, **kwargs):
        employee_id = kwargs.get('employee_id')
        
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
            return {
                'success': True, 
                'message': f'Good morning, {employee.name}! Check-in recorded at {now.strftime("%H:%M")}',
                'action': 'check_in'
            }
        
        elif not today_attendance.check_out:
            # มี check_in แล้วแต่ยังไม่ check_out -> Check Out
            
            # คำนวณระยะเวลาทำงาน
            work_duration = now - today_attendance.check_in
            hours_worked = work_duration.total_seconds() / 3600
            
            today_attendance.write({'check_out': now})
            return {
                'success': True, 
                'message': f'Goodbye, {employee.name}! Check-out recorded at {now.strftime("%H:%M")}. Worked {hours_worked:.1f} hours.',
                'action': 'check_out'
            }
        
        else:
            # มี check_in และ check_out แล้ว -> ไม่อนุญาต
            return {
                'success': False, 
                'message': f'{employee.name}, you have already completed attendance for today.',
                'action': 'already_completed'
            }

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