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

    # C. Skill Level Display (สำหรับแสดงชื่อระดับ)
    skill_level_name = fields.Char(
        string="Skill Level Name",
        related="skill_level_id.name",
        readonly=True,
        store=True,
    )

    # D. Skill Progress Percentage (คำนวณแบบง่ายๆ)
    skill_progress_percentage = fields.Float(
        string="Skill Progress (%)",
        compute="_compute_skill_progress",
        store=True,
        readonly=True,
    )

    @api.depends("employee_id.department_id")
    def _compute_leaf_department_name(self):
        for rec in self:
            dept = rec.employee_department_id
            print(f"[DEBUG] Emp: {rec.employee_id.name}, Dept: {dept and dept.name}, Full: {dept and dept.complete_name}")
            if dept:
                full_name = dept.complete_name or dept.name
                if '/' in full_name:
                    rec.leaf_department_name = full_name.split('/')[-1].strip()
                else:
                    rec.leaf_department_name = full_name.strip()
            else:
                rec.leaf_department_name = False

    @api.depends("skill_level_id")
    def _compute_skill_progress(self):
        """คำนวณความก้าวหน้าของทักษะแบบง่ายๆ"""
        for rec in self:
            if rec.skill_level_id:
                level_name = rec.skill_level_id.name.lower() if rec.skill_level_id.name else ""
                if 'beginner' in level_name or 'basic' in level_name or '1' in level_name:
                    rec.skill_progress_percentage = 20
                elif 'intermediate' in level_name or 'medium' in level_name or '2' in level_name:
                    rec.skill_progress_percentage = 40
                elif 'advanced' in level_name or 'good' in level_name or '3' in level_name:
                    rec.skill_progress_percentage = 60
                elif 'expert' in level_name or 'very good' in level_name or '4' in level_name:
                    rec.skill_progress_percentage = 80
                elif 'master' in level_name or 'excellent' in level_name or '5' in level_name:
                    rec.skill_progress_percentage = 100
                else:
                    rec.skill_progress_percentage = min((rec.skill_level_id.id % 5 + 1) * 20, 100)
            else:
                rec.skill_progress_percentage = 0

    # สำหรับเรียกใช้บังคับคำนวณใหม่ (เช่นจาก cron หรือ dev action)
    def recompute_departments(self):
        for rec in self:
            rec._compute_leaf_department_name()
            rec._compute_skill_progress()
        return True

    def get_department_hierarchy(self):
        """ดึงลำดับชั้นแผนกทั้งหมด"""
        self.ensure_one()
        if not self.employee_department_id:
            return []
        hierarchy = []
        dept = self.employee_department_id
        while dept:
            hierarchy.insert(0, dept.name)
            dept = dept.parent_id
        return hierarchy

    def get_department_path(self, separator=" > "):
        """ดึง path ของแผนกในรูปแบบ string"""
        hierarchy = self.get_department_hierarchy()
        return separator.join(hierarchy) if hierarchy else ""

    @api.model
    def _update_department_fields(self):
        """Cron job method to update all department-related fields"""
        all_skills = self.search([])
        all_skills.recompute_departments()
        return True

        
