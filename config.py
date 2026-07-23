import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'office-attendance-super-secret-key-2026')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-attendance-secret-key-2026')
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours in seconds
    
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_PATH = os.path.join(BASE_DIR, 'attendance.db')
    
    # Office Shift Configuration
    SHIFT_START_TIME = '10:00:00'  # 10:00 AM
    SHIFT_END_TIME = '19:00:00'    # 7:00 PM
    GRACE_PERIOD_MINUTES = 15      # Marked late after 10:15 AM
    
    # Standard Break Limits (in minutes)
    MORNING_TEA_MAX_MINS = 15
    LUNCH_MAX_MINS = 60
    AFTERNOON_TEA_MAX_MINS = 15
