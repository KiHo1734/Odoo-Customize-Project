from odoo import models, fields, api, _
from datetime import date, timedelta, datetime, time
from dateutil.relativedelta import relativedelta
import calendar as py_calendar

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    salary = fields.Monetary(string='Salary', currency_field='currency_id')
    start_date = fields.Date(string='Start Date')
    retirement_date = fields.Date(string='Retirement Date')
    position_change_date = fields.Date(string='Position Change Date')
    end_date = fields.Date(string='End Date') 
    
    is_special_position = fields.Boolean(string="Specialized Position")
    special_position_allowance = fields.Monetary(
        string="Special Allowance",
        currency_field="currency_id",
        default=5000.0
    )

    employee_skill_ids = fields.One2many(
        'hr.employee.skill',
        'employee_id',
        string='Skills'
    )

    total_salary = fields.Monetary(string="Total Salary", compute="_compute_total_salary", currency_field="currency_id", store=False)

    @api.depends(
        'salary',
        'is_special_position',
        'special_position_allowance',
        'employee_skill_ids.skill_certification_allowance',
    )
    def _compute_total_salary(self):
        for rec in self:
            base = rec.salary or 0.0
            special = rec.special_position_allowance if rec.is_special_position else 0.0
            skill_total = sum(rec.employee_skill_ids.mapped('skill_certification_allowance') or [])
            rec.total_salary = base + special + skill_total

    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        default=lambda self: self.env.company.currency_id
    )

    position_history_ids = fields.One2many(
        'hr.position.history',  
        'employee_id',          
        string="Position History",
        order='start_date desc, id desc'
    )

    current_position_history_id = fields.Many2one(
        'hr.position.history',
        compute='_compute_current_position',
        store=True
    )

    # จัดการเกี่ยวกับประวัติตำแหน่งของพนักงาน
    @api.depends('position_history_ids.start_date')
    def _compute_current_position(self):
        for rec in self:
            rec.current_position_history_id = rec.position_history_ids[:1] and rec.position_history_ids[0] or False

    @api.onchange('job_id', 'department_id', 'position_change_date')
    def _onchange_position_info(self):
        for rec in self:
            today = fields.Date.today()
            start = rec.position_change_date or today

            saved_recs = rec.position_history_ids.filtered(lambda r: r.id)
            new_recs = rec.position_history_ids.filtered(lambda r: not r.id)

            # ตรวจสอบว่ามี record ใหม่ซ้ำอยู่แล้วหรือไม่
            already_exists = any(
                r.job_id == rec.job_id and
                r.department_id == rec.department_id and
                r.start_date == start
                for r in new_recs
            )

            if not already_exists and (rec.job_id or rec.department_id):
                new_entry = self.env['hr.position.history'].new({
                    'job_id': rec.job_id.id,
                    'department_id': rec.department_id.id,
                    'start_date': start,
                    'end_date': rec.retirement_date or False,
                })

                # รวมทั้งหมดแล้วจัดเรียงจากใหม่ไปเก่า
                all_recs = new_entry + saved_recs + new_recs
                rec.position_history_ids = all_recs.sorted(
                    key=lambda r: r.start_date or today, reverse=True
                )
            else:
                rec.position_history_ids = rec.position_history_ids.sorted(
                    key=lambda r: r.start_date or today, reverse=True
                )

    days_left_to_retire = fields.Char(string="เวลาที่เหลือก่อนเกษียณ", compute="_compute_retirement_delta", store=False)

    @api.depends('retirement_date')
    def _compute_retirement_delta(self):
        today = date.today()
        for rec in self:
            if rec.retirement_date:
                diff = relativedelta(rec.retirement_date, today)
                rec.days_left_to_retire = f"{diff.years} ปี {diff.months} เดือน {diff.days} วัน"
            else:
                rec.days_left_to_retire = "-"
    
    # ส่วนที่ใช้สำหรับจัด Suffix Id ของพนักงาน
    employee_code = fields.Char(string="Employee Code", readonly=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('employee_code'):
                vals['employee_code'] = self.env['ir.sequence'].next_by_code('hr.employee.code')
        return super().create(vals_list)
    
    # Selection สำหรับเลือกวิธีการเดินทาง
    travel_method = fields.Selection([
        ('private_car', _('รถยนตร์ส่วนตัว')),
        ('motorbike', _('รถจักรยานยนตร์')),
        ('public_transport', _('รถสาธารณะ')),
        ('bicycle', _('จักรยาน')),
        ('walk', _('เดินเท้า')),
    ], string=_('Travel Method'), default='private_car')

    show_private_car_plate = fields.Boolean(
        string="Show Private Car Plate",
        compute="_compute_show_private_car_plate"
    )

    @api.depends('travel_method')
    def _compute_show_private_car_plate(self):
        for rec in self:
            rec.show_private_car_plate = (rec.travel_method == 'private_car')

    # วันขาด และ วันลา จาก custom_attedances module
    total_leave_days = fields.Integer(
        string="Total Leave Days",
        compute="_compute_leave_days",
    )
    total_absence_days = fields.Integer(
        string="Total Absence Days",
        compute="_compute_absence_days",
    )
        
    # ส่วน HrEmployee
    def _compute_leave_days(self, start_date=None, end_date=None):
        for employee in self:
            # ถ้าไม่ส่ง start/end ให้ใช้ค่า default
            start_date = start_date or employee.start_date
            end_date = end_date or date.today()
            if not start_date:
                employee.total_leave_days = 0
                continue

            leaves = self.env['hr.leave'].search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'validate'),
                ('request_date_from', '<=', end_date),
                ('request_date_to', '>=', start_date),
            ])
            employee.total_leave_days = sum(l.number_of_days for l in leaves)

    def _compute_absence_days(self, start_date=None, end_date=None):
        for employee in self:
            start_date = start_date or employee.start_date
            end_date = end_date or date.today()
            if not start_date or not employee.resource_calendar_id or not employee.resource_id:
                employee.total_absence_days = 0
                continue

            calendar = employee.resource_calendar_id
            start_dt = fields.Datetime.context_timestamp(self, datetime.combine(start_date, time.min))
            end_dt = fields.Datetime.context_timestamp(self, datetime.combine(end_date, time.max))

            intervals_map = calendar._work_intervals_batch(start_dt, end_dt, resources=employee.resource_id)
            work_intervals = intervals_map.get(employee.resource_id.id, [])

            work_days = len(set(interval[0].date() for interval in work_intervals))

            # วันลา
            leaves = self.env['hr.leave'].search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'validate'),
                ('request_date_from', '<=', end_date),
                ('request_date_to', '>=', start_date),
            ])
            leave_days = sum(l.number_of_days for l in leaves)

            # วันมาทำงานจริง
            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', start_dt),
                ('check_in', '<=', end_dt)
            ])
            present_days = len(set(att.check_in.date() for att in attendances))

            absence_days = work_days - leave_days - present_days
            employee.total_absence_days = max(absence_days, 0)

    @api.model
    def cron_update_leave_absence(self):
        """Cron job daily to update leave and absence counts"""
        employees = self.search([])
        for emp in employees:
            emp._compute_leave_days()
            emp._compute_absence_days()