PRAGMA foreign_keys = ON;

-- LOCATION
CREATE TABLE depart (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT
);

CREATE TABLE salle (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    depart_id INTEGER NOT NULL,
    room_number TEXT NOT NULL,
    FOREIGN KEY (depart_id) REFERENCES depart(id)
);

-- ACADEMIC STRUCTURE
CREATE TABLE category (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    payment_type TEXT NOT NULL CHECK(payment_type IN ('شهريا', 'سنويا', 'لا يوجد')),
    has_levels INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE level (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL,
    level_number INTEGER NOT NULL,
    name TEXT,
    FOREIGN KEY (category_id) REFERENCES category(id)
);


CREATE TABLE class (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL,
    level_id INTEGER,               -- NULL for categories without levels
    teacher_id INTEGER NOT NULL,    -- class is owned by a teacher
    group_number INTEGER NOT NULL,  -- teacher's group 1, 2, 3, 4, or 5
    academic_year TEXT NOT NULL,
    FOREIGN KEY (category_id) REFERENCES category(id),
    FOREIGN KEY (level_id) REFERENCES level(id),
    FOREIGN KEY (teacher_id) REFERENCES teacher(id),
    UNIQUE (teacher_id, group_number, academic_year)
    -- a teacher can't have two "group 1" in the same year
);

-- Only needed for level 3 الناشئة co-teaching : class has many teachers 
CREATE TABLE class_extra_teacher (
    class_id INTEGER NOT NULL,
    teacher_id INTEGER NOT NULL,
    PRIMARY KEY (class_id, teacher_id),
    FOREIGN KEY (class_id) REFERENCES class(id),
    FOREIGN KEY (teacher_id) REFERENCES teacher(id)
);


-- PEOPLE
CREATE TABLE teacher (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    phone TEXT,
    specialty TEXT,
    category_id INTEGER NOT NULL,
    FOREIGN KEY (category_id) REFERENCES category(id)
);

CREATE TABLE student (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    parent_name TEXT ,
    parent_phone TEXT NOT NULL,
    address TEXT,
    employment_status TEXT NOT NULL DEFAULT 'قاصر'
        CHECK(employment_status IN ('موظف', 'عاطل', 'قاصر')),
    class_id INTEGER ,
    is_active INTEGER  DEFAULT 1,
    enrolled_date TEXT ,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (class_id) REFERENCES class(id)
);

-- SCHEDULE
CREATE TABLE schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER NOT NULL,
    teacher_id INTEGER NOT NULL,
    salle_id INTEGER NOT NULL,
    day_of_week TEXT NOT NULL,
    start_time TEXT NOT NULL,
    FOREIGN KEY (class_id) REFERENCES class(id),
    FOREIGN KEY (teacher_id) REFERENCES teacher(id),
    FOREIGN KEY (salle_id) REFERENCES salle(id)
);

-- PAYMENT RATES
CREATE TABLE payment_rate (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL,
    employment_status TEXT NOT NULL DEFAULT 'قاصر'
        CHECK(employment_status IN ('موظف', 'عاطل', 'قاصر')),
    amount REAL NOT NULL,
    FOREIGN KEY (category_id) REFERENCES category(id)
);

-- PAYMENTS
-- PAYMENTS
CREATE TABLE payment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    payment_type TEXT NOT NULL CHECK(payment_type IN ('شهريا', 'سنويا')),
    year INTEGER NOT NULL,
    month INTEGER CHECK(month BETWEEN 1 AND 12),
    paid INTEGER NOT NULL DEFAULT 0,
    paid_date TEXT,
    FOREIGN KEY (student_id) REFERENCES student(id),
    UNIQUE (student_id, year, month)
);