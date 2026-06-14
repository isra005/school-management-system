import sqlite3
from flask import Flask, render_template, request, redirect, url_for, g

app = Flask(__name__)

# --- Predefined lists (used to populate dropdowns in forms) ---
categories = ['ما قبل التمدرس' , 'الناشئة' , 'محو الامية' ,'التلقين' , 'الشاطبية', 'التحفيظ','القراءات' ] # قراءات = شاطبية they take the same features in every thing but different categories so different id's 
#depart_name = ['مقر علي موسى','مقر رامول','مقر بولكاوك','مقر حمزاوي','مقر قدوس','مقر بيرة','مقر شخار','مقر يسعد','مقر مؤمن','مقر لولبيت','مقر بوزطوطة','المقر الرئيسي','مقر طالب','مقر بوغرارة' ,'مقر فاخت','مقر طاڨيڨ','مقر جراب','مقر بويديرة']
#depart_address = ['مرباع','توسان','طبت الرفيس','البياضة','الحامورة','شارع قارة','شارع الساسي','شارع الفيلق']
level_name = ['المستوى 1' , 'المستوى 2' ,'المستوى 3']
 # so they don't enter something like , done , or yes or whatever 
room_number=['القاعة 1' , 'القاعة 2' ,'القاعة 3' ,'القاعة 4' ,'القاعة 5' , 'القاعة 6' ,'القاعة 7','القاعة 8']
# class_name = ['المجموعة 4','المجموعة 3','المجموعة 2','المجموعة 1' , 'المجموعة 5','المجموعة 6','المجموعة 8','المجموعة 7' , 'المجموعة 9','المجموعة 10','المجموعة 12','المجموعة 11' , 'مجموعة 13' , 'مجموعة14' , 'مجموعة 15','مجموعة 16' ,'مجموعة 17' , 'مجموعة 18']


EMPLOYMENT_STATUS = ['قاصر', 'موظف', 'عاطل']
PAYMENT_TYPE = ['شهريا', 'سنويا']
PAID_STATUS = [0, 1]
IS_ACTIVE = [0, 1]
MONTHS = list(range(1, 13))
DAYS_OF_WEEK = ['السبت', 'الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة']
ACADEMIC_YEARS = [ '2026-2027', '2027-2028']


# --- database connection---#
def get_db():

    if "db" not in g:
        g.db = sqlite3.connect("school.db")
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

# closing the database automaticly after each request 
app.teardown_appcontext(close_db)

# --- Home page --- #

@app.route("/")
def home():
    return render_template("home.html")

####  ==== Feature 1 : Students  ====  ####

# Route: display all active students (SELECT + render table in HTML)
@app.route("/students")
def students() :
    db = get_db()
    all_students = db.execute("""
        SELECT s.id, s.first_name, s.last_name,
               s.parent_name, s.parent_phone,
               t.first_name || ' ' || t.last_name || ' - مجموعة ' || c.group_number AS class_name, cat.name AS category_name
        FROM student s 
        JOIN class c ON s.class_id = c.id
        JOIN teacher t ON c.teacher_id = t.id                      
        JOIN category cat ON c.category_id = cat.id
        WHERE s.is_active = 1
        ORDER BY s.last_name          
                              """ ).fetchall()
    return render_template("students.html" , students = all_students)


#  Route: search student by name or class
@app.route("/students/search")
def search_student():
    db = get_db()

    name = request.args.get("name", "").strip()
    category_id = request.args.get("category_id", "").strip()
    class_id = request.args.get("class_id", "").strip()
    query = """
        SELECT s.id, s.first_name, s.last_name,
               s.parent_name, s.parent_phone,
               t.first_name || ' ' || t.last_name || ' - مجموعة ' || c.group_number AS class_name, cat.name AS category_name
        FROM student s
        JOIN class c ON s.class_id = c.id
        JOIN teacher t ON c.teacher_id = t.id    
        JOIN category cat ON c.category_id = cat.id
        WHERE s.is_active = 1
    """
    params = []  # we collect the values separately for safety (prevents SQL injection)
    if name:
        query += " AND (s.first_name LIKE ? OR s.last_name LIKE ?)"
        params.extend([f"%{name}%", f"%{name}%"])

    if category_id:
        query += " AND cat.id = ?"
        params.append(category_id)

    if class_id:
        query += " AND c.id = ?"
        params.append(class_id)

    results = db.execute(query, params).fetchall()

    # Also fetch categories and classes for the dropdown menus in the search form
    categories = db.execute("SELECT id, name FROM category").fetchall()
    classes = db.execute("""
        SELECT c.id,
               t.first_name || ' ' || t.last_name || ' - مجموعة ' || c.group_number AS name,
               c.category_id
        FROM class c
        JOIN teacher t ON c.teacher_id = t.id
         
        ORDER BY c.category_id, t.last_name, c.group_number
    """).fetchall()

    return render_template("search_students.html",
                           students=results,
                           categories=categories,
                           classes=classes,
                           selected_name=name,
                           selected_category=category_id,
                           selected_class=class_id)




           
# Route: add new student (form → validate → INSERT)
@app.route("/students/add" ,  methods=["GET", "POST"])
def  add_student() :     
    db = get_db()

    if request.method == "POST":
        # request.form reads data submitted from an HTML form
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        parent_name = request.form.get("parent_name")
        parent_phone = request.form.get("parent_phone")
        address = request.form.get("address")
        employment_status = request.form.get("employment_status")
        class_id = request.form.get("class_id")
        enrolled_date = request.form.get("enrolled_date")

        # Basic validation: if any required field is empty, send back an error
        if not all([first_name, last_name ,
                    parent_phone, class_id, enrolled_date]):
            error = "الرجاء ملء جميع الحقول الإلزامية"
            classes = db.execute("""
                 SELECT c.id,
                 c.category_id,
                 t.first_name || ' ' || t.last_name ||
                 ' - مجموعة ' || c.group_number AS class_name,
                 cat.name AS category_name
         FROM class c
         JOIN teacher t ON c.teacher_id = t.id
         JOIN category cat ON c.category_id = cat.id
          ORDER BY cat.name, t.last_name, c.group_number
""").fetchall()
            categories = db.execute("SELECT id, name FROM category").fetchall()
            return render_template("add_student.html",
                       error=error,
                       classes=classes,
                       categories=categories,
                       employment_status_options=EMPLOYMENT_STATUS)

        db.execute("""
            INSERT INTO student
                (first_name, last_name, parent_name, parent_phone,
                 address, employment_status, class_id,
                 is_active, enrolled_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
        """, (first_name, last_name, parent_name, parent_phone,
              address, employment_status, class_id, enrolled_date))
        
        db.commit()

        # After a successful INSERT, redirect to the students list
        return redirect(url_for("students"))
    classes = db.execute("""
    SELECT c.id,
           c.category_id,
           t.first_name || ' ' || t.last_name ||
           ' - مجموعة ' || c.group_number AS class_name,
           cat.name AS category_name
    FROM class c
    JOIN teacher t ON c.teacher_id = t.id
    JOIN category cat ON c.category_id = cat.id
    ORDER BY cat.name, t.last_name, c.group_number
    """).fetchall()
    categories = db.execute("SELECT id, name FROM category").fetchall()
    return render_template("add_student.html",
                       classes=classes,
                       categories=categories,
                       employment_status_options=EMPLOYMENT_STATUS)

 
# Route: edit student information (pre-filled form → UPDATE)
@app.route("/students/edit/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id): #
    db = get_db()
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        parent_name = request.form.get("parent_name")
        parent_phone = request.form.get("parent_phone")
        address = request.form.get("address")
        employment_status = request.form.get("employment_status")
        class_id = request.form.get("class_id")

        db.execute("""
            UPDATE student
            SET first_name=?, last_name=?, parent_name=?,
                parent_phone=?, address=?, employment_status=?,
                class_id=?
            WHERE id=?
        """, (first_name, last_name, parent_name, parent_phone,
              address, employment_status, class_id, student_id))
        db.commit()
        return redirect(url_for("students"))
    # GET

    student = db.execute("SELECT * FROM student WHERE id = ?", (student_id,)).fetchone()
    classes = db.execute("""
         SELECT c.id,

           t.first_name || ' ' || t.last_name ||
           ' - مجموعة ' || c.group_number AS class_name,

           cat.name AS category_name

       FROM class c
       JOIN teacher t ON c.teacher_id = t.id
       JOIN category cat ON c.category_id = cat.id
    """).fetchall()
    return render_template("edit_student.html" , student = student , classes = classes , employment_status_options = EMPLOYMENT_STATUS)


#Route: deactivate student (set is_active = 0, not DELETE)
@app.route("/students/deactivate/<int:student_id>", methods=["POST"])
def deactivate_student(student_id):
    db = get_db()
    db.execute("UPDATE student SET is_active = 0 WHERE id = ?", (student_id,))
    # The comma after student_id is critical — makes it a tuple
    # Without it Python treats (student_id) as just parentheses, not a tuple
    # SQLite receives the wrong type and the UPDATE silently does nothing
    db.commit()
    return redirect(url_for("students"))

#Route: list students with 3+ unpaid months (your expulsion query)
# Students with 3+ unpaid months — expulsion candidates
@app.route("/students/expulsion")
def expulsion_candidates():
    db = get_db()
    candidates = db.execute("""
        SELECT s.id, s.first_name, s.last_name,
               s.parent_phone, COUNT(*) AS missed_months
        FROM student s
        JOIN payment p ON p.student_id = s.id
        WHERE p.paid = 0 AND s.is_active = 1
        GROUP BY s.id
        HAVING missed_months >= 3
        ORDER BY missed_months DESC
    """).fetchall()
    return render_template("expulsion.html", candidates=candidates)

# Hard delete a student — only use when student leaves permanently
# The confirmation step is important: we don't want accidental deletions
@app.route("/students/delete/<int:student_id>", methods=["POST"])
def delete_student(student_id):
    db = get_db()
    # Delete payments first — foreign key constraint won't allow
    # deleting a student who still has payment rows referencing them
    db.execute("DELETE FROM payment WHERE student_id = ?", (student_id,))
    db.execute("DELETE FROM student WHERE id = ?", (student_id,))
    db.commit()
    return redirect(url_for("students"))




####----  FEATURE 2  : TEACHERS AND CLASSES  ----####

#Route: display all classes with their category and teacher(s)
@app.route("/classes")
def classes() :
    db = get_db()
    all_classes = db.execute("""
        SELECT
            c.id,
            c.group_number,
            c.academic_year,
            cat.name AS category_name,
            COALESCE(l.name, '') AS level_name,
            t.first_name || ' ' || t.last_name AS teacher_name,
            COUNT(s.id) AS student_count
        FROM class c
        JOIN category cat ON c.category_id = cat.id
        JOIN teacher t ON c.teacher_id = t.id
        LEFT JOIN level l ON c.level_id = l.id
        LEFT JOIN student s ON s.class_id = c.id AND s.is_active = 1
        GROUP BY c.id
        ORDER BY cat.name, t.last_name, c.group_number
    """).fetchall()

    return render_template("classes.html", classes=all_classes)


# Route: add a new class
@app.route("/classes/add", methods=["GET", "POST"])
def add_class():
    db = get_db()

    if request.method == "POST":
        category_id = request.form.get("category_id")
        level_id = request.form.get("level_id") or None
        # level_id comes as empty string if not selected → convert to None
        # so it stores as NULL in the database, not as ""
        teacher_id = request.form.get("teacher_id")
        group_number = request.form.get("group_number")
        academic_year = request.form.get("academic_year")

        if not all([category_id, teacher_id, group_number, academic_year]):
            error = "الرجاء ملء جميع الحقول الإلزامية"
            teachers = db.execute("""
            SELECT t.id, t.category_id,
            t.first_name || ' ' || t.last_name AS full_name
            FROM teacher t ORDER BY t.last_name
             """).fetchall()
            categories = db.execute("SELECT id, name FROM category").fetchall()
            levels = db.execute("SELECT id, name, category_id FROM level").fetchall()
            departs = db.execute("SELECT id, name FROM depart ORDER BY name").fetchall()
            salles = db.execute("""
                SELECT s.id, s.room_number, s.depart_id, d.name AS depart_name
                FROM salle s JOIN depart d ON s.depart_id = d.id
                ORDER BY d.name, s.room_number
            """).fetchall()
            return render_template("add_class.html",
                                   error=error,
                                   teachers=teachers,
                                   categories=categories,
                                   levels=levels,
                                   departs=departs,
                                   salles=salles,
                                   days=DAYS_OF_WEEK,
                                   academic_years=ACADEMIC_YEARS)

        db.execute("""
            INSERT INTO class
                (category_id, level_id, teacher_id, group_number, academic_year)
            VALUES (?, ?, ?, ?, ?)
        """, (category_id, level_id, teacher_id, group_number, academic_year))
        db.commit()
        return redirect(url_for("classes"))

    # GET: load dropdowns
    teachers = db.execute("""
    SELECT t.id, t.category_id,
           t.first_name || ' ' || t.last_name AS full_name
    FROM teacher t ORDER BY t.last_name
      """).fetchall()
    categories = db.execute("SELECT id, name FROM category").fetchall()
    levels = db.execute("SELECT id, name, category_id FROM level").fetchall()
    departs = db.execute("SELECT id, name FROM depart ORDER BY name").fetchall()
    salles = db.execute("""
        SELECT s.id, s.room_number, s.depart_id, d.name AS depart_name
        FROM salle s JOIN depart d ON s.depart_id = d.id
        ORDER BY d.name, s.room_number
    """).fetchall()

    return render_template("add_class.html",
                           teachers=teachers,
                           categories=categories,
                           levels=levels,
                           departs=departs,
                           salles=salles,
                           days=DAYS_OF_WEEK,
                           academic_years=ACADEMIC_YEARS)


# Route: add a teacher

@app.route("/teachers/add", methods=["GET", "POST"])
def add_teacher():
    db = get_db()

    categories = db.execute("SELECT id, name FROM category ORDER BY name").fetchall()

    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        phone = request.form.get("phone")
        specialty = request.form.get("specialty")
        category_id = request.form.get("category_id")

        if not all([first_name, last_name, category_id]):
            error = "الاسم الأول واللقب والفئة إلزامية"
            return render_template("add_teacher.html", error=error, categories=categories)

        db.execute("""
            INSERT INTO teacher (first_name, last_name, phone, specialty, category_id)
            VALUES (?, ?, ?, ?, ?)
        """, (first_name, last_name, phone, specialty, category_id))
        db.commit()
        return redirect(url_for("teachers"))

    return render_template("add_teacher.html", categories=categories)


# Display all teachers
@app.route("/teachers")
def teachers():
    db = get_db()
    all_teachers = db.execute("""
        SELECT
            t.id,
            t.first_name,
            t.last_name,
            t.phone,
            t.specialty,
            cat.name AS category_name,
            COUNT(c.id) AS class_count
        FROM teacher t
        LEFT JOIN category cat ON t.category_id = cat.id
        LEFT JOIN class c ON c.teacher_id = t.id
            AND c.academic_year = '2024-2025'
        GROUP BY t.id
        ORDER BY cat.name, t.last_name
    """).fetchall()
    categories = db.execute("SELECT id, name FROM category").fetchall()
    return render_template("teachers.html",
                           teachers=all_teachers,
                           categories=categories)


@app.route("/teachers/search")
def search_teacher():
    db = get_db()
    name = request.args.get("name", "").strip()
    category_id = request.args.get("category_id", "").strip()

    query = """
        SELECT
            t.id, t.first_name, t.last_name, t.phone, t.specialty,
            cat.name AS category_name,
            COUNT(c.id) AS class_count
        FROM teacher t
        LEFT JOIN category cat ON t.category_id = cat.id
        LEFT JOIN class c ON c.teacher_id = t.id
            AND c.academic_year = '2024-2025'
        WHERE 1=1
    """
    params = []

    if name:
        query += " AND (t.first_name LIKE ? OR t.last_name LIKE ?)"
        params.extend([f"%{name}%", f"%{name}%"])

    if category_id:
        query += " AND t.category_id = ?"
        params.append(category_id)

    query += " GROUP BY t.id ORDER BY cat.name, t.last_name"

    results = db.execute(query, params).fetchall()
    categories = db.execute("SELECT id, name FROM category").fetchall()

    return render_template("search_teachers.html",
                           teachers=results,
                           categories=categories,
                           selected_name=name,
                           selected_category=category_id)

# Assign a schedule entry to a class

# This is how you record: class X meets on Saturday at 9am in room Y
# For level 3 with multiple teachers, each teacher gets their own schedule row
@app.route("/classes/<int:class_id>/schedule/add", methods=["GET", "POST"])
def add_schedule(class_id):
    db = get_db()

    # Fetch the class so we know which teacher(s) are eligible
    this_class = db.execute("""
        SELECT c.id, c.group_number, t.id AS teacher_id,
               t.first_name || ' ' || t.last_name AS teacher_name,
               cat.name AS category_name
        FROM class c
        JOIN teacher t ON c.teacher_id = t.id
        JOIN category cat ON c.category_id = cat.id
        WHERE c.id = ?
    """, (class_id,)).fetchone()

    # Also get extra teachers for level 3 الناشئة
    extra_teachers = db.execute("""
        SELECT t.id, t.first_name || ' ' || t.last_name AS teacher_name
        FROM class_extra_teacher cet
        JOIN teacher t ON cet.teacher_id = t.id
        WHERE cet.class_id = ?
    """, (class_id,)).fetchall()

    salles = db.execute("""
        SELECT s.id, s.room_number, d.name AS depart_name
        FROM salle s
        JOIN depart d ON s.depart_id = d.id
    """).fetchall()

    if request.method == "POST":
        teacher_id = request.form.get("teacher_id")
        salle_id = request.form.get("salle_id")
        day_of_week = request.form.get("day_of_week")
        start_time = request.form.get("start_time")

        db.execute("""
            INSERT INTO schedule (class_id, teacher_id, salle_id, day_of_week, start_time)
            VALUES (?, ?, ?, ?, ?)
        """, (class_id, teacher_id, salle_id, day_of_week, start_time))
        db.commit()
        return redirect(url_for("view_class", class_id=class_id))

    return render_template("add_schedule.html",
                           this_class=this_class,
                           extra_teachers=extra_teachers,
                           salles=salles,
                           days=DAYS_OF_WEEK)


# View all students in a specific class
@app.route("/classes/<int:class_id>")
def view_class(class_id):
    db = get_db()

    # Class header info
    this_class = db.execute("""
        SELECT
            c.id, c.group_number, c.academic_year,
            cat.name AS category_name,
            COALESCE(l.name, '') AS level_name,
            t.first_name || ' ' || t.last_name AS teacher_name
        FROM class c
        JOIN category cat ON c.category_id = cat.id
        JOIN teacher t ON c.teacher_id = t.id
        LEFT JOIN level l ON c.level_id = l.id
        WHERE c.id = ?
    """, (class_id,)).fetchone()

    # All active students in this class
    students_in_class = db.execute("""
        SELECT id, first_name, last_name, parent_phone, enrolled_date
        FROM student
        WHERE class_id = ? AND is_active = 1
        ORDER BY last_name
    """, (class_id,)).fetchall()

    # Schedule for this class
    class_schedule = db.execute("""
        SELECT sch.day_of_week, sch.start_time,
               s.room_number, d.name AS depart_name,
               t.first_name || ' ' || t.last_name AS teacher_name
        FROM schedule sch
        JOIN salle s ON sch.salle_id = s.id
        JOIN depart d ON s.depart_id = d.id
        JOIN teacher t ON sch.teacher_id = t.id
        WHERE sch.class_id = ?
        ORDER BY sch.day_of_week
    """, (class_id,)).fetchall()

    return render_template("view_class.html",
                           this_class=this_class,
                           students=students_in_class,
                           schedule=class_schedule)


# Hard delete a teacher
# Must check: if this teacher has classes assigned, 
# deleting them breaks those classes
# So we refuse the delete and tell the admin to reassign first
@app.route("/teachers/delete/<int:teacher_id>", methods=["POST"])
def delete_teacher(teacher_id):
    db = get_db()

    # Check if teacher has any classes
    has_classes = db.execute(
        "SELECT COUNT(*) FROM class WHERE teacher_id = ?", (teacher_id,)
    ).fetchone()[0]
    # fetchone() returns one row, [0] gets the first column = the count

    if has_classes > 0:
        # Don't delete — send them back with an error message
        # We pass the error as a URL parameter so the teachers page can show it
        return redirect(url_for("teachers", error="لا يمكن حذف الأستاذ لأنه مرتبط بمجموعات. قم بإعادة تعيين المجموعات أولاً"))

    # Also remove from any extra teacher assignments
    db.execute(
        "DELETE FROM class_extra_teacher WHERE teacher_id = ?", (teacher_id,)
    )
    # Remove from schedule
    db.execute(
        "DELETE FROM schedule WHERE teacher_id = ?", (teacher_id,)
    )
    db.execute("DELETE FROM teacher WHERE id = ?", (teacher_id,))
    db.commit()
    return redirect(url_for("teachers"))

# ============================================================
#  FEATURE 3 — PAYMENTS
# ============================================================


# View payment status for a specific class
# Shows a table: each student, their payment row for the selected month/year,
# and whether they paid or not
@app.route("/payments/class/<int:class_id>")
def class_payments(class_id):
    db = get_db()

    # Get year and month from URL parameters, default to current
    # Example URL: /payments/class/3?year=2024&month=10
    import datetime
    now = datetime.date.today()

    try:
       year = int(request.args.get("year", now.year))
    except (ValueError, TypeError):
       year = now.year
    try:
       month = int(request.args.get("month", now.month))
    except (ValueError, TypeError):
       month = now.month

    # Class info for the page header
    this_class = db.execute("""
        SELECT c.id, c.group_number,
               t.first_name || ' ' || t.last_name AS teacher_name,
               cat.name AS category_name,
               cat.payment_type
        FROM class c
        JOIN teacher t ON c.teacher_id = t.id
        JOIN category cat ON c.category_id = cat.id
        WHERE c.id = ?
    """, (class_id,)).fetchone()

    # For each student in this class, get their payment row for this period
    # LEFT JOIN means: even if no payment row exists yet, student still appears
    # with NULL payment fields — so you can see who is missing a payment record
    # For annual: match on year only, month is NULL
    # For monthly: match on year AND month


    if this_class["payment_type"] == "سنويا":
       payment_status = db.execute("""
           SELECT
            s.id AS student_id,
            s.first_name,
            s.last_name,
            p.id AS payment_id,
            p.amount,
            p.paid,
            p.paid_date
        FROM student s
        LEFT JOIN payment p ON p.student_id = s.id
            AND p.year = ?
            AND p.month IS NULL
        WHERE s.class_id = ? AND s.is_active = 1
        ORDER BY s.last_name
      """, (year, class_id)).fetchall()
    else:
        payment_status = db.execute("""
        SELECT
            s.id AS student_id,
            s.first_name,
            s.last_name,
            p.id AS payment_id,
            p.amount,
            p.paid,
            p.paid_date
        FROM student s
        LEFT JOIN payment p ON p.student_id = s.id
            AND p.year = ?
            AND p.month = ?
        WHERE s.class_id = ? AND s.is_active = 1
        ORDER BY s.last_name
    """, (year, month, class_id)).fetchall()


    return render_template("class_payments.html",
                           this_class=this_class,
                           payments=payment_status,
                           year=year,
                           month=month,
                           months=MONTHS)


# Record a payment: mark an existing payment row as paid
# The payment row must already exist (created by generate route below)
# This route is called when admin clicks "دفع" next to a student
@app.route("/payments/record/<int:payment_id>", methods=["POST"])
def record_payment(payment_id):
    db = get_db()
    import datetime
    today = datetime.date.today().isoformat()
    # isoformat() gives '2024-10-15' — clean string for storage

    db.execute("""
        UPDATE payment
        SET paid = 1, paid_date = ?
        WHERE id = ?
    """, (today, payment_id))
    db.commit()

    # We need to go back to the same class payment page
    # The class_id comes from the form (hidden input in the template)
    class_id = request.form.get("class_id")
    year = request.form.get("year")
    month = request.form.get("month")
    return redirect(url_for("class_payments",
                            class_id=class_id,
                            year=year,
                            month=month))



@app.route("/payments")
def payments_home():
    # User picks category → class → year → month here
    # Then gets redirected to class_payments with those parameters
    db = get_db()
    import datetime
    now = datetime.date.today()

    category_id = request.args.get("category_id", "").strip()
    class_id = request.args.get("class_id", "").strip()
    year = request.args.get("year", str(now.year)).strip()
    month = request.args.get("month", str(now.month)).strip()

    categories = db.execute("SELECT id, name FROM category").fetchall()

    # Load classes filtered by category if one is selected
    if category_id:
        classes = db.execute("""
            SELECT c.id, c.group_number, c.category_id,
                   t.first_name || ' ' || t.last_name || ' - مجموعة ' || c.group_number AS class_name,
                   cat.payment_type
            FROM class c
            JOIN teacher t ON c.teacher_id = t.id
            JOIN category cat ON c.category_id = cat.id
            WHERE c.category_id = ?
            ORDER BY t.last_name, c.group_number
        """, (category_id,)).fetchall()
    else:
        classes = []

    # If class is selected, redirect directly to class_payments
    if class_id and year:
        try:
            return redirect(url_for("class_payments",
                                class_id=int(class_id),
                                year=year,
                                month=month if month else 1))
        except (ValueError, TypeError):
            pass


    return render_template("payments_home.html",
                           categories=categories,
                           classes=classes,
                           selected_category=category_id,
                           selected_year=year,
                           selected_month=month,
                           months=MONTHS,
                           academic_years=ACADEMIC_YEARS)






# Undo a payment — in case admin marks wrong student as paid
@app.route("/payments/unrecord/<int:payment_id>", methods=["POST"])
def unrecord_payment(payment_id):
    db = get_db()
    db.execute("""
        UPDATE payment
        SET paid = 0, paid_date = NULL
        WHERE id = ?
    """, (payment_id,))
    db.commit()
    class_id = request.form.get("class_id")
    year = request.form.get("year")
    month = request.form.get("month")
    return redirect(url_for("class_payments",
                            class_id=class_id,
                            year=year,
                            month=month))


# Auto-generate payment rows for a class for a given month/year
# This creates one payment row per active student in the class
# It reads the correct amount from payment_rate based on category
# and student employment status
# You run this once at the start of each month for monthly categories,
# or once at enrollment for annual categories
@app.route("/payments/generate/<int:class_id>", methods=["POST"])
def generate_payments(class_id):
    db = get_db()
    import datetime
    now = datetime.date.today()
    year = int(request.form.get("year", now.year))
    month = int(request.form.get("month", now.month))

    # Get the category and payment type for this class
    class_info = db.execute("""
        SELECT cat.id AS category_id, cat.payment_type
        FROM class c
        JOIN category cat ON c.category_id = cat.id
        WHERE c.id = ?
    """, (class_id,)).fetchone()

    payment_type = class_info["payment_type"]

    # Get all active students in this class
    students = db.execute("""
        SELECT id, employment_status
        FROM student
        WHERE class_id = ? AND is_active = 1
    """, (class_id,)).fetchall()

    for student in students:
        # Look up the correct amount for this student's employment status
        # in this category
        rate = db.execute("""
            SELECT amount FROM payment_rate
            WHERE category_id = ? AND employment_status = ?
        """, (class_info["category_id"], student["employment_status"])).fetchone()

        if rate is None:
            # Fallback: try the 'قاصر' rate if no specific rate found
            rate = db.execute("""
                SELECT amount FROM payment_rate
                WHERE category_id = ? AND employment_status = 'قاصر'
            """, (class_info["category_id"],)).fetchone()

        amount = rate["amount"] if rate else 0

        # INSERT OR IGNORE: if a payment row already exists for this
        # student/month/year, do nothing — prevents duplicates
        # This requires a UNIQUE constraint on (student_id, year, month)
        # Add this to your payment table in schema.sql:
        # UNIQUE (student_id, year, month)
        db.execute("""
            INSERT OR IGNORE INTO payment
                (student_id, amount, payment_type, year, month, paid)
            VALUES (?, ?, ?, ?, ?, 0)
        """, (student["id"], amount, payment_type, year,
              month if payment_type == "شهريا" else None))

    db.commit()
    return redirect(url_for("class_payments",
                            class_id=class_id,
                            year=year,
                            month=month))


# View all unpaid students across the entire school
# Can filter by month/year for monthly, or just year for annual
@app.route("/payments/unpaid")
def unpaid_students():
    db = get_db()
    import datetime
    now = datetime.date.today()
    year = int(request.args.get("year", now.year))
    month_param = request.args.get("month", "")

    query = """
        SELECT
            s.id, s.first_name, s.last_name, s.parent_phone,
            p.amount, p.payment_type, p.year, p.month,
            cat.name AS category_name,
            t.first_name || ' ' || t.last_name AS teacher_name,
            c.group_number
        FROM payment p
        JOIN student s ON p.student_id = s.id
        JOIN class c ON s.class_id = c.id
        JOIN category cat ON c.category_id = cat.id
        JOIN teacher t ON c.teacher_id = t.id
        WHERE p.paid = 0 AND s.is_active = 1 AND p.year = ?
    """
    params = [year]

    if month_param:
        query += " AND p.month = ?"
        params.append(int(month_param))

    query += " ORDER BY cat.name, s.last_name"

    unpaid = db.execute(query, params).fetchall()

    return render_template("unpaid_students.html",
                           unpaid=unpaid,
                           year=year,
                           month=month_param,
                           months=MONTHS)


# ============================================================
#  FEATURE 4 — REPORTS
# ============================================================


# All reports on one page — easier for non-technical users
# than navigating to separate pages for each number
@app.route("/reports")
def reports():
    db = get_db()
    import datetime
    now = datetime.date.today()
    year = int(request.args.get("year", now.year))
    month = int(request.args.get("month", now.month))

    # --- Report 1: Student count per class ---
    # Shows each class, its teacher, and how many active students it has
    count_per_class = db.execute("""
        SELECT
            cat.name AS category_name,
            t.first_name || ' ' || t.last_name AS teacher_name,
            c.group_number,
            COUNT(s.id) AS student_count
        FROM class c
        JOIN category cat ON c.category_id = cat.id
        JOIN teacher t ON c.teacher_id = t.id
        LEFT JOIN student s ON s.class_id = c.id AND s.is_active = 1
        GROUP BY c.id
        ORDER BY cat.name, t.last_name
    """).fetchall()

    # --- Report 2: Student count per category ---
    count_per_category = db.execute("""
        SELECT
            cat.name AS category_name,
            COUNT(s.id) AS student_count
        FROM category cat
        LEFT JOIN class c ON c.category_id = cat.id
        LEFT JOIN student s ON s.class_id = c.id AND s.is_active = 1
        GROUP BY cat.id
        ORDER BY cat.name
    """).fetchall()

    # --- Report 3: Collected vs expected this month (monthly categories) ---
    # Expected = sum of all payment rows for this month
    # Collected = sum of paid payment rows for this month
    # The difference tells you how much is still outstanding
    monthly_report = db.execute("""
        SELECT
            cat.name AS category_name,
            COUNT(p.id) AS total_students,
            SUM(p.amount) AS expected_total,
            SUM(CASE WHEN p.paid = 1 THEN p.amount ELSE 0 END) AS collected,
            SUM(CASE WHEN p.paid = 0 THEN p.amount ELSE 0 END) AS outstanding
        FROM payment p
        JOIN student s ON p.student_id = s.id
        JOIN class c ON s.class_id = c.id
        JOIN category cat ON c.category_id = cat.id
        WHERE p.payment_type = 'شهريا'
          AND p.year = ? AND p.month = ?
        GROUP BY cat.id
        ORDER BY cat.name
    """, (year, month)).fetchall()
    # CASE WHEN works like an if/else inside SQL:
    # if paid=1, count the amount; if paid=0, count 0
    # SUM adds them all up — giving you total collected

    # --- Report 4: Annual payment summary ---
    annual_report = db.execute("""
        SELECT
            cat.name AS category_name,
            COUNT(p.id) AS total_students,
            SUM(p.amount) AS expected_total,
            SUM(CASE WHEN p.paid = 1 THEN p.amount ELSE 0 END) AS collected,
            SUM(CASE WHEN p.paid = 0 THEN p.amount ELSE 0 END) AS outstanding
        FROM payment p
        JOIN student s ON p.student_id = s.id
        JOIN class c ON s.class_id = c.id
        JOIN category cat ON c.category_id = cat.id
        WHERE p.payment_type = 'سنويا' AND p.year = ?
        GROUP BY cat.id
        ORDER BY cat.name
    """, (year,)).fetchall()

    # --- Report 5: Expulsion candidates (3+ unpaid months) ---
    expulsion = db.execute("""
        SELECT
            s.id, s.first_name, s.last_name, s.parent_phone,
            cat.name AS category_name,
            t.first_name || ' ' || t.last_name AS teacher_name,
            COUNT(*) AS missed_months
        FROM student s
        JOIN payment p ON p.student_id = s.id
        JOIN class c ON s.class_id = c.id
        JOIN category cat ON c.category_id = cat.id
        JOIN teacher t ON c.teacher_id = t.id
        WHERE p.paid = 0 AND s.is_active = 1
        GROUP BY s.id
        HAVING missed_months >= 3
        ORDER BY missed_months DESC
    """).fetchall()

    return render_template("reports.html",
                           count_per_class=count_per_class,
                           count_per_category=count_per_category,
                           monthly_report=monthly_report,
                           annual_report=annual_report,
                           expulsion=expulsion,
                           year=year,
                           month=month,
                           months=MONTHS)




# ============================================================
#  FEATURE 5 — DEPARTS & SALLES
# ============================================================

@app.route("/departs")
def departs():
    db = get_db()
    all_departs = db.execute("""
        SELECT d.id, d.name, d.address, COUNT(s.id) AS salle_count
        FROM depart d
        LEFT JOIN salle s ON s.depart_id = d.id
        GROUP BY d.id ORDER BY d.name
    """).fetchall()
    all_salles = db.execute("""
        SELECT s.id, s.room_number, d.name AS depart_name
        FROM salle s JOIN depart d ON s.depart_id = d.id
        ORDER BY d.name, s.room_number
    """).fetchall()
    return render_template("departs.html", departs=all_departs, salles=all_salles)


@app.route("/departs/add", methods=["GET", "POST"])
def add_depart():
    db = get_db()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        address = request.form.get("address", "").strip() or None
        salle_count = request.form.get("salle_count", "0").strip()

        if not name:
            error = "اسم المقر إلزامي"
            return render_template("add_depart.html", error=error,
                                   depart_names=depart_name,
                                   depart_addresses=depart_address,
                                   room_numbers=room_number,
                                   selected_name=name,
                                   selected_address="")

        # Insert the depart
        cursor = db.execute(
            "INSERT INTO depart (name, address) VALUES (?, ?)", (name, address)
        )
        depart_id = cursor.lastrowid

        # Auto-create the first N rooms from the room_number list
        try:
            count = int(salle_count)
        except ValueError:
            count = 0

        # Take the first `count` rooms from the predefined list
        # e.g. count=3 → creates القاعة 1, القاعة 2, القاعة 3
        for i in range(min(count, len(room_number))):
            db.execute(
                "INSERT INTO salle (depart_id, room_number) VALUES (?, ?)",
                (depart_id, room_number[i])
            )

        db.commit()
        return redirect(url_for("departs"))

    return render_template("add_depart.html",
                           depart_names=depart_name,
                           depart_addresses=depart_address,
                           room_numbers=room_number,
                           selected_name="",
                           selected_address="")


@app.route("/departs/delete/<int:depart_id>", methods=["POST"])
def delete_depart(depart_id):
    db = get_db()
    has_salles = db.execute(
        "SELECT COUNT(*) FROM salle WHERE depart_id = ?", (depart_id,)
    ).fetchone()[0]
    if has_salles:
        return redirect(url_for("departs",
                                error="لا يمكن حذف المقر لأنه يحتوي على قاعات. احذف القاعات أولاً"))
    db.execute("DELETE FROM depart WHERE id = ?", (depart_id,))
    db.commit()
    return redirect(url_for("departs"))


@app.route("/salles/add", methods=["GET", "POST"])
def add_salle():
    db = get_db()
    departs_list = db.execute("SELECT id, name FROM depart ORDER BY name").fetchall()
    if request.method == "POST":
        depart_id = request.form.get("depart_id")
        rn = request.form.get("room_number", "").strip()
        if not all([depart_id, rn]):
            error = "المقر ورقم القاعة إلزاميان"
            return render_template("add_salle.html", error=error,
                                   departs=departs_list,
                                   room_numbers=room_number)
        db.execute("INSERT INTO salle (depart_id, room_number) VALUES (?, ?)", (depart_id, rn))
        db.commit()
        return redirect(url_for("departs"))
    return render_template("add_salle.html", departs=departs_list, room_numbers=room_number)


@app.route("/salles/delete/<int:salle_id>", methods=["POST"])
def delete_salle(salle_id):
    db = get_db()
    in_use = db.execute(
        "SELECT COUNT(*) FROM schedule WHERE salle_id = ?", (salle_id,)
    ).fetchone()[0]
    if in_use:
        return redirect(url_for("departs",
                                error="لا يمكن حذف القاعة لأنها مستخدمة في جدول. احذف الجدول أولاً"))
    db.execute("DELETE FROM salle WHERE id = ?", (salle_id,))
    db.commit()
    return redirect(url_for("departs"))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)



