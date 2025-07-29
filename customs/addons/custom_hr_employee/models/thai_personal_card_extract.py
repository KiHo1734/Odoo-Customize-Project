import datetime
import base64
import tempfile
import unicodedata
from io import BytesIO
from odoo import models, fields, api
from odoo.exceptions import UserError
from cryptography.fernet import Fernet
from PIL import Image
from typhoon_ocr import ocr_document
import re

class HrPersonalCardExtract(models.Model):
    _inherit = 'hr.employee'

    id_card_image = fields.Binary(string='ID Card Image')
    id_card_image_filename = fields.Char(string="ID Card Filename")

    religion = fields.Char(string="Religion")
    identification_id_encrypted = fields.Char(store=True)

    identification_id = fields.Char(
        string="ID Number",
        compute="_compute_identification_id",
        inverse="_inverse_identification_id",
        store=False,
    )


    def read(self, fields=None, load='_classic_read'):
        res = super().read(fields, load)
        if not fields or 'identification_id' in fields:
            for record, val in zip(self, res):
                if record.identification_id_encrypted:
                    try:
                        fernet = record._get_or_create_fernet()
                        val['identification_id'] = fernet.decrypt(record.identification_id_encrypted.encode()).decode()
                    except Exception:
                        val['identification_id'] = False
        return res

    def _get_or_create_fernet(self):
        Param = self.env['ir.config_parameter'].sudo()
        key = Param.get_param('personal_card_fernet_key')
        if not key:
            key = Fernet.generate_key().decode()
            Param.set_param('personal_card_fernet_key', key)
        return Fernet(key.encode())

    @api.depends('identification_id_encrypted')
    def _compute_identification_id(self):
        for rec in self:
            if rec.identification_id_encrypted:
                try:
                    fernet = rec._get_or_create_fernet()
                    rec.identification_id = fernet.decrypt(rec.identification_id_encrypted.encode()).decode()
                except:
                    rec.identification_id = False
            else:
                rec.identification_id = False

    def _inverse_identification_id(self):
        for rec in self:
            if rec.identification_id:
                fernet = rec._get_or_create_fernet()
                rec.identification_id_encrypted = fernet.encrypt(rec.identification_id.encode()).decode()
            else:
                rec.identification_id_encrypted = False

    def extract_info_from_image(self):
        for rec in self:
            rec._extract_from_image_single()

    @staticmethod
    def thai_date_to_date(date_str):
        thai_months = {
            'ม.ค': '01', 'ก.พ': '02', 'มี.ค': '03', 'เม.ย': '04',
            'พ.ค': '05', 'มิ.ย': '06', 'ก.ค': '07', 'ส.ค': '08',
            'ก.ย': '09', 'ต.ค': '10', 'พ.ย': '11', 'ธ.ค': '12'
        }

        try:
            date_str = unicodedata.normalize("NFKC", date_str).replace('\u00a0', ' ').strip()
            parts = date_str.split()
            if len(parts) != 3:
                return None

            day = parts[0]
            raw_month = parts[1].replace(".", "")
            year = int(parts[2]) - 543

            month = next((v for k, v in thai_months.items() if raw_month in k.replace(".", "")), None)
            if not month:
                return None

            return datetime.datetime.strptime(f"{day}-{month}-{year}", "%d-%m-%Y").date()
        except:
            return None

    def _extract_from_image_single(self):
        if not self.id_card_image:
            raise UserError("กรุณาอัปโหลดรูปบัตรประชาชนก่อน")

        image_data = base64.b64decode(self.id_card_image)
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            with Image.open(BytesIO(image_data)) as img:
                img = img.convert("RGB")
                img.thumbnail((1000, 1000))
                img.save(f, format="JPEG")
            temp_path = f.name

        try:
            markdown = ocr_document(
                temp_path,
                base_url="http://localhost:11434/v1",
                api_key="sk-Mt83qPXTLlk25KJHBhpaBYm35ghgqsLGU0CetBZy3h7RRhGG",
                model="scb10x/typhoon-ocr-7b"
            )

            # ✅ แปลง markdown เป็น dict
            def parse_markdown(text):
                data = {}
                for line in text.strip().splitlines():
                    if line.startswith("#"):
                        continue
                    match = re.match(r"-\s*(.+?):\s*(.+)", line)
                    if match:
                        key, value = match.groups()
                        data[key.strip()] = value.strip()
                return data

            result = parse_markdown(markdown)

            id_number = result.get("เลขประจำตัวประชาชน") or result.get("รหัสประจำตัวประชาชน")
            if not id_number:
                raise UserError("ไม่พบเลขประจำตัวประชาชนในภาพ")
            self.identification_id_encrypted = self._get_or_create_fernet().encrypt(id_number.encode()).decode()

            self.name = result.get("Name")
            if not self.name:
                self.name = result.get("ชื่อตัวและชื่อสกุล", "")

            self.religion = result.get("ศาสนา", "")

            birth_raw = result.get("เกิดวันที่") or result.get("Date of Birth")
            if birth_raw:
                birth_date = self.thai_date_to_date(birth_raw)
                if birth_date:
                    self.birthday = birth_date

            self.private_street = result.get("ที่อยู่", "")

            country = self.env.ref('base.th')
            self.country_id = country
            self.private_country_id = country

        except Exception as e:
            raise UserError(f"อ่านข้อมูลจากภาพไม่สำเร็จ: {e}")
