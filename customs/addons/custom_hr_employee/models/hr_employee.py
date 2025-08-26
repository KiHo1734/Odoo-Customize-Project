from datetime import date
from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from datetime import timedelta

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
                rec.days_left_to_retire = f"{diff.years} ปี {diff.months} เดือน"
            else:
                rec.days_left_to_retire = "-"

    # วันขาด และ วันลา จาก custom_attedances module
    # absent_days = fields.Integer(string="Absent Days", compute="_compute_attendance_stats", store=True)
    # leave_days = fields.Integer(string="Leave Days", compute="_compute_attendance_stats", store=True)
    
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