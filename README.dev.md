# Odoo Customize Project
โปรเจกต์นี้สำหรับปรับแต่ง Odoo ตามความต้องการของเรา

## การตั้งค่าไฟล์ config (odoo.conf)
ไฟล์ `odoo.conf` เป็นไฟล์ตั้งค่าโปรเจกต์ Odoo ที่มีข้อมูลสำคัญ เช่น การเชื่อมต่อฐานข้อมูล รหัสผ่านต่าง ๆ

เพื่อความปลอดภัย ไฟล์ `odoo.conf` จะ **ไม่ถูกเก็บใน Git** (อยู่ใน `.gitignore`)  
แต่เราจะเก็บไฟล์ตัวอย่างชื่อ `odoo.conf.example` แทน

### วิธีใช้งาน
1. คัดลอกไฟล์ `odoo.conf.example` เป็น `odoo.conf`

   ```bash
   cp odoo.conf.example odoo.

   แล้วทำการแก้ไขข้อมูลที่ต้องใช้ เช่น ข้อมูล Database (odoo ใช้ PostgreSQL เป็นหลัก)
   
2. การติดตั้ง Enviroment เพื่อใช้งาน Odoo ใช้คำสั่ง

   ```bash
   py -m venv venv

   เพื่อติดตั้ง venv สำหรับจัดการ Python libraries หรือ Packages ต่าง ๆ
   
3. ใช้คำสั่ง venv\Scripts\activate เพื่อใช้งาน venv environtment

4. ใช้คำสั่ง pip install -r requirements.txt เพื่อติดตัง Dependencies ที่จำเป็นทั้งหมดจาก requirements.txt
