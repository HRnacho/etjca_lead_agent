// ETJCA Lead Generation Agent - Main JavaScript

// Global Variables
let currentProspects = [];
let selectedProspects = [];
let chartInstances = {};

// Document Ready
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    initializeTooltips();
    startAutoRefresh();
});

// Initialize Application
function initializeApp() {
    console.log('ETJCA Lead Generation Agent - Initialized');
    
    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        setTimeout(() => {
            card.classList.add('fade-in');
        }, index * 100);
    });
    
    // Initialize page-specific functions
    const currentPage = window.location.pathname;
    
    switch(currentPage) {
        case '/':
            initializeDashboard();
            break;
        case '/search_prospects':
            initializeSearchPage();
            break;
        case '/select_prospects':
            initializeSelectPage();
            break;
        case '/reports':
            initializeReportsPage();
            break;
        case '/settings':
            initializeSettingsPage();
            break;
    }
}

// Setup Event Listeners
function setupEventListeners() {
    // Sidebar navigation
    const navLinks = document.querySelectorAll('.sidebar .nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Remove active class from all links
            navLinks.forEach(l => l.classList.remove('active'));
            // Add active class to clicked link
            this.classList.add('active');
        });
    });
    
    // Search form submission
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', handleSearch);
    }
    
    // Prospect selection
    const prospectCheckboxes = document.querySelectorAll('.prospect-checkbox');
    prospectCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', handleProspectSelection);
    });
    
    // Bulk actions
    const bulkActionButtons = document.querySelectorAll('.bulk-action-btn');
    bulkActionButtons.forEach(button => {
        button.addEventListener('click', handleBulkAction);
    });
}

// Initialize Tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Auto-refresh Dashboard
function startAutoRefresh() {
    if (window.location.pathname === '/') {
        setInterval(refreshDashboardStats, 60000); // Refresh every minute
    }
}

// Dashboard Functions
function initializeDashboard() {
    refreshDashboardStats();
    loadRecentActivities();
    loadUpcomingAppointments();
}

function refreshDashboardStats() {
    fetch('/api/dashboard_stats')
        .then(response => response.json())
        .then(data => {
            updateStatsCards(data);
        })
        .catch(error => {
            console.error('Error refreshing stats:', error);
        });
}

function updateStatsCards(data) {
    const elements = {
        'total-prospects': data.total_prospects || 0,
        'emails-sent': data.emails_sent || 0,
        'appointments': data.appointments_scheduled || 0,
        'responses': data.responses_received || 0
    };
    
    Object.keys(elements).forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            // Animate number change
            animateNumber(element, parseInt(element.textContent), elements[id]);
        }
    });
}

function animateNumber(element, start, end) {
    const duration = 1000;
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const current = Math.floor(start + (end - start) * progress);
        element.textContent = current;
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

function loadRecentActivities() {
    fetch('/api/recent_activities')
        .then(response => response.json())
        .then(data => {
            updateActivityTimeline(data.activities);
        })
        .catch(error => {
            console.error('Error loading activities:', error);
        });
}

function updateActivityTimeline(activities) {
    const timeline = document.querySelector('.timeline');
    if (!timeline) return;
    
    timeline.innerHTML = '';
    
    activities.forEach(activity => {
        const activityItem = document.createElement('div');
        activityItem.className = 'timeline-item';
        activityItem.innerHTML = `
            <div class="timeline-marker bg-${getActivityColor(activity.type)}"></div>
            <div class="timeline-content">
                <strong>${activity.type}</strong> ${activity.description}
                <small class="text-muted d-block">${formatTimeAgo(activity.timestamp)}</small>
            </div>
        `;
        timeline.appendChild(activityItem);
    });
}

function getActivityColor(type) {
    const colors = {
        'Email': 'primary',
        'Appuntamento': 'success',
        'Anagrafica': 'info',
        'Risposta': 'warning'
    };
    return colors[type] || 'secondary';
}

function formatTimeAgo(timestamp) {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMs = now - time;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 60) {
        return `${diffMins} minuti fa`;
    } else if (diffHours < 24) {
        return `${diffHours} ore fa`;
    } else {
        return `${diffDays} giorni fa`;
    }
}

// Search Functions
function initializeSearchPage() {
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', handleSearch);
    }
}

function handleSearch(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const searchData = {
        source: formData.get('source'),
        keywords: formData.get('keywords'),
        location: formData.get('location')
    };
    
    showLoading('Ricerca in corso...');
    
    fetch('/api/search_prospects', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(searchData)
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        displaySearchResults(data.prospects);
    })
    .catch(error => {
        hideLoading();
        showError('Errore nella ricerca: ' + error.message);
    });
}

function displaySearchResults(prospects) {
    const resultsContainer = document.getElementById('searchResults');
    if (!resultsContainer) return;
    
    resultsContainer.innerHTML = '';
    
    if (prospects.length === 0) {
        resultsContainer.innerHTML = '<p class="text-center text-muted">Nessun prospect trovato</p>';
        return;
    }
    
    prospects.forEach(prospect => {
        const prospectCard = createProspectCard(prospect);
        resultsContainer.appendChild(prospectCard);
    });
}

function createProspectCard(prospect) {
    const card = document.createElement('div');
    card.className = 'prospect-card';
    card.innerHTML = `
        <div class="d-flex justify-content-between align-items-start">
            <div>
                <h6 class="mb-1">${prospect.nome} ${prospect.cognome}</h6>
                <p class="mb-1 text-muted">${prospect.posizione} - ${prospect.azienda}</p>
                <small class="text-muted">${prospect.citta || ''} | ${prospect.fonte}</small>
            </div>
            <div>
                <button class="btn btn-sm btn-outline-primary" onclick="addProspectToDatabase(${JSON.stringify(prospect).replace(/"/g, '&quot;')})">
                    <i class="fas fa-plus"></i> Aggiungi
                </button>
            </div>
        </div>
    `;
    return card;
}

function addProspectToDatabase(prospect) {
    fetch('/api/add_prospect_manual', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(prospect)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccess('Prospect aggiunto con successo!');
        } else {
            showError('Errore nell\'aggiunta del prospect');
        }
    })
    .catch(error => {
        showError('Errore: ' + error.message);
    });
}

// Select Prospects Functions
function initializeSelectPage() {
    loadProspectsList();
    setupBulkActions();
}

function loadProspectsList() {
    fetch('/api/get_prospects')
        .then(response => response.json())
        .then(data => {
            displayProspectsList(data.prospects);
        })
        .catch(error => {
            console.error('Error loading prospects:', error);
        });
}

function displayProspectsList(prospects) {
    const tbody = document.querySelector('#prospectsTable tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    prospects.forEach(prospect => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>
                <input type="checkbox" class="prospect-checkbox" value="${prospect.id}">
            </td>
            <td>${prospect.nome} ${prospect.cognome}</td>
            <td>${prospect.azienda}</td>
            <td>${prospect.posizione || '-'}</td>
            <td>${prospect.email || '-'}</td>
            <td>${prospect.citta || '-'}</td>
            <td><span class="status-badge status-${prospect.stato}">${prospect.stato}</span></td>
            <td>
                <button class="btn btn-sm btn-outline-primary" onclick="viewProspectDetails(${prospect.id})">
                    <i class="fas fa-eye"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function setupBulkActions() {
    const selectAllBtn = document.getElementById('selectAllBtn');
    const deselectAllBtn = document.getElementById('deselectAllBtn');
    const processBtn = document.getElementById('processBtn');
    
    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', selectAllProspects);
    }
    
    if (deselectAllBtn) {
        deselectAllBtn.addEventListener('click', deselectAllProspects);
    }
    
    if (processBtn) {
        processBtn.addEventListener('click', processSelectedProspects);
    }
}

function selectAllProspects() {
    const checkboxes = document.querySelectorAll('.prospect-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = true;
    });
    updateSelectedCount();
}

function deselectAllProspects() {
    const checkboxes = document.querySelectorAll('.prospect-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = false;
    });
    updateSelectedCount();
}

function updateSelectedCount() {
    const selectedCount = document.querySelectorAll('.prospect-checkbox:checked').length;
    const countElement = document.getElementById('selectedCount');
    if (countElement) {
        countElement.textContent = selectedCount;
    }
}

function processSelectedProspects() {
    const selected = Array.from(document.querySelectorAll('.prospect-checkbox:checked'))
        .map(checkbox => checkbox.value);
    
    if (selected.length === 0) {
        showWarning('Seleziona almeno un prospect da processare');
        return;
    }
    
    const actions = getSelectedActions();
    
    if (actions.length === 0) {
        showWarning('Seleziona almeno un\'azione da eseguire');
        return;
    }
    
    const data = {
        prospect_ids: selected,
        actions: actions
    };
    
    showLoading('Processamento in corso...');
    
    fetch('/api/process_selected_prospects', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            showSuccess('Prospect processati con successo!');
            loadProspectsList(); // Refresh the list
        } else {
            showError('Errore nel processamento');
        }
    })
    .catch(error => {
        hideLoading();
        showError('Errore: ' + error.message);
    });
}

function getSelectedActions() {
    const actions = [];
    
    if (document.getElementById('actionAnagrafica')?.checked) {
        actions.push('anagrafica');
    }
    if (document.getElementById('actionEmail')?.checked) {
        actions.push('email');
    }
    if (document.getElementById('actionAttivita')?.checked) {
        actions.push('attivita');
    }
    if (document.getElementById('actionCompleto')?.checked) {
        actions.push('completo');
    }
    
    return actions;
}

// Settings Functions
function initializeSettingsPage() {
    loadCurrentSettings();
    setupSettingsTabs();
}

function loadCurrentSettings() {
    fetch('/api/get_settings')
        .then(response => response.json())
        .then(data => {
            populateSettingsForm(data);
        })
        .catch(error => {
            console.error('Error loading settings:', error);
        });
}

function populateSettingsForm(settings) {
    Object.keys(settings).forEach(key => {
        const input = document.querySelector(`[name="${key}"]`);
        if (input) {
            if (input.type === 'checkbox') {
                input.checked = settings[key];
            } else {
                input.value = settings[key];
            }
        }
    });
}

function setupSettingsTabs() {
    const tabs = document.querySelectorAll('#settingsTabs .nav-link');
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const target = this.getAttribute('data-bs-target');
            localStorage.setItem('activeSettingsTab', target);
        });
    });
    
    // Restore active tab
    const activeTab = localStorage.getItem('activeSettingsTab');
    if (activeTab) {
        const tab = document.querySelector(`[data-bs-target="${activeTab}"]`);
        if (tab) {
            tab.click();
        }
    }
}

// Utility Functions
function showLoading(message = 'Caricamento...') {
    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'loadingOverlay';
    loadingDiv.className = 'position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center';
    loadingDiv.style.backgroundColor = 'rgba(0,0,0,0.5)';
    loadingDiv.style.zIndex = '9999';
    loadingDiv.innerHTML = `
        <div class="text-center text-white">
            <div class="loading-spinner"></div>
            <p class="mt-3">${message}</p>
        </div>
    `;
    document.body.appendChild(loadingDiv);
}

function hideLoading() {
    const loadingDiv = document.getElementById('loadingOverlay');
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

function showSuccess(message) {
    showToast(message, 'success');
}

function showError(message) {
    showToast(message, 'error');
}

function showWarning(message) {
    showToast(message, 'warning');
}

function showToast(message, type = 'info') {
    const toastContainer = getOrCreateToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type === 'warning' ? 'warning' : type === 'success' ? 'success' : 'primary'} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

function getOrCreateToastContainer() {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    return container;
}

// Export functions for global use
window.ETJCA = {
    showLoading,
    hideLoading,
    showSuccess,
    showError,
    showWarning,
    refreshDashboardStats,
    processSelectedProspects,
    addProspectToDatabase
};

// Add Manual Prospect Modal Functions
function showAddProspectModal() {
    const modal = new bootstrap.Modal(document.getElementById('addProspectModal'));
    modal.show();
}

function saveProspect() {
    const form = document.getElementById('addProspectForm');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData);
    
    fetch('/api/add_prospect_manual', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccess('Prospect aggiunto con successo!');
            bootstrap.Modal.getInstance(document.getElementById('addProspectModal')).hide();
            form.reset();
            if (typeof loadProspectsList === 'function') {
                loadProspectsList();
            }
        } else {
            showError('Errore nel salvataggio del prospect');
        }
    })
    .catch(error => {
        showError('Errore nella comunicazione con il server');
        console.error('Error:', error);
    });
}

// Make functions globally available
window.showAddProspectModal = showAddProspectModal;
window.saveProspect = saveProspect;
window.selectAllProspects = selectAllProspects;
window.deselectAllProspects = deselectAllProspects;
window.processSelectedProspects = processSelectedProspects;
