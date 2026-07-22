<<<<<<< HEAD
# 🏢 Office Attendance Management System (AttendX.io)

A modern, full-stack, production-ready **Office Attendance Management System** built with **Python (Flask)**, **SQLite**, **HTML5**, **CSS3**, and **JavaScript (ES6)**.

Features secure JWT role-based authentication (`Admin` vs `Employee`), automated check-in/out, multi-break tracking (**Morning Tea**, **Lunch**, **Afternoon Tea**), automated late-mark calculation, leave approval workflow, real-time analytics dashboard with Chart.js, responsive dark mode, and report export engine (**Excel .xlsx & PDF**).

---

## ✨ Features

### 👤 Employee Features
- **JWT Authentication**: Secure login session with role-based routing.
- **Punch Card**: Real-time digital clock with 1-click Check In & Check Out.
- **Automated Late Mark**: Automatically flags check-ins past shift start time (e.g., past 09:15 AM).
- **☕ Break Tracking System**:
  - **Morning Tea Break** (Standard 15 mins)
  - **Lunch Break** (Standard 45 mins)
  - **Afternoon Tea Break** (Standard 15 mins)
  - Live ongoing break timer widget with automatic net working hours deduction.
- **Attendance History**: View past attendance logs with net working hours, break durations, and status badges.
- **Leave Application**: Submit leave requests with reason and date range. Track approval status in real time.
- **Profile & Security**: Update contact details and change account password.

### 🛡️ Admin Features
- **Analytics Dashboard**: Interactive Chart.js visual metrics for monthly attendance distribution and department staff headcounts.
- **Employee CRUD Directory**: Search, add, update, reset password, and remove employee accounts.
- **Global Attendance Monitor**: Filter global attendance records by date, month, department, status, or search query.
- **Leave Approval Center**: Review pending leave applications with custom admin remarks. Approving a leave automatically marks employee attendance as `On Leave`.
- **📊 Reports & Data Exports**:
  - **Excel Export**: Download complete formatted monthly attendance logs as `.xlsx` with column styles and headers.
  - **PDF Export**: Generate clean, printable PDF attendance summary reports.

### 🎨 UI & UX Design
- **Theme Switcher**: Smooth persistent **Dark Mode** & **Light Mode** toggle.
- **Glassmorphic Design**: Modern typography (Plus Jakarta Sans), smooth cards, animated badges, toast notification system.
- **Responsive Layout**: Mobile and desktop friendly sidebar navigation.

---

## 🛠️ Technology Stack

- **Backend**: Python 3, Flask 3.1, Werkzeug (Password hashing with pbkdf2:sha256), PyJWT (JWT tokens).
- **Database**: SQLite 3 (`attendance.db`).
- **Exports**: `openpyxl` (Excel), `reportlab` (PDF).
- **Frontend**: HTML5, Vanilla CSS3 (Custom Design System with CSS variables), Vanilla JavaScript (ES6 Fetch API).
- **Icons & Visuals**: Remixicon CDN, Chart.js CDN.

---

## 🚀 Quick Start & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/office-attendance-system.git
cd office-attendance-system
```

### 2. Set Up Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Seed Database with Initial Data
```bash
python seed.py
```

### 5. Run the Application
```bash
python app.py
```
Open your browser and navigate to: `http://127.0.0.1:5000`

---

## 🔑 Default Credentials (Seed Data)

| Role | Email | Password | Employee ID | Department |
| :--- | :--- | :--- | :--- | :--- |
| **Admin** | `admin@office.com` | `Admin@123` | ADM001 | Management |
| **Employee 1** | `emp1@office.com` | `Emp@123` | EMP001 | Engineering |
| **Employee 2** | `emp2@office.com` | `Emp@123` | EMP002 | Marketing |
| **Employee 3** | `emp3@office.com` | `Emp@123` | EMP003 | Human Resources |

---

## 📁 Project Structure

```
Attendence/
├── app.py                  # Main Flask application & routes controller
├── config.py               # Application settings, secrets, shift configuration
├── db.py                   # SQLite connection & schema initialization
├── seed.py                 # Initial data seeding script
├── requirements.txt        # Python dependency list
├── .gitignore              # Git ignore rules for Python & SQLite
├── README.md               # Project documentation
├── routes/
│   ├── auth.py             # JWT login, logout, profile API
│   ├── employee.py         # Check-in, check-out, break tracking, leaves API
│   ├── admin.py            # Employee CRUD, global logs, leave approvals API
│   └── reports.py          # Excel (.xlsx) and PDF export engine API
├── static/
│   ├── css/
│   │   └── style.css       # Core CSS design system, dark mode, responsive grid
│   └── js/
│       ├── main.js         # Theme manager, JWT fetch wrapper, notifications
│       ├── employee.js     # Punch card & live break timer logic
│       └── admin.js        # Admin analytics, Chart.js, employee modals
└── templates/
    ├── base.html           # Master layout template with topbar & sidebar
    ├── login.html          # Glassmorphism login portal
    ├── dashboard.html      # Role-based dashboard (Admin/Employee)
    ├── attendance.html     # Attendance logs & global monitor
    ├── leaves.html         # Leave requests & approval center
    ├── employees.html      # Employee management CRUD grid
    ├── reports.html        # Export reports page (Excel & PDF)
    └── profile.html        # User profile & security page
```

---

## 🌐 Deploying to GitHub & Cloud Services

### Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit of Office Attendance System"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/office-attendance-system.git
git push -u origin main
```

### Hosting Recommendations
- **Render / Railway**: Create a new Web Service, connect your GitHub repository, set Build Command to `pip install -r requirements.txt` and Start Command to `gunicorn app:app` or `python app.py`.
- **PythonAnywhere**: Upload repository files or clone directly via bash terminal, configure WSGI file pointing to `app.py`.

---

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).
=======
# Attendance
>>>>>>> 5d538d1a28a5f6a6b62ecdf4ef730d03e34a9c7b
