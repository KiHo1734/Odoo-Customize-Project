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
        action = kwargs.get('action')

        if not employee_id or not action:
            return {'success': False, 'error': 'Missing employee_id or action'}

        now = datetime.now()
        params = request.env['ir.config_parameter'].sudo()
        work_start_hour = float(params.get_param('hr_attendance.work_start', 8.0))
        work_end_hour = float(params.get_param('hr_attendance.work_end', 17.0))

        work_start = time(int(work_start_hour), int((work_start_hour % 1) * 60))
        work_end = time(int(work_end_hour), int((work_end_hour % 1) * 60))

        employee = request.env['hr.employee'].sudo().browse(int(employee_id))
        if not employee.exists():
            return {'success': False, 'error': 'Employee not found'}

        Attendance = request.env['hr.attendance'].sudo()

        if action == 'check_in':
            # หา attendance ค้าง (ยังไม่ check-out)
            last_attendance = Attendance.search([
                ('employee_id', '=', employee.id),
                ('check_out', '=', False)
            ], order="check_in desc", limit=1)

            if last_attendance:
                last_checkin_date = last_attendance.check_in.date()
                today = now.date()
                if last_checkin_date < today:
                    # ปิด attendance ของวันก่อนหน้าอัตโนมัติ
                    last_attendance.write({'check_out': datetime.combine(last_checkin_date, time(23, 59, 59))})

            # ตรวจสอบว่ามี check-in ของวันปัจจุบันหรือยัง
            existing_today = Attendance.search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', now.replace(hour=0, minute=0, second=0, microsecond=0)),
                ('check_out', '=', False)
            ], limit=1)

            if not existing_today:
                Attendance.create({'employee_id': employee.id, 'check_in': now})

        elif action == 'check_out':
            if now.time() < work_end:
                return {'success': False, 'error': f'Check-out allowed only after {work_end.strftime("%H:%M")}'}

            attendance = Attendance.search([
                ('employee_id', '=', employee.id),
                ('check_out', '=', False)
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
