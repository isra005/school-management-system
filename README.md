# School Management System — نظام إدارة المدرسة

A full-stack student management system built for a nonprofit Quranic school in Algeria. Currently deployed and in active use.

## What it does ??
- Student enrollment across 6 educational categories
- Teacher and class management with scheduling
- Monthly and annual payment tracking with automated record generation
- Expulsion candidate detection (3+ unpaid months)
- Branch/room management across multiple locations
- Arabic RTL interface for non-technical staff

## Tech Stack
- **Backend:** Python, Flask
- **Database:** SQLite with normalized schema (3NF)
- **Frontend:** Jinja2 templates, HTML/CSS, vanilla JavaScript
- **Deployment:** Local network, Windows (start.bat)

## Database Schema
11 tables covering: depart, salle, category, level, class,
teacher, student, schedule, payment_rate, payment,
class_extra_teacher

## What I learned : 
- Relational database design and normalization to 3NF
- Many-to-many relationships (teachers ↔ classes)
- Flask routing, Jinja2 templating, SQLite integration
- Local network deployment for non-technical users
- Handling real edge cases: co-teaching, employment-based payment rates, soft delete vs hard delete tradeoffs
- building a inteface used by none technical indivituals 

## Setup
\`\`\`bash
pip install flask
python init_db.py
python app.py
\`\`\`
Then open http://127.0.0.1:5000