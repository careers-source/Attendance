from flask import Blueprint, request, jsonify, g
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db
from routes.auth import jwt_required
from config import Config

employee_bp = Blueprint('employee', __name__, url_prefix='/api/employee')

@employee_bp.route('/dashboard-summary', methods=['GET'])
@jwt_required(role='employee')
def get_dashboard_summary():
    user_id = g.current_user['id']
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Today's attendance record
    cursor.execute("SELECT * FROM attendance WHERE user_id = ? AND date = ?", (user_id, today_str))
    today_att = cursor.fetchone()
    today_att_dict = dict(today_att) if today_att else None
    
    # Active break if any
    active_break = None
    if today_att:
        cursor.execute("SELECT * FROM breaks WHERE attendance_id = ? AND status = 'ongoing' ORDER BY id DESC LIMIT 1", (today_att['id'],))
        brk = cursor.fetchone()
        if brk:
            active_break = dict(brk)
            
    # Monthly stats (Current month)
    curr_month = datetime.now().strftime('%Y-%m')
    cursor.execute("""
        SELECT 
            COUNT(CASE WHEN status IN ('Present', 'Late') THEN 1 END) as present_days,
            COUNT(CASE WHEN status = 'Late' THEN 1 END) as late_days,
            COUNT(CASE WHEN status = 'Half Day' THEN 1 END) as half_days,
            COALESCE(SUM(net_hours), 0) as total_net_hours,
            COALESCE(SUM(break_duration_mins), 0) as total_break_mins
        FROM attendance 
        WHERE user_id = ? AND date LIKE ?
    """, (user_id, f"{curr_month}%"))
    monthly_stats = dict(cursor.fetchone())
    
    # Pending leave count
    cursor.execute("SELECT COUNT(*) as count FROM leaves WHERE user_id = ? AND status = 'Pending'", (user_id,))
    pending_leaves = cursor.fetchone()['count']
    
    conn.close()

    return jsonify({
        'today': today_att_dict,
        'active_break': active_break,
        'monthly_stats': monthly_stats,
        'pending_leaves': pending_leaves
    }), 200

@employee_bp.route('/check-in', methods=['POST'])
@jwt_required(role='employee')
def check_in():
    user_id = g.current_user['id']
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d')
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')

    conn = get_db()
    cursor = conn.cursor()

    # Check if already checked in today
    cursor.execute("SELECT * FROM attendance WHERE user_id = ? AND date = ?", (user_id, today_str))
    existing = cursor.fetchone()
    if existing and existing['check_in']:
        conn.close()
        return jsonify({'error': 'You have already checked in today!'}), 400

    # Determine late mark
    # Grace time is SHIFT_START_TIME + GRACE_PERIOD_MINUTES (e.g. 09:15:00)
    shift_start_dt = datetime.strptime(f"{today_str} {Config.SHIFT_START_TIME}", '%Y-%m-%d %H:%M:%S')
    grace_dt = shift_start_dt + timedelta(minutes=Config.GRACE_PERIOD_MINUTES)
    is_late = 1 if now > grace_dt else 0
    status = 'Late' if is_late else 'Present'

    if existing:
        cursor.execute("""
            UPDATE attendance 
            SET check_in = ?, is_late = ?, status = ?
            WHERE id = ?
        """, (now_str, is_late, status, existing['id']))
        att_id = existing['id']
    else:
        cursor.execute("""
            INSERT INTO attendance (user_id, date, check_in, is_late, status)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, today_str, now_str, is_late, status))
        att_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return jsonify({
        'message': f"Checked in successfully at {now.strftime('%I:%M %p')}" + (" (Marked Late)" if is_late else ""),
        'attendance_id': att_id,
        'is_late': is_late,
        'status': status
    }), 200

@employee_bp.route('/check-out', methods=['POST'])
@jwt_required(role='employee')
def check_out():
    user_id = g.current_user['id']
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d')
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM attendance WHERE user_id = ? AND date = ?", (user_id, today_str))
    att = cursor.fetchone()

    if not att or not att['check_in']:
        conn.close()
        return jsonify({'error': 'You must check in before checking out!'}), 400

    if att['check_out']:
        conn.close()
        return jsonify({'error': 'You have already checked out today!'}), 400

    # Ensure no ongoing break
    cursor.execute("SELECT * FROM breaks WHERE attendance_id = ? AND status = 'ongoing'", (att['id'],))
    active_break = cursor.fetchone()
    if active_break:
        conn.close()
        return jsonify({'error': 'Please end your active break before checking out!'}), 400

    check_in_dt = datetime.strptime(att['check_in'], '%Y-%m-%d %H:%M:%S')
    total_seconds = (now - check_in_dt).total_seconds()
    total_hours = round(total_seconds / 3600.0, 2)
    
    break_mins = att['break_duration_mins'] or 0
    net_hours = round(total_hours - (break_mins / 60.0), 2)
    if net_hours < 0:
        net_hours = 0.0

    # Determine status based on net hours
    final_status = att['status']
    if net_hours < 4.0:
        final_status = 'Half Day'
    elif att['is_late']:
        final_status = 'Late'
    else:
        final_status = 'Present'

    cursor.execute("""
        UPDATE attendance 
        SET check_out = ?, total_hours = ?, net_hours = ?, status = ?
        WHERE id = ?
    """, (now_str, total_hours, net_hours, final_status, att['id']))

    conn.commit()
    conn.close()

    return jsonify({
        'message': f"Checked out successfully at {now.strftime('%I:%M %p')}",
        'total_hours': total_hours,
        'net_hours': net_hours,
        'status': final_status
    }), 200

@employee_bp.route('/break/start', methods=['POST'])
@jwt_required(role='employee')
def start_break():
    data = request.get_json() or {}
    break_type = data.get('break_type', '').strip().lower() # 'morning_tea', 'lunch', 'afternoon_tea'

    if break_type not in ['morning_tea', 'lunch', 'afternoon_tea']:
        return jsonify({'error': 'Invalid break type specified'}), 400

    user_id = g.current_user['id']
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d')
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM attendance WHERE user_id = ? AND date = ?", (user_id, today_str))
    att = cursor.fetchone()

    if not att or not att['check_in']:
        conn.close()
        return jsonify({'error': 'You must check in before taking a break!'}), 400

    if att['check_out']:
        conn.close()
        return jsonify({'error': 'You have already checked out for today!'}), 400

    # Check for active break
    cursor.execute("SELECT * FROM breaks WHERE attendance_id = ? AND status = 'ongoing'", (att['id'],))
    if cursor.fetchone():
        conn.close()
        return jsonify({'error': 'You already have an active break in progress!'}), 400

    cursor.execute("""
        INSERT INTO breaks (attendance_id, user_id, break_type, start_time, status)
        VALUES (?, ?, ?, ?, 'ongoing')
    """, (att['id'], user_id, break_type, now_str))

    conn.commit()
    conn.close()

    formatted_type = break_type.replace('_', ' ').title()
    return jsonify({
        'message': f"{formatted_type} started at {now.strftime('%I:%M %p')}",
        'break_type': break_type,
        'start_time': now_str
    }), 200

@employee_bp.route('/break/end', methods=['POST'])
@jwt_required(role='employee')
def end_break():
    user_id = g.current_user['id']
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d')
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM attendance WHERE user_id = ? AND date = ?", (user_id, today_str))
    att = cursor.fetchone()

    if not att:
        conn.close()
        return jsonify({'error': 'No attendance record found for today'}), 400

    cursor.execute("SELECT * FROM breaks WHERE attendance_id = ? AND status = 'ongoing' ORDER BY id DESC LIMIT 1", (att['id'],))
    active_break = cursor.fetchone()

    if not active_break:
        conn.close()
        return jsonify({'error': 'No active break found to end'}), 400

    start_dt = datetime.strptime(active_break['start_time'], '%Y-%m-%d %H:%M:%S')
    duration_seconds = (now - start_dt).total_seconds()
    duration_mins = max(1, int(duration_seconds // 60))

    # Update break record
    cursor.execute("""
        UPDATE breaks 
        SET end_time = ?, duration_mins = ?, status = 'completed'
        WHERE id = ?
    """, (now_str, duration_mins, active_break['id']))

    # Total accumulated break duration for today
    cursor.execute("SELECT COALESCE(SUM(duration_mins), 0) as total_break FROM breaks WHERE attendance_id = ? AND status = 'completed'", (att['id'],))
    total_break_mins = cursor.fetchone()['total_break']

    cursor.execute("UPDATE attendance SET break_duration_mins = ? WHERE id = ?", (total_break_mins, att['id']))

    conn.commit()
    conn.close()

    formatted_type = active_break['break_type'].replace('_', ' ').title()
    return jsonify({
        'message': f"{formatted_type} ended. Duration: {duration_mins} mins.",
        'duration_mins': duration_mins,
        'total_break_mins': total_break_mins
    }), 200

@employee_bp.route('/history', methods=['GET'])
@jwt_required(role='employee')
def get_attendance_history():
    user_id = g.current_user['id']
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT a.*, 
               (SELECT COUNT(*) FROM breaks b WHERE b.attendance_id = a.id) as break_count
        FROM attendance a
        WHERE a.user_id = ? AND a.date LIKE ?
        ORDER BY a.date DESC
    """, (user_id, f"{month}%"))
    
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({'history': rows}), 200

@employee_bp.route('/leave/apply', methods=['POST'])
@jwt_required(role='employee')
def apply_leave():
    data = request.get_json() or {}
    leave_type = data.get('leave_type', '').strip()
    start_date = data.get('start_date', '').strip()
    end_date = data.get('end_date', '').strip()
    reason = data.get('reason', '').strip()

    if not leave_type or not start_date or not end_date or not reason:
        return jsonify({'error': 'All fields (leave type, start date, end date, reason) are required'}), 400

    user_id = g.current_user['id']
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO leaves (user_id, leave_type, start_date, end_date, reason, status)
        VALUES (?, ?, ?, ?, ?, 'Pending')
    """, (user_id, leave_type, start_date, end_date, reason))
    
    conn.commit()
    conn.close()

    return jsonify({'message': 'Leave application submitted successfully for Admin review.'}), 201

@employee_bp.route('/leave/history', methods=['GET'])
@jwt_required(role='employee')
def get_leave_history():
    user_id = g.current_user['id']
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leaves WHERE user_id = ? ORDER BY id DESC", (user_id,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify({'leaves': rows}), 200

@employee_bp.route('/profile/update', methods=['POST'])
@jwt_required()
def update_profile():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()
    current_password = data.get('current_password', '').strip()
    new_password = data.get('new_password', '').strip()

    user_id = g.current_user['id']
    conn = get_db()
    cursor = conn.cursor()

    if name:
        cursor.execute("UPDATE users SET name = ?, phone = ? WHERE id = ?", (name, phone, user_id))

    if new_password:
        if not current_password:
            conn.close()
            return jsonify({'error': 'Current password required to change password'}), 400

        cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not check_password_hash(user['password_hash'], current_password):
            conn.close()
            return jsonify({'error': 'Current password does not match'}), 400

        new_hash = generate_password_hash(new_password)
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))

    conn.commit()
    conn.close()

    return jsonify({'message': 'Profile updated successfully.'}), 200
