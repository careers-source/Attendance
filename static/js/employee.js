/* ==========================================================================
   OFFICE ATTENDANCE SYSTEM - EMPLOYEE PORTAL INTERACTION & BREAK TIMER JS
   ========================================================================== */

let activeBreakTimer = null;
let activeBreakStartTime = null;

document.addEventListener('DOMContentLoaded', () => {
  if (window.location.pathname === '/dashboard' || window.location.pathname === '/attendance') {
    initClock();
    loadEmployeeDashboard();
  }
  
  if (window.location.pathname === '/leaves') {
    loadLeaveHistory();
  }
});

// Digital Clock
function initClock() {
  const clockEl = document.getElementById('live-clock');
  const dateEl = document.getElementById('live-date');
  
  function updateTime() {
    const now = new Date();
    if (clockEl) {
      clockEl.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }
    if (dateEl) {
      dateEl.textContent = now.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
    }
  }
  updateTime();
  setInterval(updateTime, 1000);
}

// Load Dashboard Data
async function loadEmployeeDashboard() {
  try {
    const data = await apiFetch('/api/employee/dashboard-summary');
    renderPunchCard(data.today, data.active_break);
    renderMonthlyStats(data.monthly_stats, data.pending_leaves);
    
    // Load attendance history table if present on page
    if (document.getElementById('attendance-history-tbody')) {
      loadAttendanceHistory();
    }
  } catch (err) {
    showToast(err.message, 'danger');
  }
}

// Render Punch Card (Check In / Check Out & Break Buttons)
function renderPunchCard(todayAtt, activeBreak) {
  const checkInBtn = document.getElementById('btn-checkin');
  const checkOutBtn = document.getElementById('btn-checkout');
  const statusBadge = document.getElementById('today-status-badge');
  const checkInTimeEl = document.getElementById('today-checkin-time');
  const checkOutTimeEl = document.getElementById('today-checkout-time');
  const netHoursEl = document.getElementById('today-net-hours');
  
  const breakControlsContainer = document.getElementById('break-controls-container');
  const activeBreakBox = document.getElementById('active-break-box');
  const activeBreakTitle = document.getElementById('active-break-title');

  // Reset timers
  if (activeBreakTimer) clearInterval(activeBreakTimer);

  if (!todayAtt || !todayAtt.check_in) {
    // Not checked in yet
    if (checkInBtn) checkInBtn.disabled = false;
    if (checkOutBtn) checkOutBtn.disabled = true;
    if (statusBadge) statusBadge.className = 'badge badge-absent', statusBadge.textContent = 'Not Checked In';
    if (checkInTimeEl) checkInTimeEl.textContent = '--:--';
    if (checkOutTimeEl) checkOutTimeEl.textContent = '--:--';
    if (netHoursEl) netHoursEl.textContent = '0.0 hrs';
    if (breakControlsContainer) breakControlsContainer.style.display = 'none';
    if (activeBreakBox) activeBreakBox.style.display = 'none';
  } else {
    // Checked in
    if (checkInBtn) checkInBtn.disabled = true;
    if (checkInTimeEl) checkInTimeEl.textContent = todayAtt.check_in.split(' ')[1] || todayAtt.check_in;
    
    if (todayAtt.check_out) {
      // Checked out already
      if (checkOutBtn) checkOutBtn.disabled = true;
      if (checkOutTimeEl) checkOutTimeEl.textContent = todayAtt.check_out.split(' ')[1] || todayAtt.check_out;
      if (netHoursEl) netHoursEl.textContent = `${todayAtt.net_hours} hrs`;
      if (statusBadge) {
        statusBadge.className = `badge badge-${todayAtt.status.toLowerCase().replace(' ', '')}`;
        statusBadge.textContent = todayAtt.status;
      }
      if (breakControlsContainer) breakControlsContainer.style.display = 'none';
      if (activeBreakBox) activeBreakBox.style.display = 'none';
    } else {
      // Checked in & working
      if (checkOutBtn) checkOutBtn.disabled = false;
      if (checkOutTimeEl) checkOutTimeEl.textContent = 'In Progress...';
      if (netHoursEl) netHoursEl.textContent = 'Counting...';
      if (statusBadge) {
        statusBadge.className = `badge badge-${todayAtt.status.toLowerCase()}`;
        statusBadge.textContent = todayAtt.status;
      }
      
      if (activeBreak) {
        // Break in progress!
        if (breakControlsContainer) breakControlsContainer.style.display = 'none';
        if (activeBreakBox) activeBreakBox.style.display = 'block';
        if (activeBreakTitle) activeBreakTitle.textContent = `${activeBreak.break_type.replace('_', ' ').toUpperCase()} IN PROGRESS`;
        
        activeBreakStartTime = new Date(activeBreak.start_time.replace(' ', 'T'));
        startActiveBreakTimer();
      } else {
        // Ready for break
        if (breakControlsContainer) breakControlsContainer.style.display = 'flex';
        if (activeBreakBox) activeBreakBox.style.display = 'none';
      }
    }
  }
}

// Live Ongoing Break Timer Counter
function startActiveBreakTimer() {
  const timerDisplay = document.getElementById('active-break-timer-display');
  function tick() {
    const now = new Date();
    const diffSecs = Math.floor((now - activeBreakStartTime) / 1000);
    const mins = Math.floor(diffSecs / 60).toString().padStart(2, '0');
    const secs = (diffSecs % 60).toString().padStart(2, '0');
    if (timerDisplay) timerDisplay.textContent = `${mins}:${secs}`;
  }
  tick();
  activeBreakTimer = setInterval(tick, 1000);
}

// Monthly Summary Stats
function renderMonthlyStats(stats, pendingLeaves) {
  const presentEl = document.getElementById('stat-present-days');
  const lateEl = document.getElementById('stat-late-days');
  const hoursEl = document.getElementById('stat-total-hours');
  const leavesEl = document.getElementById('stat-pending-leaves');

  if (presentEl) presentEl.textContent = stats.present_days || 0;
  if (lateEl) lateEl.textContent = stats.late_days || 0;
  if (hoursEl) hoursEl.textContent = `${(stats.total_net_hours || 0).toFixed(1)}h`;
  if (leavesEl) leavesEl.textContent = pendingLeaves || 0;
}

// Check In Trigger
async function handleCheckIn() {
  try {
    const res = await apiFetch('/api/employee/check-in', { method: 'POST' });
    showToast(res.message, res.is_late ? 'warning' : 'success');
    loadEmployeeDashboard();
  } catch (err) {
    showToast(err.message, 'danger');
  }
}

// Check Out Trigger
async function handleCheckOut() {
  if (!confirm('Are you sure you want to check out for today?')) return;
  try {
    const res = await apiFetch('/api/employee/check-out', { method: 'POST' });
    showToast(res.message, 'success');
    loadEmployeeDashboard();
  } catch (err) {
    showToast(err.message, 'danger');
  }
}

// Start Break Trigger
async function handleStartBreak(breakType) {
  try {
    const res = await apiFetch('/api/employee/break/start', {
      method: 'POST',
      body: JSON.stringify({ break_type: breakType })
    });
    showToast(res.message, 'info');
    loadEmployeeDashboard();
  } catch (err) {
    showToast(err.message, 'danger');
  }
}

// End Break Trigger
async function handleEndBreak() {
  try {
    const res = await apiFetch('/api/employee/break/end', { method: 'POST' });
    showToast(res.message, 'success');
    loadEmployeeDashboard();
  } catch (err) {
    showToast(err.message, 'danger');
  }
}

// Attendance History Loader
async function loadAttendanceHistory() {
  const monthInput = document.getElementById('history-month-filter');
  const month = monthInput ? monthInput.value : new Date().toISOString().slice(0, 7);
  
  try {
    const res = await apiFetch(`/api/employee/history?month=${month}`);
    const tbody = document.getElementById('attendance-history-tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    if (res.history.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">No attendance records found for ${month}</td></tr>`;
      return;
    }
    
    res.history.forEach(item => {
      const tr = document.createElement('tr');
      const statusClass = item.status.toLowerCase().replace(' ', '');
      tr.innerHTML = `
        <td><strong>${item.date}</strong></td>
        <td>${item.check_in ? item.check_in.split(' ')[1] : '--:--'}</td>
        <td>${item.check_out ? item.check_out.split(' ')[1] : '--:--'}</td>
        <td>${item.break_duration_mins} mins (${item.break_count} breaks)</td>
        <td><strong>${item.net_hours} hrs</strong></td>
        <td><span class="badge badge-${statusClass}">${item.status}</span></td>
        <td>${item.is_late ? '<span class="badge badge-late">Late</span>' : '<span class="text-muted">On Time</span>'}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    showToast(err.message, 'danger');
  }
}

// Leave Application & History
async function loadLeaveHistory() {
  try {
    const res = await apiFetch('/api/employee/leave/history');
    const tbody = document.getElementById('leave-history-tbody');
    if (!tbody) return;

    tbody.innerHTML = '';
    if (res.leaves.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">No leave requests found.</td></tr>`;
      return;
    }

    res.leaves.forEach(item => {
      const tr = document.createElement('tr');
      let badgeClass = 'badge-halfday';
      if (item.status === 'Approved') badgeClass = 'badge-present';
      if (item.status === 'Rejected') badgeClass = 'badge-absent';

      tr.innerHTML = `
        <td><strong>${item.leave_type}</strong></td>
        <td>${item.start_date} to ${item.end_date}</td>
        <td>${item.reason}</td>
        <td><span class="badge ${badgeClass}">${item.status}</span></td>
        <td>${item.admin_remarks || '<span class="text-muted">None</span>'}</td>
        <td>${item.created_at ? item.created_at.split(' ')[0] : ''}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    showToast(err.message, 'danger');
  }
}

async function submitLeaveForm(e) {
  e.preventDefault();
  const leave_type = document.getElementById('leave_type').value;
  const start_date = document.getElementById('start_date').value;
  const end_date = document.getElementById('end_date').value;
  const reason = document.getElementById('reason').value;

  try {
    const res = await apiFetch('/api/employee/leave/apply', {
      method: 'POST',
      body: JSON.stringify({ leave_type, start_date, end_date, reason })
    });
    showToast(res.message, 'success');
    closeModal('apply-leave-modal');
    loadLeaveHistory();
  } catch (err) {
    showToast(err.message, 'danger');
  }
}
