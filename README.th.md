   # Odoo Customize Project
   โปรเจกต์นี้สำหรับปรับแต่ง Odoo ตามความต้องการของเรา

   ## การตั้งค่าไฟล์ config (odoo.conf)
   ไฟล์ `odoo.conf` เป็นไฟล์ตั้งค่าโปรเจกต์ Odoo ที่มีข้อมูลสำคัญ เช่น การเชื่อมต่อฐานข้อมูล รหัสผ่านต่าง ๆ

   เพื่อความปลอดภัย ไฟล์ `odoo.conf` จะ **ไม่ถูกเก็บใน Git** (อยู่ใน `.gitignore`)  
   แต่เราจะเก็บไฟล์ตัวอย่างชื่อ `odoo.conf.example` แทน

   ### วิธีการติดตั้งหลัง Pull Git มาใช้
   1. สร้างไฟล์ odoo.conf 

      ```bash
      python odoo-bin -c odoo.conf --save
      ```

      --save จะสร้าง odoo.conf อัตโนมัติ หากยังไม่มี [ตัวอย่างไฟล์ odoo.conf](odoo.conf.example)

      แล้วทำการแก้ไขข้อมูลที่ต้องใช้ เช่น db_user และ db_password (odoo ใช้ PostgreSQL เป็นหลัก)

      ```ini
      [options]
      addons_path = addons,customs/addons
      admin_passwd = admin
      db_host = localhost
      db_port = 5432
      db_user = myUser    <----- แก้ db_user
      db_password = 1234  <----- แก้ db_user
      logfile = odoo.log
      xmlrpc_port = 8069
      ```
      ถ้าไม่เข้าใจไปดู Slide นี้เป็นแนวทางได้คร่าว ๆ [อันนี้เป็น Slide ที่ผมทำตอนเริ่มศึกษา odoo ช่วงแรก ๆ](https://www.canva.com/design/DAGmvvM3Wvw/CSePN35W6QotP6aFMvcRjg/edit?utm_content=DAGmvvM3Wvw&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton)
      
   2. การติดตั้ง Enviroment เพื่อใช้งาน Odoo ใช้คำสั่ง

      ```bash
      py -m venv venv
      ```
      เพื่อติดตั้ง venv สำหรับจัดการ Python libraries หรือ Packages ต่าง ๆ
      
   3. ใช้คำสั่ง  `venv\Scripts\activate` เพื่อใช้งาน venv environtment

   4. ใช้คำสั่ง `pip install -r requirements.txt` เพื่อติดตัง Dependencies ที่จำเป็นทั้งหมดจาก requirements.txt ลงใน venv environtment

   ## คำสั่งเพิ่มเติม (**ทุกครั้งที่ใช้คำสั่งใด ๆ ก็ตามแนะนำให้ใช้บน venv environtment**)
   ### อัปเดตโมดูล (ใช้ตอนสร้างหรืออัปเดต Custom Modules)
   ```bash
   python odoo-bin -u <ชื่อโมดูลที่สร้าง> -d <ชื่อฐานข้อมูล>
   ```
   ## โครงสร้างในการสร้างไฟล์ Custom modules
      customs/                               ← โฟลเดอร์หลักสำหรับเก็บ custom modules ทั้งหมด 
         └── addons/                         ← โฟลเดอร์สำหรับใส่ custom modules แต่ละตัว
            └── custom_hr_employee/          ← โมดูลสำหรับปรับแต่ง hr.employee (modules ที่เราสร้างเพิ่ม) ✅
               ├── __init__.py               ← บอก Python ว่าโฟลเดอร์นี้เป็น Package ✅
               ├── __manifest__.py           ← ไฟล์กำหนด metadata ของโมดูล เช่น version, depends, assets, data ✅
               ├── models/                   ← โฟลเดอร์เก็บ Python model logic ⚠️ จำเป็นถ้าเพิ่ม field/logic
               │   ├── __init__.py           ← บอก Python ให้โหลด hr_employee.py (import models ทั้งหมด) ⚠️ จำเป็นถ้ามี model
               │   └── hr_employee.py        ← ไฟล์ Python สำหรับเพิ่ม/สืบทอด field, method ของ hr.employee ⚠️ ถ้าเพิ่มฟิลด์/เขียน Python model
               ├── views/                    ← เก็บไฟล์ XML ที่ใช้กำหนดหน้าจอ UI (form, tree, kanban, menu ฯลฯ) ✅
               │   ├── hr_employee_view.xml  ← กำหนด form view ของ hr.employee (เช่นเพิ่ม field เงินเดือน) ✅ 
               │   └── custom_menus.xml      ← สร้างเมนูใหม่หรือลิงก์ไปยัง model ที่ปรับแต่ง ❌ สร้างเมนูเพิ่ม ถ้าต้องการ
               ├── security/                 ← ไฟล์เกี่ยวกับสิทธิ์การเข้าถึงข้อมูล ✅ จำเป็นถ้าเพิ่ม/เปลี่ยนโมเดล
               │   ├── ir.model.access.csv   ← สิทธิ์ CRUD (อ่าน/เขียน/สร้าง/ลบ) สำหรับโมเดลนี้ ✅ สิทธิ์เข้าถึง model
               │   └── security.xml          ← ใช้สร้าง rule เฉพาะกลุ่ม เช่น เห็นเฉพาะพนักงานในแผนกเดียวกัน ❌ สำหรับ rule advance เช่น จำกัดข้อมูล
               ├── static/                   ← ไฟล์ frontend asset เช่น CSS/JS ❌ ใช้ปรับแต่ง UI (CSS/JS)
               │   └── src/
               │       ├── css/
               │       │   └── employee_style.css        ← ปรับแต่ง style UI backend (เช่น สี, ขนาดตัวอักษร)
               │       └── js/
               │           └── custom_script.js          ← เขียน JavaScript เพิ่ม interaction ในหน้า web
               ├── data/                                 ← ข้อมูลที่โหลดเข้าระบบเมื่อ install โมดูล (default data) ❌ ข้อมูลเริ่มต้น เช่น default employee
               │   └── default_data.xml                  ← ตัวอย่างเช่น preload พนักงาน 1 คน หรือค่าสถานะเริ่มต้น
               └── reports/                              ← ไฟล์สำหรับสร้างรายงาน PDF, XLSX, QWeb ❌ รายงาน PDF, QWeb template
                     ├── employee_report.xml             ← กำหนด action/report template
                     └── employee_report_template.xml    ← QWeb template ของรายงาน (HTML-based)
      
      ✅ = จำเป็น
      ⚠️ = ขึ้นอยู่กับว่าใช้ทำอะไร
      ❌ = ไม่จำเป็นถ้าไม่ได้ใช้ฟีเจอร์นั้น
