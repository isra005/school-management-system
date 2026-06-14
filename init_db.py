import sqlite3
import os

if os.path.exists('school.db'):
    os.remove('school.db')

conn = sqlite3.connect('school.db')
conn.execute("PRAGMA foreign_keys = ON")

with open('schema.sql', 'r', encoding='utf-8') as f:
    conn.executescript(f.read())

# ── Categories ───────────────────────────────────────────────────────────────
categories = [
    ('ما قبل التمدرس', 'شهريا',  0),
    ('الناشئة',        'سنويا',  1),
    ('محو الامية',     'سنويا',  0),
    ('التلقين',        'شهريا',  0),
    ('الشاطبية',       'شهريا',  0),
    ('التحفيظ',        'سنويا',  0),
    ('القراءات',       'شهريا',  0),
]

conn.executemany(
    "INSERT INTO category (name, payment_type, has_levels) VALUES (?, ?, ?)",
    categories
)



conn.executescript ( """
   
    INSERT INTO depart (name, address) VALUES ('مقر تجريبي 1', 'عنوان تجريبي 1');
    INSERT INTO depart (name, address) VALUES ('مقر تجريبي 2', 'عنوان تجريبي 2');
""")
# ── Levels for الناشئة ───────────────────────────────────────────────────────
conn.executescript("""
    INSERT INTO level (category_id, level_number, name)
    SELECT id, 1, 'المستوى 1' FROM category WHERE name = 'الناشئة';
    INSERT INTO level (category_id, level_number, name)
    SELECT id, 2, 'المستوى 2' FROM category WHERE name = 'الناشئة';
    INSERT INTO level (category_id, level_number, name)
    SELECT id, 3, 'المستوى 3' FROM category WHERE name = 'الناشئة';
""")



# ── Payment rates ─────────────────────────────────────────────────────────────
# قاصر فقط: ما قبل التمدرس، الناشئة، التلقين
# عاطل/موظف فقط: محو الامية، الشاطبية، التحفيظ، القراءات
rates = [
    # 1 - ما قبل التمدرس : شهريا — قاصر فقط 100
    ('ما قبل التمدرس', 'قاصر', 100),

    # 2 - الناشئة : سنويا — قاصر فقط 50
    ('الناشئة', 'قاصر', 50),

    # 3 - محو الامية : سنويا — عاطل 50 / موظف 100
    ('محو الامية', 'عاطل',  50),
    ('محو الامية', 'موظف', 100),

    # 4 - التلقين : شهريا — قاصر فقط 100
    ('التلقين', 'قاصر', 100),

    # 5 - الشاطبية : شهريا — عاطل 50 / موظف 50
    ('الشاطبية', 'عاطل', 50),
    ('الشاطبية', 'موظف', 50),

    # 6 - التحفيظ : سنويا — عاطل 50 / موظف 100
    ('التحفيظ', 'عاطل',  50),
    ('التحفيظ', 'موظف', 100),

    # 7 - القراءات : شهريا — عاطل 50 / موظف 50
    ('القراءات', 'عاطل', 50),
    ('القراءات', 'موظف', 50),
]

conn.executemany("""
    INSERT INTO payment_rate (category_id, employment_status, amount)
    SELECT c.id, ?, ? FROM category c WHERE c.name = ?
""", [(r[1], r[2], r[0]) for r in rates])

conn.commit()
conn.close()
print("Done.")
