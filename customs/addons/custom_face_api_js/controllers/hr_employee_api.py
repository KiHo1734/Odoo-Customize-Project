from odoo import http
from odoo.http import request
from datetime import datetime, time

class HREmployeeAPI(http.Controller):
    @http.route('/hr_employee/get_descriptors', type='json', auth='public', methods=['POST'])
    def get_descriptors(self):
        employees = request.env['hr.employee'].sudo().search([('face_descriptor_json','!=',False)])
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
        action = kwargs.get('action')

        if not employee_id or not action:
            return {'success': False, 'error': 'Missing employee_id or action'}

        now = datetime.now()
        # ดึงค่า parameter จาก system
        params = request.env['ir.config_parameter'].sudo()
        work_start_hour = float(params.get_param('hr_attendance.work_start', 8.0))
        work_end_hour = float(params.get_param('hr_attendance.work_end', 17.0))

        # แปลง float เป็นเวลา
        work_start = time(int(work_start_hour), int((work_start_hour % 1) * 60))
        work_end = time(int(work_end_hour), int((work_end_hour % 1) * 60))

        employee = request.env['hr.employee'].sudo().browse(int(employee_id))
        if not employee.exists():
            return {'success': False, 'error': 'Employee not found'}

        Attendance = request.env['hr.attendance'].sudo()

        if action == 'check_in':
            if now.time() == work_start:
                return {'success': False, 'error': f'Check-in allowed after {work_start.strftime("%H:%M")}'}
            existing = Attendance.search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', now.replace(hour=0, minute=0, second=0, microsecond=0)),
                ('check_out', '=', False)
            ], limit=1)
            if not existing:
                Attendance.create({'employee_id': employee.id, 'check_in': now})

        elif action == 'check_out':
            # เช็คเอาต์ได้หลัง 17:00
            if now.time() >= work_end:
                return {'success': False, 'error': f'Check-out allowed only after {work_end.strftime("%H:%M")}'}
            attendance = Attendance.search([
                ('employee_id','=', employee.id),
                ('check_out','=', False)
            ], limit=1)
            if attendance:
                attendance.write({'check_out': now})

        return {'success': True}

    @http.route('/hr_attendance/get_work_hours', type='json', auth='public', methods=['POST'])
    def get_work_hours(self):
        params = request.env['ir.config_parameter'].sudo()
        work_start_hour = float(params.get_param('hr_attendance.work_start', 8.0))
        work_end_hour = float(params.get_param('hr_attendance.work_end', 17.0))
        return {'work_start': work_start_hour, 'work_end': work_end_hour}

