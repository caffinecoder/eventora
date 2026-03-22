

const API = 'https://eventorabackend.onrender.com/api/v1/';

const Auth = {
  getAccess()  { return localStorage.getItem('eventora_access'); },
  getRefresh() { return localStorage.getItem('eventora_refresh'); },
  getUser()    { return JSON.parse(localStorage.getItem('eventora_user') || 'null'); },

  save(access, refresh, user) {
    localStorage.setItem('eventora_access',  access);
    localStorage.setItem('eventora_refresh', refresh);
    localStorage.setItem('eventora_user',    JSON.stringify(user));
  },

  clear() {
    localStorage.removeItem('eventora_access');
    localStorage.removeItem('eventora_refresh');
    localStorage.removeItem('eventora_user');
  },

  isLoggedIn()  { return !!this.getAccess(); },
  isStudent()   { return this.getUser()?.role === 'student'; },
  isAdmin()     { return this.getUser()?.role === 'admin'; },
};

async function apiFetch(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers };

  const token = Auth.getAccess();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  let res = await fetch(`${API}${path}`, { ...options, headers });

  if (res.status === 401 && Auth.getRefresh()) {
    const refreshed = await fetch(`${API}/auth/token/refresh/`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ refresh: Auth.getRefresh() }),
    });

    if (refreshed.ok) {
      const data = await refreshed.json();
      Auth.save(data.access, Auth.getRefresh(), Auth.getUser());
      headers['Authorization'] = `Bearer ${data.access}`;
      res = await fetch(`${API}${path}`, { ...options, headers }); // retry
    } else {
      Auth.clear();
      window.location.href = 'login.html';
      return;
    }
  }

  return res;
}

const api = {
  // Auth
  async login(email, password) {
    return apiFetch('/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  },

  async logout() {
    const res = await apiFetch('/auth/logout/', {
      method: 'POST',
      body: JSON.stringify({ refresh: Auth.getRefresh() }),
    });
    Auth.clear();
    return res;
  },

  async registerStudent(data) {
    return apiFetch('/auth/register/student/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async getProfile() {
    return apiFetch('/auth/profile/');
  },

  // Events
  async getEvents(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return apiFetch(`/events/${qs ? '?' + qs : ''}`);
  },

  async getEventDetail(slug) {
    return apiFetch(`/events/${slug}/`);
  },

  async getCategories() {
    return apiFetch('/events/categories/');
  },

  async getAdminStats() {
    return apiFetch('/events/admin/stats/');
  },

  async getAdminEvents(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return apiFetch(`/events/admin/${qs ? '?' + qs : ''}`);
  },

  async createEvent(data) {
    return apiFetch('/events/admin/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async updateEvent(id, data) {
    return apiFetch(`/events/admin/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  async deleteEvent(id) {
    return apiFetch(`/events/admin/${id}/`, { method: 'DELETE' });
  },

  async updateEventStatus(id, status) {
    return apiFetch(`/events/admin/${id}/status/`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
  },

  // Registrations
  async register(eventId) {
    return apiFetch('/registrations/', {
      method: 'POST',
      body: JSON.stringify({ event: eventId }),
    });
  },

  async getMyRegistrations(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return apiFetch(`/registrations/my/${qs ? '?' + qs : ''}`);
  },

  async cancelRegistration(id) {
    return apiFetch(`/registrations/${id}/cancel/`, { method: 'PATCH' });
  },

  async getAdminRegistrations(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return apiFetch(`/registrations/admin/${qs ? '?' + qs : ''}`);
  },

  // Payments
  async initiatePayment(registrationId, method) {
    return apiFetch('/payments/initiate/', {
      method: 'POST',
      body: JSON.stringify({ registration_id: registrationId, method }),
    });
  },

  async confirmPayment(transactionId, gatewayReference, success) {
    return apiFetch('/payments/confirm/', {
      method: 'POST',
      body: JSON.stringify({ transaction_id: transactionId, gateway_reference: gatewayReference, success }),
    });
  },

  async getMyPayments() {
    return apiFetch('/payments/my/');
  },

  async getAdminPayments(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return apiFetch(`/payments/admin/${qs ? '?' + qs : ''}`);
  },
};

// ── Navbar helper — updates nav based on login state ─────────────────────────
function updateNav() {
  const user = Auth.getUser();
  const loginLink = document.getElementById('nav-login');
  const myRegsLink = document.getElementById('nav-my-regs');
  const logoutBtn = document.getElementById('nav-logout');
  const userNameEl = document.getElementById('nav-username');

  if (user && loginLink) loginLink.style.display = 'none';
  if (user && logoutBtn) logoutBtn.style.display = 'inline-block';
  if (user && userNameEl) userNameEl.textContent = user.full_name.split(' ')[0];
  if (user?.role === 'student' && myRegsLink) myRegsLink.style.display = 'inline';

  if (logoutBtn) {
    logoutBtn.addEventListener('click', async () => {
      await api.logout();
      window.location.href = 'login.html';
    });
  }
}

// ── Toast notification ────────────────────────────────────────────────────────
function showToast(message, type = 'success') {
  const existing = document.getElementById('eventora-toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.id = 'eventora-toast';
  const bg = type === 'error' ? 'rgba(239,68,68,0.15)' : 'rgba(110,231,183,0.12)';
  const border = type === 'error' ? 'rgba(239,68,68,0.4)' : 'rgba(110,231,183,0.3)';
  const color = type === 'error' ? '#f87171' : '#6ee7b7';
  toast.style.cssText = `
    position:fixed; bottom:2rem; right:2rem; z-index:9999;
    background:${bg}; border:1px solid ${border}; color:${color};
    padding:0.85rem 1.25rem; border-radius:12px; font-size:0.875rem;
    font-family:'DM Sans',sans-serif; max-width:320px;
    animation:fadeUp 0.3s ease both; box-shadow:0 8px 32px rgba(0,0,0,0.3);
  `;
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}
