import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, request, jsonify, g
from werkzeug.security import check_password_hash, generate_password_hash
from config import Config
from db import get_db

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

def generate_token(user_id, role, email, name):
    payload = {
        'user_id': user_id,
        'role': role,
        'email': email,
        'name': name,
        'exp': datetime.utcnow() + timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES)
    }
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm='HS256')

def jwt_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            
            # Check Authorization Header
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
            
            # Check Cookie as Fallback
            if not token:
                token = request.cookies.get('jwt_token')
                
            if not token:
                return jsonify({'error': 'Authentication token missing'}), 401
                
            try:
                data = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
                
                # Verify user exists in database
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("SELECT id, employee_id, name, email, role, department, designation, phone FROM users WHERE id = ?", (data['user_id'],))
                user = cursor.fetchone()
                conn.close()
                
                if not user:
                    return jsonify({'error': 'User no longer exists'}), 401

                g.current_user = dict(user)
                
                if role and g.current_user['role'] != role and g.current_user['role'] != 'admin':
                    return jsonify({'error': 'Unauthorized access to this resource'}), 403
                    
            except jwt.ExpiredSignatureError:
                return jsonify({'error': 'Token has expired. Please login again'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'error': 'Invalid authentication token'}), 401
                
            return f(*args, **kwargs)
        return decorated
    return decorator

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email,))
    user = cursor.fetchone()
    conn.close()

    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Invalid email or password'}), 401

    token = generate_token(user['id'], user['role'], user['email'], user['name'])

    response = jsonify({
        'message': 'Login successful',
        'token': token,
        'user': {
            'id': user['id'],
            'employee_id': user['employee_id'],
            'name': user['name'],
            'email': user['email'],
            'role': user['role'],
            'department': user['department'],
            'designation': user['designation']
        }
    })

    # Also set HttpOnly Cookie for session persistence
    response.set_cookie('jwt_token', token, httponly=True, max_age=Config.JWT_ACCESS_TOKEN_EXPIRES)
    return response, 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    return jsonify({'user': g.current_user}), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    response = jsonify({'message': 'Logged out successfully'})
    response.delete_cookie('jwt_token')
    return response, 200
