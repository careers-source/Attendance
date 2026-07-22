from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from db import get_db
from routes.auth import jwt_required

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/dashboard-stats', methods=['GET'])
@jwt_required(role='admin')
def get_dashboard_stats():
    today_str = datetime.now().strftime('%Y-%m-%d')
    month_str = datetime.now().strftime('%Y-%m')

    conn = get_db()
    cursor = conn.cursor()

    # Total employees
    cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'employee'")
    total_employees = cursor.fetchone()['count']

    # Today attendance breakdown
    cursor.execute("""
        SELECT 
            COUNT(CASE WHEN status IN ('Present', 'Late') THEN 1 END) as present_today,
            COUNT(CASE WHEN status = 'Late' THEN 1 END) as late_today,
            COUNT(CASE WHEN status = 'Half Day' THEN 1 END) as half_day_today,
            COUNT(CASE WHEN status = 'On Leave' THEN 1 END) as leave_today
        FROM attendance
        WHERE date = ?
    """, (today_str,))
    today_stats = dict(cursor.fetchone())

    # Pending leaves count
    cursor.execute("SELECT COUNT(*) as count FROM leaves WHERE status = 'Pending'")
    pending_leaves_count = cursor.fetchone()['count']

    # Monthly Breakdown chart data
    cursor.execute("""
        SELECT status, COUNT(*) as count 
        FROM attendance 
        WHERE date LIKE ?
        GROUP BY status
    """, (f"{month_str}%",))
    monthly_chart_data = {row['status']: row['count'] for row in cursor.fetchall()}

    # Department breakdown
    cursor.execute("""
        SELECT department, COUNT(*) as count 
        FROM users 
        WHERE role = 'employee' 
        GROUP BY department
    """)
    dept_chart_data = {row['department']: row['count'] for row in cursor.fetchall()}

    conn.close()

    return jsonify({
        'total_employees': total_employees,
        'today_stats': today_stats,
        'pending_leaves_count': pending_leaves_count,
        'monthly_chart_data': monthly_chart_data,
        'dept_chart_data': dept_chart_data
    }), 200

@admin_bp.route('/employees', methods=['GET'])
@jwt_required(role='admin')
def get_employees():
    search = request.args.get('search', '').strip().lower()
    department = request.args.get('department', '').strip()

    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT id, employee_id, name, email, role, department, designation, phone, join_date, created_at FROM users WHERE 1=1"
    params = []

    if search:
        query += " AND (LOWER(name) LIKE ? OR LOWER(email) LIKE ? OR LOWER(employee_id) LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    if department:
        query += " AND department = ?"
        params.append(department)

    query += " ORDER BY id DESC"

    cursor.execute(query, params)
    employees = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify({'employees': employees}), 200

@admin_bp.route('/employees', methods=['POST'])
@jwt_required(role='admin')
def add_employee():
    data = request.get_json() or {}
    employee_id = data.get('employee_id', '').strip()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()
    role = data.get('role', 'employee').strip().lower()
    department = data.get('department', 'General').strip()
    designation = data.get('designation', 'Staff').strip()
    phone = data.get('phone', '').strip()
    join_date = data.get('join_date', datetime.now().strftime('%Y-%m-%d')).strip()

    if not employee_id or not name or not email or not password:
        return jsonify({'error': 'Employee ID, Name, Email, and Password are required'}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Check for existing email or employee_id
    cursor.execute("SELECT id FROM users WHERE email = ? OR employee_id = ?", (email, employee_id))
    if cursor.fetchone():
        conn.close()
        return jsonify({'error': 'An employee with this Email or Employee ID already exists'}), 400

    password_hash = generate_password_hash(password)

    cursor.execute("""
        INSERT INTO users (employee_id, name, email, password_hash, role, department, designation, phone, join_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (employee_id, name, email, password_hash, role, department, designation, phone, join_date))

    conn.commit()
    conn.close()

    return jsonify({'message': 'Employee added successfully.'}), 201

@admin_bp.route('/employees/<int:user_id>', methods=['PUT'])
@jwt_required(role='admin')
def update_employee(user_id):
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    role = data.get('role', '').strip()
    department = data.get('department', '').strip()
    designation = data.get('designation', '').strip()
    phone = data.get('phone', '').strip()
    password = data.get('password', '').strip()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Employee not found'}), 404

    cursor.execute("""
        UPDATE users 
        SET name = COALESCE(NULLIF(?, ''), name),
            role = COALESCE(NULLIF(?, ''), role),
            department = COALESCE(NULLIF(?, ''), department),
            designation = COALESCE(NULLIF(?, ''), designation),
            phone = COALESCE(NULLIF(?, ''), phone)
        WHERE id = ?
    """, (name, role, department, designation, phone, user_id))

    if password:
        pw_hash = generate_password_hash(password)
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (pw_hash, user_id))

    conn.commit()
    conn.close()

    return jsonify({'message': 'Employee updated successfully.'}), 200

@admin_bp.route('/employees/<int:user_id>', methods=['DELETE'])
@jwt_required(role='admin')
def delete_employee(user_id):
    if user_id == g.current_user['id']:
        return jsonify({'error': 'You cannot delete your own admin account!'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Employee removed successfully.'}), 200

@admin_bp.route('/attendance', methods=['GET'])
@jwt_required(role='admin')
def get_global_attendance():
    selected_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d')).strip()
    month = request.args.get('month', '').strip()
    search = request.args.get('search', '').strip().lower()
    department = request.args.get('department', '').strip()
    status = request.args.get('status', '').strip()

    conn = get_db()
    cursor = conn.cursor()

    query = """
        SELECT a.*, u.employee_id, u.name as user_name, u.email as user_email, u.department, u.designation,
               (SELECT COUNT(*) FROM breaks b WHERE b.attendance_id = a.id) as break_count
        FROM attendance a
        JOIN users u ON a.user_id = u.id
        WHERE 1=1
    """
    params = []

    if month:
        query += " AND a.date LIKE ?"
        params.append(f"{month}%")
    elif selected_date:
        query += " AND a.date = ?"
        params.append(selected_date)

    if search:
        query += " AND (LOWER(u.name) LIKE ? OR LOWER(u.employee_id) LIKE ? OR LOWER(u.email) LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    if department:
        query += " AND u.department = ?"
        params.append(department)

    if status:
        query += " AND a.status = ?"
        params.append(status)

    query += " ORDER BY a.date DESC, a.id DESC"

    cursor.execute(query, params)
    records = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify({'attendance': records}), 200

@admin_bp.route('/leaves', methods=['GET'])
@jwt_required(role='admin')
def get_all_leaves():
    status = request.args.get('status', '').strip()

    conn = get_db()
    cursor = conn.cursor()

    query = """
        SELECT l.*, u.employee_id, u.name as user_name, u.email as user_email, u.department
        FROM leaves l
        JOIN users u ON l.user_id = u.id
        WHERE 1=1
    """
    params = []

    if status:
        query += " AND l.status = ?"
        params.append(status)

    query += " ORDER BY l.id DESC"

    cursor.execute(query, params)
    leaves = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify({'leaves': leaves}), 200

@admin_bp.route('/leave/<int:leave_id>/action', methods=['POST'])
@jwt_required(role='admin')
def process_leave(leave_id):
    data = request.get_json() or {}
    action = data.get('action', '').strip().capitalize() # 'Approved' or 'Rejected'
    admin_remarks = data.get('remarks', '').strip()

    if action not in ['Approved', 'Rejected']:
        return jsonify({'error': 'Action must be Approved or Rejected'}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM leaves WHERE id = ?", (leave_id,))
    leave = cursor.fetchone()

    if not leave:
        conn.close()
        return jsonify({'error': 'Leave request not found'}), 404

    cursor.execute("""
        UPDATE leaves 
        SET status = ?, admin_remarks = ?
        WHERE id = ?
    """, (action, admin_remarks, leave_id))

    # If approved, update or insert attendance records as 'On Leave' for that date range
    if action == 'Approved':
        start_dt = datetime.strptime(leave['start_date'], '%Y-%m-%d').date()
        end_dt = datetime.strptime(leave['end_date'], '%Y-%m-%d').date()
        curr_dt = start_dt
        
        while curr_dt <= end_dt:
            dt_str = curr_dt.strftime('%Y-%m-%d')
            cursor.execute("SELECT id FROM attendance WHERE user_id = ? AND date = ?", (leave['user_id'], dt_str))
            existing = cursor.fetchone()

            if existing:
                cursor.execute("UPDATE attendance SET status = 'On Leave', notes = ? WHERE id = ?", (f"Approved Leave: {leave['leave_type']}", existing['id']))
            else:
                cursor.execute("""
                    INSERT INTO attendance (user_id, date, status, notes)
                    VALUES (?, ?, 'On Leave', ?)
                """, (leave['user_id'], dt_str, f"Approved Leave: {leave['leave_type']}"))

            curr_dt += timedelta(days=1)

    conn.commit()
    conn.close()

    return jsonify({'message': f"Leave application {action} successfully."}), 200
