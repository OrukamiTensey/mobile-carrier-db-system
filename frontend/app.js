/**
 * Mobile Operator Database - Frontend Application
 */

const API_BASE = '/api';

// ============================================
// State Management
// ============================================
const state = {
    currentSection: 'subscribers',
    subscribers: [],
    delayedPayments: [],
    serviceRequests: [],
    selectedColumns: ['ric_number', 'full_name', 'phone_model', 'service_type', 'monthly_cost', 'is_active'],
    editingSubscriberId: null
};

// ============================================
// Utility Functions
// ============================================
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-times-circle',
        warning: 'fa-exclamation-circle',
        info: 'fa-info-circle'
    };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <i class="fas ${icons[type]} toast-icon"></i>
        <span class="toast-message">${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">&times;</button>
    `;

    container.appendChild(toast);
    setTimeout(() => toast.remove(), 5000);
}

async function apiRequest(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Помилка сервера' }));
            throw new Error(error.detail || 'Помилка запиту');
        }

        if (response.status === 204) return null;
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

function formatDate(dateString) {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('uk-UA');
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('uk-UA', {
        style: 'currency',
        currency: 'UAH'
    }).format(amount || 0);
}

// ============================================
// Navigation
// ============================================
function initNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const section = item.dataset.section;
            navigateTo(section);
        });
    });
}

function navigateTo(section) {
    // Update nav
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.section === section);
    });

    // Update sections
    document.querySelectorAll('.content-section').forEach(sec => {
        sec.classList.remove('active');
    });
    document.getElementById(`${section}Section`).classList.add('active');

    // Update header
    const titles = {
        subscribers: ['Абоненти', 'Управління базою даних абонентів'],
        delayed: ['Затримані платежі', 'Абоненти з простроченими платежами'],
        requests: ['Заявки на обслуговування', 'Управління сервісними заявками'],
        analytics: ['Аналітика', 'Статистика та графи зв\'язків']
    };

    document.getElementById('pageTitle').textContent = titles[section][0];
    document.getElementById('pageSubtitle').textContent = titles[section][1];

    // Update add button visibility
    const addBtn = document.getElementById('addNewBtn');
    if (section === 'subscribers') {
        addBtn.innerHTML = '<i class="fas fa-plus"></i> Додати абонента';
        addBtn.onclick = () => openSubscriberModal();
    } else if (section === 'requests') {
        addBtn.innerHTML = '<i class="fas fa-plus"></i> Нова заявка';
        addBtn.onclick = () => openRequestModal();
    } else {
        addBtn.style.display = section === 'delayed' || section === 'analytics' ? 'none' : '';
    }
    addBtn.style.display = (section === 'subscribers' || section === 'requests') ? '' : 'none';

    state.currentSection = section;
    loadSectionData(section);
}

// ============================================
// Column Selector
// ============================================
function initColumnSelector() {
    const allColumns = [
        { id: 'id', label: 'ID' },
        { id: 'ric_number', label: 'RIC номер' },
        { id: 'pin_code', label: 'PIN-код' },
        { id: 'full_name', label: 'ПІБ' },
        { id: 'phone_model', label: 'Модель телефону' },
        { id: 'phone_type', label: 'Тип телефону' },
        { id: 'service_type', label: 'Вид обслуговування' },
        { id: 'contract_duration_months', label: 'Тривалість контракту' },
        { id: 'contract_start_date', label: 'Дата початку' },
        { id: 'monthly_cost', label: 'Вартість/міс' },
        { id: 'is_active', label: 'Активний' }
    ];

    const grid = document.getElementById('columnsGrid');
    grid.innerHTML = allColumns.map(col => `
        <label class="column-checkbox">
            <input type="checkbox" value="${col.id}" 
                   ${state.selectedColumns.includes(col.id) ? 'checked' : ''}>
            <span>${col.label}</span>
        </label>
    `).join('');

    document.getElementById('applyColumnsBtn').addEventListener('click', () => {
        state.selectedColumns = Array.from(
            document.querySelectorAll('#columnsGrid input:checked')
        ).map(cb => cb.value);

        if (state.selectedColumns.length === 0) {
            showToast('Виберіть хоча б одну колонку', 'warning');
            return;
        }

        loadSubscribers();
    });
}

// ============================================
// Subscribers
// ============================================
async function loadSubscribers() {
    try {
        const data = await apiRequest('/subscribers/by-columns', {
            method: 'POST',
            body: JSON.stringify({ columns: state.selectedColumns })
        });

        state.subscribers = data;
        renderSubscribersTable(data);
    } catch (error) {
        // Fallback to regular endpoint
        try {
            const data = await apiRequest('/subscribers/');
            state.subscribers = data;
            renderSubscribersTable(data);
        } catch (err) {
            showToast('Не вдалося завантажити абонентів', 'error');
            renderSubscribersTable([]);
        }
    }
}

function renderSubscribersTable(data) {
    const columnLabels = {
        id: 'ID',
        ric_number: 'RIC номер',
        pin_code: 'PIN',
        full_name: 'ПІБ',
        phone_model: 'Модель',
        phone_type: 'Тип',
        service_type: 'Обслуговування',
        contract_duration_months: 'Контракт (міс)',
        contract_start_date: 'Початок',
        monthly_cost: 'Вартість',
        is_active: 'Статус'
    };

    // Header
    const header = document.getElementById('tableHeader');
    header.innerHTML = state.selectedColumns.map(col =>
        `<th>${columnLabels[col] || col}</th>`
    ).join('') + '<th>Дії</th>';

    // Body
    const body = document.getElementById('tableBody');

    if (data.length === 0) {
        body.innerHTML = `
            <tr>
                <td colspan="${state.selectedColumns.length + 1}" class="empty-state">
                    <i class="fas fa-users"></i>
                    <p>Немає даних для відображення</p>
                </td>
            </tr>
        `;
    } else {
        body.innerHTML = data.map(row => `
            <tr>
                ${state.selectedColumns.map(col => {
            let value = row[col];
            if (col === 'is_active') {
                value = value ? '<span class="badge badge-success">Активний</span>' : '<span class="badge badge-danger">Неактивний</span>';
            } else if (col === 'monthly_cost') {
                value = formatCurrency(value);
            } else if (col === 'contract_start_date') {
                value = formatDate(value);
            } else if (col === 'service_type') {
                const types = { prepaid: 'Передплата', postpaid: 'Контракт', corporate: 'Корпоративний' };
                value = types[value] || value || '-';
            } else if (col === 'phone_type') {
                const types = { smartphone: 'Смартфон', feature_phone: 'Кнопковий', tablet: 'Планшет' };
                value = types[value] || value || '-';
            }
            return `<td>${value ?? '-'}</td>`;
        }).join('')}
                <td>
                    <div class="table-actions">
                        <button class="btn btn-sm btn-secondary btn-icon" title="Редагувати" 
                                onclick="editSubscriber(${row.id || 0})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-danger btn-icon" title="Видалити"
                                onclick="deleteSubscriber(${row.id || 0})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    document.getElementById('recordCount').textContent = `${data.length} записів`;
}

// ============================================
// Delayed Payments
// ============================================
async function loadDelayedPayments() {
    try {
        const data = await apiRequest('/subscribers/delayed-payments');
        state.delayedPayments = data;
        renderDelayedTable(data);
    } catch (error) {
        showToast('Не вдалося завантажити затримані платежі', 'error');
        renderDelayedTable([]);
    }
}

function renderDelayedTable(data) {
    const body = document.getElementById('delayedBody');

    if (data.length === 0) {
        body.innerHTML = `
            <tr>
                <td colspan="7" class="empty-state">
                    <i class="fas fa-check-circle"></i>
                    <p>Немає затриманих платежів</p>
                </td>
            </tr>
        `;
    } else {
        body.innerHTML = data.map(row => `
            <tr>
                <td><strong>${row.ric_number}</strong></td>
                <td>${row.full_name}</td>
                <td>${row.phone_model || '-'}</td>
                <td><span class="badge badge-danger">${formatCurrency(row.amount)}</span></td>
                <td><span class="badge badge-warning">${row.delay_days} днів</span></td>
                <td><span class="badge badge-danger">${formatDate(row.disconnection_date)}</span></td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="createRequestFromDelayed('${row.ric_number}', '${row.phone_model || ''}')">
                        <i class="fas fa-clipboard-list"></i> Заявка
                    </button>
                </td>
            </tr>
        `).join('');
    }
}

// ============================================
// Service Requests
// ============================================
async function loadServiceRequests(filter = 'all') {
    try {
        let endpoint = '/service-requests/';
        if (filter === 'pending') endpoint = '/service-requests/pending';

        const data = await apiRequest(endpoint);

        if (filter !== 'all' && filter !== 'pending') {
            state.serviceRequests = data.filter(r => r.status === filter);
        } else {
            state.serviceRequests = data;
        }

        renderRequestsGrid(state.serviceRequests);
    } catch (error) {
        showToast('Не вдалося завантажити заявки', 'error');
        renderRequestsGrid([]);
    }
}

function renderRequestsGrid(data) {
    const grid = document.getElementById('requestsGrid');

    const typeLabels = {
        repair: 'Ремонт',
        replacement: 'Заміна',
        activation: 'Активація',
        deactivation: 'Деактивація',
        maintenance: 'Технічне обслуговування'
    };

    const statusBadges = {
        pending: '<span class="badge badge-warning">Очікує</span>',
        in_progress: '<span class="badge badge-info">В процесі</span>',
        completed: '<span class="badge badge-success">Завершено</span>',
        cancelled: '<span class="badge badge-danger">Скасовано</span>'
    };

    if (data.length === 0) {
        grid.innerHTML = `
            <div class="card empty-state" style="grid-column: 1/-1">
                <i class="fas fa-clipboard-list"></i>
                <p>Немає заявок для відображення</p>
            </div>
        `;
    } else {
        grid.innerHTML = data.map(req => `
            <div class="request-card">
                <div class="request-header">
                    <div>
                        <div class="request-type">${typeLabels[req.request_type] || req.request_type}</div>
                        <div class="request-ric">RIC: ${req.ric_number}</div>
                    </div>
                    ${statusBadges[req.status] || ''}
                </div>
                <dl class="request-details">
                    <dt>Модель:</dt>
                    <dd>${req.phone_model}</dd>
                    <dt>Контракт:</dt>
                    <dd>${req.has_contract ? 'Так' : 'Ні'}</dd>
                    ${req.connection_date ? `<dt>Підключення:</dt><dd>${formatDate(req.connection_date)}</dd>` : ''}
                    ${req.disconnection_date ? `<dt>Відключення:</dt><dd>${formatDate(req.disconnection_date)}</dd>` : ''}
                </dl>
                <div class="request-footer">
                    <span class="request-date">${formatDate(req.created_at)}</span>
                    <select class="btn btn-sm btn-secondary" onchange="updateRequestStatus('${req._id || req.id}', this.value)">
                        <option value="pending" ${req.status === 'pending' ? 'selected' : ''}>Очікує</option>
                        <option value="in_progress" ${req.status === 'in_progress' ? 'selected' : ''}>В процесі</option>
                        <option value="completed" ${req.status === 'completed' ? 'selected' : ''}>Завершено</option>
                        <option value="cancelled" ${req.status === 'cancelled' ? 'selected' : ''}>Скасовано</option>
                    </select>
                </div>
            </div>
        `).join('');
    }
}

async function updateRequestStatus(requestId, status) {
    try {
        await apiRequest(`/service-requests/${requestId}/status`, {
            method: 'PATCH',
            body: JSON.stringify({ status })
        });
        showToast('Статус оновлено', 'success');
    } catch (error) {
        showToast('Помилка оновлення статусу', 'error');
    }
}

// ============================================
// Analytics
// ============================================
async function loadAnalytics() {
    try {
        // Load stats
        const subscribers = await apiRequest('/subscribers/').catch(() => []);
        const delayed = await apiRequest('/subscribers/delayed-payments').catch(() => []);
        const pendingReqs = await apiRequest('/service-requests/pending').catch(() => []);
        const plans = await apiRequest('/analytics/service-plans').catch(() => []);

        document.getElementById('totalSubscribers').textContent = subscribers.length;
        document.getElementById('delayedCount').textContent = delayed.length;
        document.getElementById('pendingRequests').textContent = pendingReqs.length;
        document.getElementById('plansCount').textContent = plans.length;

        // Render plans
        const plansList = document.getElementById('plansList');
        plansList.innerHTML = plans.map(plan => `
            <div class="plan-item">
                <div class="plan-name">${plan.name}</div>
                <div class="plan-cost">${plan.cost}<span> грн/міс</span></div>
                <div class="plan-features">${plan.data_gb} GB, ${plan.minutes === -1 ? '∞' : plan.minutes} хв</div>
            </div>
        `).join('') || '<p>Немає тарифних планів (Neo4j не підключено)</p>';

    } catch (error) {
        console.error('Analytics error:', error);
    }
}

// ============================================
// Section Data Loader
// ============================================
function loadSectionData(section) {
    switch (section) {
        case 'subscribers':
            loadSubscribers();
            break;
        case 'delayed':
            loadDelayedPayments();
            break;
        case 'requests':
            loadServiceRequests();
            break;
        case 'analytics':
            loadAnalytics();
            break;
    }
}

// ============================================
// Modals
// ============================================
function openSubscriberModal(subscriberId = null) {
    const modal = document.getElementById('subscriberModal');
    const form = document.getElementById('subscriberForm');
    const title = document.getElementById('modalTitle');

    form.reset();
    state.editingSubscriberId = subscriberId;

    if (subscriberId) {
        title.textContent = 'Редагувати абонента';
        // Load subscriber data
        apiRequest(`/subscribers/${subscriberId}`).then(data => {
            Object.keys(data).forEach(key => {
                const input = form.elements[key];
                if (input) input.value = data[key] || '';
            });
        });
    } else {
        title.textContent = 'Новий абонент';
        form.elements.contract_start_date.value = new Date().toISOString().split('T')[0];
    }

    modal.classList.add('active');
}

function closeSubscriberModal() {
    document.getElementById('subscriberModal').classList.remove('active');
    state.editingSubscriberId = null;
}

function openRequestModal(ricNumber = '', phoneModel = '') {
    const modal = document.getElementById('requestModal');
    const form = document.getElementById('requestForm');

    form.reset();
    form.elements.ric_number.value = ricNumber;
    form.elements.phone_model.value = phoneModel;

    modal.classList.add('active');
}

function closeRequestModal() {
    document.getElementById('requestModal').classList.remove('active');
}

function createRequestFromDelayed(ricNumber, phoneModel) {
    openRequestModal(ricNumber, phoneModel);
}

// ============================================
// Form Handlers
// ============================================
async function handleSubscriberSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    // Convert types
    data.contract_duration_months = parseInt(data.contract_duration_months) || 12;
    data.monthly_cost = parseFloat(data.monthly_cost) || 0;

    try {
        if (state.editingSubscriberId) {
            await apiRequest(`/subscribers/${state.editingSubscriberId}`, {
                method: 'PUT',
                body: JSON.stringify(data)
            });
            showToast('Абонента оновлено', 'success');
        } else {
            await apiRequest('/subscribers/', {
                method: 'POST',
                body: JSON.stringify(data)
            });
            showToast('Абонента створено', 'success');
        }

        closeSubscriberModal();
        loadSubscribers();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function handleRequestSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    data.has_contract = form.elements.has_contract.checked;
    data.service_duration_hours = parseFloat(data.service_duration_hours) || 0;

    try {
        await apiRequest('/service-requests/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        showToast('Заявку створено', 'success');
        closeRequestModal();
        loadServiceRequests();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function editSubscriber(id) {
    if (!id) return;
    openSubscriberModal(id);
}

async function deleteSubscriber(id) {
    if (!id) return;
    if (!confirm('Ви впевнені, що хочете видалити цього абонента?')) return;

    try {
        await apiRequest(`/subscribers/${id}`, { method: 'DELETE' });
        showToast('Абонента видалено', 'success');
        loadSubscribers();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// ============================================
// Search
// ============================================
function initSearch() {
    const input = document.getElementById('searchInput');
    let debounceTimeout;

    input.addEventListener('input', (e) => {
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(async () => {
            const query = e.target.value.trim();
            if (query.length < 2) {
                loadSubscribers();
                return;
            }

            try {
                const data = await apiRequest(`/subscribers/search?q=${encodeURIComponent(query)}`);
                renderSubscribersTable(data);
            } catch (error) {
                console.error('Search error:', error);
            }
        }, 300);
    });
}

// ============================================
// Filter Buttons
// ============================================
function initFilters() {
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            loadServiceRequests(btn.dataset.filter);
        });
    });
}

// ============================================
// Database Status Check
// ============================================
async function checkDatabaseStatus() {
    const pgStatus = document.getElementById('pgStatus');
    const neo4jStatus = document.getElementById('neo4jStatus');
    const couchStatus = document.getElementById('couchStatus');

    // Check PostgreSQL via subscribers endpoint
    try {
        await apiRequest('/subscribers/?limit=1');
        pgStatus.classList.add('connected');
    } catch {
        pgStatus.classList.add('error');
    }

    // Check Neo4j via analytics endpoint
    try {
        await apiRequest('/analytics/service-plans');
        neo4jStatus.classList.add('connected');
    } catch {
        neo4jStatus.classList.add('error');
    }

    // Check CouchDB via service requests endpoint
    try {
        await apiRequest('/service-requests/?limit=1');
        couchStatus.classList.add('connected');
    } catch {
        couchStatus.classList.add('error');
    }
}

// ============================================
// Initialize Application
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initColumnSelector();
    initSearch();
    initFilters();

    // Modal handlers
    document.getElementById('closeModal').addEventListener('click', closeSubscriberModal);
    document.getElementById('cancelBtn').addEventListener('click', closeSubscriberModal);
    document.getElementById('closeRequestModal').addEventListener('click', closeRequestModal);
    document.getElementById('cancelRequestBtn').addEventListener('click', closeRequestModal);

    // Form handlers
    document.getElementById('subscriberForm').addEventListener('submit', handleSubscriberSubmit);
    document.getElementById('requestForm').addEventListener('submit', handleRequestSubmit);

    // Close modal on outside click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });

    // Load initial data
    loadSectionData('subscribers');
    checkDatabaseStatus();
});
