from werkzeug.security import generate_password_hash
from db import get_db, init_db
from datetime import datetime, timedelta

def seed_database():
    init_db()
    conn = get_db()
    cursor = conn.cursor()

    # Passwords
    admin_pw = generate_password_hash('Prathmesh@1234')
    emp_pw = generate_password_hash('Emp@123')

    # Insert or Update Default Users
    users_data = [
        ('ADM001', 'Prathmesh', 'prathmesh@office.com', admin_pw, 'admin', 'Management', 'Lead Admin', '9876543210', '2024-01-01'),
        ('EMP001', 'Sagar M ', 'sagar@office.com', emp_pw, 'employee', 'General', 'Python Developer', '9699056940', '2026-07-13'),
        ('EMP002', 'Michael Chen', 'emp2@office.com', emp_pw, 'employee', 'Marketing', 'Marketing Specialist', '9876543212', '2024-03-01'),
        ('EMP003', 'David Smith', 'emp3@office.com', emp_pw, 'employee', 'Human Resources', 'HR Coordinator', '9876543213', '2024-04-10')
    ]

    for emp_id, name, email, pw, role, dept, desig, phone, join_d in users_data:
        cursor.execute("SELECT id FROM users WHERE employee_id = ?", (emp_id,))
        row = cursor.fetchone()
        if row:
            cursor.execute("UPDATE users SET password_hash = ?, role = ?, name = ?, email = ? WHERE id = ?", (pw, role, name, email, row['id']))
        else:
            cursor.execute('''
                INSERT INTO users (employee_id, name, email, password_hash, role, department, designation, phone, join_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (emp_id, name, email, pw, role, dept, desig, phone, join_d))

    conn.commit()


    # Get user IDs
    cursor.execute("SELECT id, employee_id FROM users")
    user_map = {row['employee_id']: row['id'] for row in cursor.fetchall()}

    # Create Sample Attendance for Past 5 days
    today = datetime.now().date()
    statuses = ['Present', 'Late', 'Present', 'Half Day', 'Present']
    
    for emp_code, user_id in user_map.items():
        if emp_code == 'ADM001':
            continue
            
        for idx in range(5, 0, -1):
            past_date = (today - timedelta(days=idx)).strftime('%Y-%m-%d')
            
            # Skip weekends (Saturday=5, Sunday=6)
            date_obj = datetime.strptime(past_date, '%Y-%m-%d')
            if date_obj.weekday() >= 5:
                continue

            status = statuses[(idx + user_id) % len(statuses)]
            is_late = 1 if status == 'Late' else 0
            
            check_in_hour = 10 if not is_late else 10
            check_in_min = 5 if not is_late else 35
            check_in_str = f"{past_date} 0{check_in_hour}:{check_in_min}:00"
            
            check_out_str = f"{past_date} 19:00:00" if status != 'Half Day' else f"{past_date} 14:00:00"
            total_hours = 9.0 if status != 'Half Day' else 4.0
            break_mins = 90
            net_hours = total_hours - (break_mins / 60.0)

            cursor.execute('''
                INSERT OR IGNORE INTO attendance (user_id, date, check_in, check_out, total_hours, break_duration_mins, net_hours, status, is_late, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, past_date, check_in_str, check_out_str, total_hours, break_mins, net_hours, status, is_late, 'Regular Shift'))


            if cursor.rowcount > 0:
                att_id = cursor.lastrowid
                # Add sample breaks
                cursor.execute('''
                    INSERT INTO breaks (attendance_id, user_id, break_type, start_time, end_time, duration_mins, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (att_id, user_id, 'lunch', f"{past_date} 13:00:00", f"{past_date} 14:00:00", 60, 'completed'))

                cursor.execute('''
                    INSERT INTO breaks (attendance_id, user_id, break_type, start_time, end_time, duration_mins, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (att_id, user_id, 'morning_tea', f"{past_date} 11:00:00", f"{past_date} 11:15:00", 15, 'completed'))

                cursor.execute('''
                    INSERT INTO breaks (attendance_id, user_id, break_type, start_time, end_time, duration_mins, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (att_id, user_id, 'evening_tea', f"{past_date} 17:00:00", f"{past_date} 17:15:00", 15, 'completed'))


    # Sample Leaves
    cursor.execute("SELECT COUNT(*) as count FROM leaves")
    if cursor.fetchone()['count'] == 0:
        leaves_data = [
            (user_map['EMP001'], 'Casual', (today + timedelta(days=2)).strftime('%Y-%m-%d'), (today + timedelta(days=3)).strftime('%Y-%m-%d'), 'Family Function', 'Pending', None),
            (user_map['EMP002'], 'Sick', (today - timedelta(days=10)).strftime('%Y-%m-%d'), (today - timedelta(days=9)).strftime('%Y-%m-%d'), 'Viral Fever', 'Approved', 'Get well soon'),
        ]

        cursor.executemany('''
            INSERT INTO leaves (user_id, leave_type, start_date, end_date, reason, status, admin_remarks)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', leaves_data)


    conn.commit()
    conn.close()
    print("Database seeded with default Admin, Employees, Attendance & Leaves!")

if __name__ == '__main__':
    seed_database()
