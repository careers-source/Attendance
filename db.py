import sqlite3
from config import Config

def get_db():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'employee',
            department TEXT DEFAULT 'General',
            designation TEXT DEFAULT 'Staff',
            phone TEXT,
            join_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Attendance Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date DATE NOT NULL,
            check_in DATETIME,
            check_out DATETIME,
            total_hours REAL DEFAULT 0.0,
            break_duration_mins INTEGER DEFAULT 0,
            net_hours REAL DEFAULT 0.0,
            status TEXT DEFAULT 'Absent',
            is_late INTEGER DEFAULT 0,
            notes TEXT,
            UNIQUE(user_id, date),
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')

    # Breaks Table (Morning Tea, Lunch, Afternoon Tea)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS breaks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attendance_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            break_type TEXT NOT NULL,
            start_time DATETIME NOT NULL,
            end_time DATETIME,
            duration_mins INTEGER DEFAULT 0,
            status TEXT DEFAULT 'ongoing',
            FOREIGN KEY (attendance_id) REFERENCES attendance (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')

    # Leaves Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leaves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            leave_type TEXT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            reason TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            admin_remarks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == '__main__':
    init_db()
