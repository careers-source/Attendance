/* ==========================================================================
   OFFICE ATTENDANCE SYSTEM - ADMIN PORTAL & ANALYTICS JS
   ========================================================================== */

let monthlyChartInstance = null;
let deptChartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
  if (window.location.pathname === '/dashboard') {
    // If admin role logged in, load admin stats
    setTimeout(() => {
      if (AppState.user && AppState.user.role === 'admin') {
        initAdminDashboard();
      }
    }, 300);
  }

  if (window.location.pathname === '/employees') {
    loadEmployees();
  }

  if (window.location.pathname === '/attendance') {
    loadGlobalAttendance();
  }

  if (window.location.pathname === '/leaves') {
    loadAdminLeaves();
  }

  if (window.location.pathname === '/reports') {
    initReportsPage();
  }
});

// Admin Dashboard Analytics & Charts
async function initAdminDashboard() {
  const adminStatsSection = document.getElementById('admin-stats-section');
  if (adminStatsSection) adminStatsSection.style.display = 'block';

  try {
    const data = await apiFetch('/api/admin/dashboard-stats');
    
    // Update summary stat cards
    document.getElementById('admin-total-employees').textContent = data.total_employees;
    document.getElementById('admin-present-today').textContent = data.today_stats.present_today || 0;
    document.getElementById('admin-late-today').textContent = data.today_stats.late_today || 0;
    document.getElementById('admin-pending-leaves').textContent = data.pending_leaves_count || 0;

    renderCharts(data.monthly_chart_data, data.dept_chart_data);
  } catch (err) {
    showToast(err.message, 'danger');
  }
}

function renderCharts(monthlyData, deptData) {
  const monthlyCanvas = document.getElementById('monthlyAttendanceChart');
  const deptCanvas = document.getElementById('deptDistributionChart');

  if (monthlyCanvas && window.Chart) {
    if (monthlyChartInstance) monthlyChartInstance.destroy();
    
    const labels = Object.keys(monthlyData);
    const values = Object.values(monthlyData);

    monthlyChartInstance = new Chart(monthlyCanvas, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: values,
          backgroundColor: ['#10b981', '#f59e0b', '#0ea5e9', '#ef4444', '#6366f1'],
          borderWidth: 2,
          borderColor: 'transparent'
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 12, font: { family: 'Plus Jakarta Sans' } } }
        }
      }
    });
  }

  if (deptCanvas && window.Chart) {
    if (deptChartInstance) deptChartInstance.destroy();

    const labels = Object.keys(deptData);
    const values = Object.values(deptData);

    deptChartInstance = new Chart(deptCanvas, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Employees',
          data: values,
          backgroundColor: '#4f46e5',
          borderRadius: 8
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, ticks: { precision: 0 } }
        }
      }
    });
  }
}

// Employee CRUD Management
async function loadEmployees() {
  const search = document.getElementById('emp-search-input')?.value || '';
  const dept = document.getElementById('emp-dept-filter')?.value || '';

  try {
    const data = await apiFetch(`/api/admin/employees?search=${encodeURIComponent(search)}&department=${encodeURIComponent(dept)}`);
    const tbody = document.getElementById('employees-tbody');
    if (!tbody) return;

    tbody.innerHTML = '';
    if (data.employees.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">No employees found.</td></tr>`;
      return;
    }

    data.employees.forEach(emp => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>${emp.employee_id}</strong></td>
        <td>
          <div class="d-flex align-items-center gap-2">
            <div class="user-avatar" style="width:32px;height:32px;font-size:0.8rem;">${emp.name.charAt(0)}</div>
            <div>
              <div class="fw-bold">${emp.name}</div>
              <div class="text-muted" style="font-size:0.78rem;">${emp.email}</div>
            </div>
          </div>
        </td>
        <td>${emp.department}</td>
        <td>${emp.designation}</td>
        <td><span class="badge ${emp.role === 'admin' ? 'badge-leave' : 'badge-present'}">${emp.role}</span></td>
        <td>${emp.phone || '--'}</td>
        <td>
          <button class="btn btn-sm btn-outline me-1" onclick="openEditEmployeeModal(${JSON.stringify(emp).replace(/"/g, '&quot;')})"><i class="ri-edit-line"></i></button>
          ${emp.role !== 'admin' ? `<button class="btn btn-sm btn-danger" onclick="deleteEmployee(${emp.id}, '${emp.name}')"><i class="ri-delete-bin-line"></i></button>` : ''}
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    showToast(err.message, 'danger');
  }
}

function openAddEmployeeModal() {
  document.getElementById('add-emp-form').reset();
  openModal('add-employee-modal');
}

async function submitAddEmployee(e) {
  e.preventDefault();
  const payload = {
    employee_id: document.getElementById('new_emp_id').value,
    name: document.getElementById('new_emp_name').value,
    email: document.getElementById('new_emp_email').value,
    password: document.getElementById('new_emp_password').value,
    role: document.getElementById('new_emp_role').value,
    department: document.getElementById('new_emp_dept').value,
    designation: document.getElementById('new_emp_designation').value,
    phone: document.getElementById('new_emp_phone').value
  };

  try {
    const res = await apiFetch('/api/admin/employees', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
    showToast(res.message, 'success');
    closeModal('add-employee-modal');
    loadEmployees();
  } catch (err) {
    showToast(err.message, 'danger');
  }
}

function openEditEmployeeModal(emp) {
  document.getElementById('edit_emp_user_id').value = emp.id;
  document.getElementById('edit_emp_name').value = emp.name;
  document.getElementById('edit_emp_role').value = emp.role;
  document.getElementById('edit_emp_dept').value = emp.department;
  document.getElementById('edit_emp_designation').value = emp.designation;
  document.getElementById('edit_emp_phone').value = emp.phone || '';
  document.getElementById('edit_emp_password').value = '';
  openModal('edit-employee-modal');
}

async function submitEditEmployee(e) {
  e.preventDefault();
  const userId = document.getElementById('edit_emp_user_id').value;
  const payload = {
    name: document.getElementById('edit_emp_name').value,
    role: document.getElementById('edit_emp_role').value,
    department: document.getElementById('edit_emp_dept').value,
    designation: document.getElementById('edit_emp_designation').value,
    phone: document.getElementById('edit_emp_phone').value,
    password: document.getElementById('edit_emp_password').value
  };

  try {
    const res = await apiFetch(`/api/admin/employees/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
    showToast(res.message, 'success');
    closeModal('edit-employee-modal');
    loadEmployees();
  } catch (err) {
    showToast(err.message, 'danger');
  }
}

async function deleteEmployee(id, name) {
  if (!confirm(`Are you sure you want to remove employee "${name}"? This action cannot be undone.`)) return;
  try {
    const res = await apiFetch(`/api/admin/employees/${id}`, { method: 'DELETE' });
    showToast(res.message, 'success');
    loadEmployees();
  } catch (err) {
    showToast(err.message, 'danger');
  }
}

// Global Attendance Monitor
async function loadGlobalAttendance() {
  const dateVal = document.getElementById('global-att-date')?.value || '';
  const searchVal = document.getElementById('global-att-search')?.value || '';
  const deptVal = document.getElementById('global-att-dept')?.value || '';
  const statusVal = document.getElementById('global-att-status')?.value || '';

  try {
    const data = await apiFetch(`/api/admin/attendance?date=${dateVal}&search=${encodeURIComponent(searchVal)}&department=${encodeURIComponent(deptVal)}&status=${encodeURIComponent(statusVal)}`);
    const tbody = document.getElementById('global-attendance-tbody');
    if (!tbody) return;

    tbody.innerHTML = '';
    if (data.attendance.length === 0) {
      tbody.innerHTML = `<tr><td colspan="9" class="text-center py-4 text-muted">No attendance logs found matching filters.</td></tr>`;
      return;
    }

    data.attendance.forEach(att => {
      const tr = document.createElement('tr');
      const statusClass = att.status.toLowerCase().replace(' ', '');
      tr.innerHTML = `
        <td><strong>${att.date}</strong></td>
        <td>${att.employee_id}</td>
        <td><strong>${att.user_name}</strong> <span class="text-muted">(${att.department})</span></td>
        <td>${att.check_in ? att.check_in.split(' ')[1] : '--:--'}</td>
        <td>${att.check_out ? att.check_out.split(' ')[1] : '--:--'}</td>
        <td>${att.break_duration_mins} mins</td>
        <td><strong>${att.net_hours} hrs</strong></td>
        <td><span class="badge badge-${statusClass}">${att.status}</span></td>
        <td>${att.is_late ? '<span class="badge badge-late">Late</span>' : '<span class="text-muted">On Time</span>'}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    showToast(err.message, 'danger');
  }
}

// Admin Leaves Approval Center
async function loadAdminLeaves() {
  const statusVal = document.getElementById('admin-leave-status-filter')?.value || '';
  try {
    const data = await apiFetch(`/api/admin/leaves?status=${encodeURIComponent(statusVal)}`);
    const tbody = document.getElementById('admin-leaves-tbody');
    if (!tbody) return;

    tbody.innerHTML = '';
    if (data.leaves.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">No leave applications found.</td></tr>`;
      return;
    }

    data.leaves.forEach(l => {
      const tr = document.createElement('tr');
      let badgeClass = 'badge-halfday';
      if (l.status === 'Approved') badgeClass = 'badge-present';
      if (l.status === 'Rejected') badgeClass = 'badge-absent';

      tr.innerHTML = `
        <td><strong>${l.employee_id}</strong> - ${l.user_name}</td>
        <td>${l.department}</td>
        <td><span class="badge badge-leave">${l.leave_type}</span></td>
        <td>${l.start_date} to ${l.end_date}</td>
        <td>${l.reason}</td>
        <td><span class="badge ${badgeClass}">${l.status}</span></td>
        <td>
          ${l.status === 'Pending' ? `
            <button class="btn btn-sm btn-success me-1" onclick="processLeaveAction(${l.id}, 'Approved')">Approve</button>
            <button class="btn btn-sm btn-danger" onclick="processLeaveAction(${l.id}, 'Rejected')">Reject</button>
          ` : `<span class="text-muted">${l.admin_remarks || 'Processed'}</span>`}
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    showToast(err.message, 'danger');
  }
}

async function processLeaveAction(leaveId, action) {
  const remarks = prompt(`Enter admin remarks for ${action.toLowerCase()} leave (optional):`) || '';
  try {
    const res = await apiFetch(`/api/admin/leave/${leaveId}/action`, {
      method: 'POST',
      body: JSON.stringify({ action: action, remarks: remarks })
    });
    showToast(res.message, 'success');
    loadAdminLeaves();
  } catch (err) {
    showToast(err.message, 'danger');
  }
}

// Reports & Export Functions
function initReportsPage() {
  const now = new Date();
  const monthStr = now.toISOString().slice(0, 7);
  const monthInput = document.getElementById('report-month-select');
  if (monthInput) monthInput.value = monthStr;
}

function triggerExcelExport() {
  const month = document.getElementById('report-month-select')?.value || '';
  const dept = document.getElementById('report-dept-select')?.value || '';
  const token = localStorage.getItem('jwt_token');

  window.open(`/api/admin/export/excel?month=${month}&department=${encodeURIComponent(dept)}&jwt_token=${token}`, '_blank');
}

function triggerPdfExport() {
  const month = document.getElementById('report-month-select')?.value || '';
  const dept = document.getElementById('report-dept-select')?.value || '';
  const token = localStorage.getItem('jwt_token');

  window.open(`/api/admin/export/pdf?month=${month}&department=${encodeURIComponent(dept)}&jwt_token=${token}`, '_blank');
}

// Modal Helpers
function openModal(modalId) {
  const el = document.getElementById(modalId);
  if (el) el.classList.add('active');
}

function closeModal(modalId) {
  const el = document.getElementById(modalId);
  if (el) el.classList.remove('active');
}
