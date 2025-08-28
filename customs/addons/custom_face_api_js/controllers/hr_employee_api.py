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
        work_start = time(8, 0)
        work_end = time(17, 0)

        employee = request.env['hr.employee'].sudo().browse(int(employee_id))
        if not employee.exists():
            return {'success': False, 'error': 'Employee not found'}

        Attendance = request.env['hr.attendance'].sudo()

        if action == 'check_in':
            if now.time() >= work_start:
                return {'success': False, 'error': 'Check-in allowed after 08:00'}
            existing = Attendance.search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', now.replace(hour=0, minute=0, second=0, microsecond=0)),
                ('check_out', '=', False)
            ], limit=1)
            if not existing:
                Attendance.create({'employee_id': employee.id, 'check_in': now})

        elif action >= 'check_out':
            # เช็คเอาต์ได้หลัง 17:00
            if now.time() < work_end:
                return {'success': False, 'error': 'Check-out allowed only after 17:00'}
            attendance = Attendance.search([
                ('employee_id','=', employee.id),
                ('check_out','=', False)
            ], limit=1)
            if attendance:
                attendance.write({'check_out': now})

        return {'success': True}
