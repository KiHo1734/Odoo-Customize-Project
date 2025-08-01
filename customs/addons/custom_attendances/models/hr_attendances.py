from odoo import models, fields, api
from datetime import datetime, time

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    is_late = fields.Boolean(string="Late Check-in", compute="_compute_attendance_flags", store=True)
    is_absent = fields.Boolean(string="Absent", compute="_compute_attendance_flags", store=True)
    left_early = fields.Boolean(string="Left Early", compute="_compute_attendance_flags", store=True)
    is_on_leave = fields.Boolean(string="On Leave", compute="_compute_attendance_flags", store=True)

    @api.depends('check_in', 'check_out', 'employee_id')
    def _compute_attendance_flags(self):
        for rec in self:
            rec.is_late = False
            rec.left_early = False
            rec.is_absent = False
            rec.is_on_leave = False

            if not rec.check_in:
                # เช็คว่าพนักงานลาหรือไม่
                leave = rec.env['hr.leave'].search([
                    ('employee_id', '=', rec.employee_id.id),
                    ('state', '=', 'validate'),
                    ('request_date_from', '<=', fields.Date.today()),
                    ('request_date_to', '>=', fields.Date.today())
                ], limit=1)
                if leave:
                    rec.is_on_leave = True
                else:
                    rec.is_absent = True
                continue

            # เวลาทำงานจาก calendar ของพนักงาน
            calendar = rec.employee_id.resource_calendar_id
            weekday = str(rec.check_in.weekday())  # Monday = 0
            attendances = calendar.attendance_ids.filtered(lambda a: a.dayofweek == weekday and not a.display_type)

            if attendances:
                earliest = min(a.hour_from for a in attendances)
                latest = max(a.hour_to for a in attendances)
                scheduled_checkin = time(int(earliest), int((earliest % 1) * 60))
                scheduled_checkout = time(int(latest), int((latest % 1) * 60))

                actual_checkin = rec.check_in.time()
                actual_checkout = rec.check_out.time() if rec.check_out else None

                # เข้างานสาย
                rec.is_late = actual_checkin > scheduled_checkin

                # กลับก่อนเวลา
                if actual_checkout:
                    rec.left_early = actual_checkout < scheduled_checkout
