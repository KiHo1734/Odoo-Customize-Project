from odoo import api, fields, models

class EmployeeSkill(models.Model):
    _inherit = 'hr.employee.skill'

    # A. แผนกตรงของพนักงาน
    employee_department_id = fields.Many2one(
        related="employee_id.department_id",
        string="Employee Department",
        store=True,
        readonly=True,
    )

    # B2. Leaf Department Name (แยกชื่อส่วนท้าย)
    leaf_department_name = fields.Char(
        string="Leaf Department Name",
        compute="_compute_leaf_department_name",
        store=True,
        readonly=True,
    )

    # (C) Root Department – ถ้าต้องการ
    root_department_id = fields.Many2one(
        "hr.department",
        string="Root Department",
        compute="_compute_root_department",
        store=True,
        readonly=True,
    )

    @api.model
    def create(self, vals):
        """เมื่อสร้างใหม่ ให้ compute ทันที"""
        result = super().create(vals)
        # ไม่ต้อง call _compute_leaf_department() เพราะไม่มี method นี้
        result._compute_leaf_department_name()
        result._compute_root_department()
        return result

    def recompute_departments(self):
        """Method สำหรับบังคับ recompute ข้อมูล"""
        for rec in self:
            rec._compute_leaf_department_name()
            rec._compute_root_department()
        return True

    @api.depends("employee_department_id", "employee_department_id.name")
    def _compute_leaf_department_name(self):
        for rec in self:
            if rec.employee_department_id:
                # ใช้ชื่อแผนกที่พนักงานสังกัดโดยตรง
                rec.leaf_department_name = rec.employee_department_id.name
            else:
                rec.leaf_department_name = False

    @api.depends("employee_id.department_id")
    def _compute_root_department(self):
        for rec in self:
            dept = rec.employee_id.department_id
            if dept:
                # หา root department โดยไล่ขึ้นไปจนถึงระดับบนสุด
                while dept.parent_id:
                    dept = dept.parent_id
                rec.root_department_id = dept
            else:
                rec.root_department_id = False