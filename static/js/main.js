/* ==========================================================================
   OFFICE ATTENDANCE SYSTEM - CORE MAIN JS & API UTILITIES
   ========================================================================== */

// Global User & Theme State
window.AppState = {
  user: null,
  theme: localStorage.getItem('theme') || 'light'
};

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  checkAuthSession();
});

// Theme Management
function initTheme() {
  document.documentElement.setAttribute('data-theme', AppState.theme);
  const themeBtn = document.getElementById('theme-toggle-btn');
  if (themeBtn) {
    themeBtn.innerHTML = AppState.theme === 'dark' ? '<i class="ri-sun-line"></i>' : '<i class="ri-moon-line"></i>';
    themeBtn.addEventListener('click', toggleTheme);
  }
}

function toggleTheme() {
  AppState.theme = AppState.theme === 'light' ? 'dark' : 'light';
  localStorage.setItem('theme', AppState.theme);
  document.documentElement.setAttribute('data-theme', AppState.theme);
  
  const themeBtn = document.getElementById('theme-toggle-btn');
  if (themeBtn) {
    themeBtn.innerHTML = AppState.theme === 'dark' ? '<i class="ri-sun-line"></i>' : '<i class="ri-moon-line"></i>';
  }
}

// Authentication Session Manager
async function checkAuthSession() {
  const isLoginPage = window.location.pathname === '/' || window.location.pathname === '/login';
  
  const token = localStorage.getItem('jwt_token');
  if (!token && !isLoginPage) {
    window.location.href = '/login';
    return;
  }
  
  if (token) {
    try {
      const res = await apiFetch('/api/auth/me');
      if (res.user) {
        AppState.user = res.user;
        updateUIWithUser(res.user);
        
        if (isLoginPage) {
          window.location.href = '/dashboard';
        }
      }
    } catch (err) {
      if (!isLoginPage) {
        logoutUser();
      }
    }
  }
}

function updateUIWithUser(user) {
  const userNameEls = document.querySelectorAll('.user-name-display');
  const userRoleEls = document.querySelectorAll('.user-role-display');
  const userAvatarEls = document.querySelectorAll('.user-avatar-display');
  
  userNameEls.forEach(el => el.textContent = user.name);
  userRoleEls.forEach(el => el.textContent = `${user.department} • ${user.role.toUpperCase()}`);
  userAvatarEls.forEach(el => el.textContent = user.name.charAt(0).toUpperCase());
  
  // Show Admin menu items if role == admin, hide if employee
  const adminOnlyEls = document.querySelectorAll('.admin-only');
  adminOnlyEls.forEach(el => {
    el.style.display = user.role === 'admin' ? 'flex' : 'none';
  });
}

// Fetch API Wrapper with Automatic Authorization Headers
async function apiFetch(url, options = {}) {
  const token = localStorage.getItem('jwt_token');
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(url, {
    ...options,
    headers
  });
  
  const data = await response.json();
  
  if (!response.ok) {
    if (response.status === 401 && window.location.pathname !== '/login') {
      logoutUser();
    }
    throw new Error(data.error || 'Request failed');
  }
  
  return data;
}

// Logout Utility
function logoutUser() {
  localStorage.removeItem('jwt_token');
  fetch('/api/auth/logout', { method: 'POST' }).finally(() => {
    window.location.href = '/login';
  });
}

// Toast Notifications System
function showToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }
  
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  
  let icon = 'ri-information-line';
  if (type === 'success') icon = 'ri-checkbox-circle-line';
  if (type === 'danger') icon = 'ri-error-warning-line';
  if (type === 'warning') icon = 'ri-alert-line';
  
  toast.innerHTML = `<i class="${icon}"></i> <span>${message}</span>`;
  container.appendChild(toast);
  
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}
