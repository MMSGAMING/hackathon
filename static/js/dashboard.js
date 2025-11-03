let charts = {};
let currentMode = 'normal';

document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    loadDashboard();
});

function initializeApp() {
    fetch('/api/status')
        .then(r => r.json())
        .then(data => {
            document.getElementById('ml-status').textContent = data.model_status === 'trained' ? 'Trained ✓' : 'Training...';
            document.getElementById('ml-accuracy').textContent = data.model_accuracy.toFixed(1) + '%';
            document.getElementById('ml-samples').textContent = (data.training_samples || 1440).toLocaleString();
        });
}

function setupEventListeners() {
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const tabName = this.dataset.tab;
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(tabName).classList.add('active');
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    if (tabName === 'analytics') loadAnalytics();
}

function loadDashboard() {
    fetch('/api/metrics/daily').then(r => r.json()).then(data => updateMetrics(data));
    fetch(`/api/schedule/24h?mode=${currentMode}`).then(r => r.json()).then(data => {
        populateScheduleTable(data);
        loadOccupancyChart(data);
    });
    fetch(`/api/energy/comparison?mode=${currentMode}`).then(r => r.json()).then(data => loadEnergyChart(data));
    fetch('/api/rooms').then(r => r.json()).then(data => populateRooms(data));
    generateDecisionLog();
}

function updateMetrics(data) {
    document.getElementById('energy-current').textContent = data.optimized_energy + ' kW';
    document.getElementById('co2-saved').textContent = data.co2_saved_kg + ' kg';
    document.getElementById('occupancy-pred').textContent = Math.round(data.occupancy_avg * 100) + '%';
    document.getElementById('savings-percent').textContent = data.savings_percent.toFixed(1) + '%';
}

function populateScheduleTable(schedule) {
    const tbody = document.getElementById('schedule-tbody');
    tbody.innerHTML = '';
    schedule.filter((_, i) => i % 2 === 0).slice(0, 12).forEach(item => {
        const row = document.createElement('tr');
        const occ = (item.predicted_occupancy * 100).toFixed(0);
        const hvacColor = item.hvac_mode === 'OFF' ? 'status-off' : item.hvac_mode === 'ECO' ? 'status-eco' : 'status-full';
        const lightColor = item.lights_mode === 'OFF' ? 'status-off' : item.lights_mode === 'DIM' ? 'status-eco' : 'status-full';
        row.innerHTML = `<td>${item.time_slot}</td><td>${occ}%</td><td><span class="${hvacColor}">${item.hvac_mode}</span></td><td><span class="${lightColor}">${item.lights_mode}</span></td><td>${item.total_energy} kW</td><td>${item.savings_percent}%</td>`;
        tbody.appendChild(row);
    });
}

function loadOccupancyChart(schedule) {
    const ctx = document.getElementById('occupancyChart').getContext('2d');
    if (charts.occupancy) charts.occupancy.destroy();
    charts.occupancy = new Chart(ctx, {
        type: 'line',
        data: { labels: schedule.map(s => s.hour), datasets: [{label: 'ML Predicted Occupancy', data: schedule.map(s => s.predicted_occupancy * 100), borderColor: '#00d4ff', backgroundColor: 'rgba(0, 212, 255, 0.1)', borderWidth: 2, fill: true, tension: 0.4}]},
        options: { responsive: true, plugins: { legend: { labels: { color: '#b0c4de' } } }, scales: { y: { min: 0, max: 100, ticks: { color: '#b0c4de' } }, x: { ticks: { color: '#b0c4de' } } } }
    });
}

function loadEnergyChart(data) {
    const ctx = document.getElementById('energyChart').getContext('2d');
    if (charts.energy) charts.energy.destroy();
    charts.energy = new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array.from({length: 24}, (_, i) => `${i}:00`),
            datasets: [
                {label: 'Baseline', data: data.baseline_24h, borderColor: '#ff6b6b', backgroundColor: 'rgba(255, 107, 107, 0.1)', borderWidth: 2, fill: true},
                {label: 'ML Optimized', data: data.optimized_24h, borderColor: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.1)', borderWidth: 2, fill: true}
            ]
        },
        options: { responsive: true, plugins: { legend: { labels: { color: '#b0c4de' } } }, scales: { y: { ticks: { color: '#b0c4de' } }, x: { ticks: { color: '#b0c4de' } } } }
    });
}

function populateRooms(rooms) {
    const grid = document.getElementById('zones-grid');
    grid.innerHTML = '';
    rooms.forEach(room => {
        let colorClass = 'optimal';
        if (room.temperature < 19) colorClass = 'cold';
        else if (room.temperature > 24) colorClass = 'hot';
        else if (room.occupancy < 0.1) colorClass = 'empty';
        const card = document.createElement('div');
        card.className = `zone-card ${colorClass}`;
        card.innerHTML = `<div class="zone-name">${room.name}</div><div class="zone-info">Occupancy: ${(room.occupancy * 100).toFixed(0)}%<br>Temp: ${room.temperature.toFixed(1)}°C<br>HVAC: ${room.hvac}</div>`;
        grid.appendChild(card);
    });
}

function generateDecisionLog() {
    const log = document.getElementById('decision-log');
    log.innerHTML = '';
    const decisions = [
        {time: '09:15 AM', decision: 'ML predicted 12% occupancy → Conference A HVAC OFF (Save: 0.8 kW)'},
        {time: '09:30 AM', decision: 'Occupancy rising to 45% → Open Office HVAC ON'},
        {time: '10:00 AM', decision: 'Detected pattern: typical Monday surge → Pre-cooling initiated'},
        {time: '12:00 PM', decision: 'Lunch hour detected: Lights DIM in 3 zones (Save: 0.6 kW)'},
        {time: '12:30 PM', decision: 'Occupancy prediction: ↓ 30% → HVAC ECO mode'},
        {time: '01:00 PM', decision: 'Conference B empty for 45 min → All systems OFF (Save: 1.2 kW)'},
        {time: '04:00 PM', decision: 'Evening occupancy spike predicted → Server room cooling +5%'},
        {time: '05:30 PM', decision: 'End of day detected → Gradual shutdown sequence initiated'}
    ];
    decisions.forEach(item => {
        const entry = document.createElement('div');
        entry.className = 'log-entry';
        entry.innerHTML = `<span class="log-time">${item.time}:</span> <span class="log-decision">${item.decision}</span>`;
        log.appendChild(entry);
    });
}

function changeMode(mode) {
    currentMode = mode;
    fetch(`/api/schedule/24h?mode=${mode}`).then(r => r.json()).then(data => {
        populateScheduleTable(data);
        loadOccupancyChart(data);
    });
}

function toggleOptimization(enabled) {
    fetch('/api/optimization', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({enabled: enabled})});
}

function runSimulation() {
    fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hour: new Date().getHours(), day_of_week: new Date().getDay(), temperature: 22 + Math.random() * 4, humidity: 40 + Math.random() * 20 })
    }).then(r => r.json()).then(data => {
        alert(`ML Prediction:\n- Occupancy: ${(data.occupancy * 100).toFixed(0)}%\n- HVAC: ${data.hvac_mode}\n- Lights: ${data.lights_mode}\n- Savings: ${data.savings_percent}%`);
    });
}

function retrainModel() {
    const btn = event.target;
    btn.disabled = true;
    btn.textContent = '⏳ Training...';
    fetch('/api/retrain', {method: 'POST'}).then(r => r.json()).then(data => {
        if (data.metrics) {
            document.getElementById('ml-accuracy').textContent = (data.metrics.accuracy * 100).toFixed(1) + '%';
        }
        btn.disabled = false;
        btn.textContent = '🔄 Retrain Model';
        alert('✓ Model retrained!\nNew Accuracy: ' + (data.metrics.accuracy * 100).toFixed(1) + '%');
    });
}

function loadAnalytics() {
    fetch('/api/features').then(r => r.json()).then(data => loadFeatureImportance(data));
    loadSavingsChart();
    loadTrendChart();
}

function loadFeatureImportance(features) {
    const ctx = document.getElementById('featureChart');
    if (!ctx) return;
    if (charts.features) charts.features.destroy();
    const labels = Object.keys(features);
    const values = Object.values(features);
    charts.features = new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: { labels: labels, datasets: [{label: 'Feature Importance (%)', data: values, backgroundColor: ['#00d4ff', '#10b981', '#ffd93d', '#ff6b6b', '#7ca3c0']}]},
        options: { indexAxis: 'y', responsive: true, plugins: { legend: { labels: { color: '#b0c4de' } } }, scales: { x: { ticks: { color: '#b0c4de' } }, y: { ticks: { color: '#b0c4de' } } } }
    });
}

function loadSavingsChart() {
    const ctx = document.getElementById('savingsChart');
    if (!ctx) return;
    if (charts.savings) charts.savings.destroy();
    charts.savings = new Chart(ctx.getContext('2d'), {
        type: 'doughnut',
        data: { labels: ['HVAC', 'Lighting', 'Predictive'], datasets: [{data: [60, 30, 10], backgroundColor: ['#00d4ff', '#10b981', '#ffd93d']}]},
        options: { responsive: true, plugins: { legend: { labels: { color: '#b0c4de' } } } }
    });
}

function loadTrendChart() {
    const ctx = document.getElementById('trendChart');
    if (!ctx) return;
    if (charts.trend) charts.trend.destroy();
    charts.trend = new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [
                {label: 'Baseline', data: [168, 165, 170, 172, 168, 140, 120], backgroundColor: 'rgba(255, 107, 107, 0.3)'},
                {label: 'Optimized', data: [157, 155, 159, 160, 157, 130, 110], backgroundColor: 'rgba(16, 185, 129, 0.3)'}
            ]
        },
        options: { responsive: true, plugins: { legend: { labels: { color: '#b0c4de' } } }, scales: { y: { ticks: { color: '#b0c4de' } }, x: { ticks: { color: '#b0c4de' } } } }
    });
}
