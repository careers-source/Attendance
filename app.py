from flask import Flask, render_template, redirect, jsonify, request
from config import Config
from db import init_db
from routes.auth import auth_bp
from routes.employee import employee_bp
from routes.admin import admin_bp
from routes.reports import reports_bp

app = Flask(__name__)
app.config.from_object(Config)

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(employee_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(reports_bp)

# Page Routes (HTML Views)
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard_page():
    return render_template('dashboard.html')

@app.route('/attendance')
def attendance_page():
    return render_template('attendance.html')

@app.route('/leaves')
def leaves_page():
    return render_template('leaves.html')

@app.route('/employees')
def employees_page():
    return render_template('employees.html')

@app.route('/reports')
def reports_page():
    return render_template('reports.html')

@app.route('/profile')
def profile_page():
    return render_template('profile.html')

from seed import seed_database

# Initialize DB & auto-seed when app starts
with app.app_context():
    init_db()
    seed_database()


import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

