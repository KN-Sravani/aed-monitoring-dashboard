// script.js
let deviceDataStore = [];
let chartInstance = null;
let mapInstance = null;
let mapMarkers = [];

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initSettings();
    initParticles();
    fetchDeviceData();
    
    // Auto-refresh simulation
    setInterval(() => {
        const rate = document.getElementById('refresh-rate').value;
        if (rate !== 'Manual only') {
            fetchDeviceData(true);
        }
    }, rateToMs(document.getElementById('refresh-rate').value));
});

function rateToMs(val) {
    if(val.includes('5')) return 5000;
    if(val.includes('30')) return 30000;
    return 60000;
}

// Navigation Logic
function initNavigation() {
    const navItems = document.querySelectorAll('#nav-list li');
    const views = document.querySelectorAll('.content-view');
    const titleEle = document.getElementById('page-title');
    const subtitleEle = document.getElementById('page-subtitle');

    const titles = {
        'view-dashboard': { t: 'Network Overview', s: 'Real-time trust analysis for AED devices' },
        'view-map': { t: 'Live Map', s: 'Geographical distribution of active AED units' },
        'view-devices': { t: 'Devices Control Grid', s: 'Manage and override individual AED units' },
        'view-alerts': { t: 'Threat Timeline', s: 'Historical log of all detected security risks' },
        'view-settings': { t: 'System Preferences', s: 'Customize interface and operation parameters' }
    };

    navItems.forEach(item => {
        // Accessibility (A11y) keydown support
        item.addEventListener('keydown', (e) => {
            if(e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                item.click();
            }
        });

        item.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Remove active classes & aria-states
            navItems.forEach(nav => {
                nav.classList.remove('active');
                if (nav.querySelector('a')) {
                    nav.querySelector('a').setAttribute('aria-selected', 'false');
                }
            });
            views.forEach(view => {
                view.style.display = 'none';
                view.classList.remove('active-view');
            });
            
            // Activate selected
            item.classList.add('active');
            if (item.querySelector('a')) {
                item.querySelector('a').setAttribute('aria-selected', 'true');
            }
            const targetId = item.getAttribute('data-target');
            const targetView = document.getElementById(targetId);
            
            if(targetView) {
                targetView.style.display = 'block';
                // Trigger reflow for animation
                void targetView.offsetWidth;
                targetView.classList.add('active-view');
            }

            // Lazy initialize map to avoid 0x0 sizing issues with display:none
            if(targetId === 'view-map') {
                if(!mapInstance && deviceDataStore.length > 0) {
                    let avgLat = 0; let avgLon = 0;
                    deviceDataStore.forEach(d => { avgLat += d.latitude; avgLon += d.longitude; });
                    initMap(avgLat/deviceDataStore.length, avgLon/deviceDataStore.length);
                    updateMap(deviceDataStore);
                }
                if(mapInstance) {
                    setTimeout(() => { mapInstance.invalidateSize(); }, 300); // 300ms to allow animations to finish
                }
            }

            // Update Header
            if(titles[targetId]) {
                titleEle.textContent = titles[targetId].t;
                subtitleEle.textContent = titles[targetId].s;
            }
        });
    });
}

// Settings Logic
function initSettings() {
    const cyberToggle = document.getElementById('toggle-theme');
    cyberToggle.addEventListener('change', (e) => {
        if(e.target.checked) {
            document.body.classList.add('cyberpunk-theme');
        } else {
            document.body.classList.remove('cyberpunk-theme');
        }
        if(deviceDataStore.length > 0) {
            updateDashboard(deviceDataStore); // Rerender chart colors
            updateMap(deviceDataStore); // Rerender map markers
        }
    });

    const particleToggle = document.getElementById('toggle-particles');
    particleToggle.addEventListener('change', (e) => {
        document.getElementById('particles').style.display = e.target.checked ? 'block' : 'none';
    });
}

// Map Generation
function initMap(centerLat, centerLon) {
    if(mapInstance) return;

    mapInstance = L.map('map-container').setView([centerLat, centerLon], 14);
    
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap &copy; CARTO',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(mapInstance);
}

function updateMap(devices) {
    if(devices.length === 0 || !mapInstance) return;

    // Clear old markers
    mapMarkers.forEach(m => mapInstance.removeLayer(m));
    mapMarkers = [];

    // Cyberpunk Theme check
    const isCyber = document.body.classList.contains('cyberpunk-theme');

    devices.forEach(device => {
        let color = isCyber ? '#00ff64' : '#00e676'; // Safe
        let status = "Operational";
        if (device.trust_score < 50) {
            color = isCyber ? '#ff003c' : '#ff1e56'; // Danger
            status = "Critical Alert";
        } else if (device.trust_score < 90) {
            color = isCyber ? '#fdf500' : '#ffb74d'; // Warning
            status = "Warning";
        }

        // Custom SVG Marker definition
        const markerSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="${color}" stroke="#000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>`;
        const icon = L.divIcon({
            className: "custom-svg-icon",
            html: markerSvg,
            iconSize: [24, 24],
            iconAnchor: [12, 24],
            popupAnchor: [0, -24]
        });

        // Format relative time 
        const dateObj = new Date(device.last_used);
        const timeDiff = Math.abs(new Date() - dateObj);
        const daysDiff = Math.ceil(timeDiff / (1000 * 60 * 60 * 24)); 
        const lastUsedStr = daysDiff <= 1 ? "Today" : `${daysDiff} days ago`;

        const popupContent = `
            <div class="map-popup-header">
                ${device.device}
                <span style="color:${color}">${device.trust_score}%</span>
            </div>
            <div class="map-popup-detail">Status: <span>${status}</span></div>
            <div class="map-popup-detail">Last Used: <span>${lastUsedStr}</span><br><em style="font-size:0.75rem">(${dateObj.toLocaleDateString()})</em></div>
        `;

        const marker = L.marker([device.latitude, device.longitude], {icon: icon})
            .addTo(mapInstance)
            .bindPopup(popupContent);
        
        mapMarkers.push(marker);
    });
}

// Particle Generation
function initParticles() {
    const container = document.getElementById('particles');
    for(let i=0; i<50; i++) {
        const p = document.createElement('div');
        p.classList.add('particle');
        const size = Math.random() * 4 + 1;
        p.style.width = `${size}px`;
        p.style.height = `${size}px`;
        p.style.left = `${Math.random() * 100}vw`;
        p.style.top = `${Math.random() * 100 + 100}vh`;
        p.style.animationDuration = `${Math.random() * 10 + 5}s`;
        p.style.animationDelay = `${Math.random() * 5}s`;
        container.appendChild(p);
    }
}

// Data Handling
async function fetchDeviceData(silent = false) {
    try {
        const response = await fetch('results.json');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const rawData = await response.json();
        
        deviceDataStore = processData(rawData);
        
        updateDashboard(deviceDataStore);
        updateDevicesView(deviceDataStore);
        if(document.getElementById('view-map').style.display !== 'none') {
            updateMap(deviceDataStore);
        }
        updateAlertsTimeline(rawData); 
    } catch (error) {
        console.error("Could not load device data: ", error);
        if(!silent) document.getElementById('device-table-body').innerHTML = `<tr><td colspan="4" class="danger">Error loading data. Check console.</td></tr>`;
    }
}

window.refreshData = function() {
    fetchDeviceData();
    // Visual feedback
    const btn = document.querySelector('.action-bar .secondary');
    if(btn) {
        const originalText = btn.textContent;
        btn.textContent = "Pinging...";
        setTimeout(() => { btn.textContent = originalText; }, 800);
    }
}

function processData(rawData) {
    const deviceMap = new Map();
    rawData.forEach(entry => {
        if (deviceMap.has(entry.device)) {
            if (entry.trust_score < deviceMap.get(entry.device).trust_score) {
                deviceMap.set(entry.device, entry);
            }
        } else {
            deviceMap.set(entry.device, entry);
        }
    });
    return Array.from(deviceMap.values());
}

// View Updaters
function updateDashboard(devices) {
    let totalScore = 0;
    let criticalCount = 0;
    const tableBody = document.getElementById('device-table-body');
    tableBody.innerHTML = ''; 

    const chartLabels = [];
    const chartData = [];
    const chartColors = [];
    const chartBorders = [];
    
    // Check if cyberpunk theme is active to alter chart colors
    const isCyber = document.body.classList.contains('cyberpunk-theme');

    devices.forEach(device => {
        totalScore += device.trust_score;
        let statusClass = 'badge-safe'; let statusText = 'SAFE'; let scoreClass = 'score-high';
        let color = isCyber ? 'rgba(0, 255, 100, 0.6)' : 'rgba(0, 230, 118, 0.6)';
        let border = isCyber ? '#00ff64' : 'rgba(0, 230, 118, 1)';

        if (device.trust_score < 50) {
            statusClass = 'badge-risk'; statusText = 'CRITICAL'; scoreClass = 'score-low';
            criticalCount++;
            color = isCyber ? 'rgba(255, 0, 60, 0.6)' : 'rgba(255, 30, 86, 0.6)';
            border = isCyber ? '#ff003c' : 'rgba(255, 30, 86, 1)';
        } else if (device.trust_score < 90) {
            statusClass = 'badge-warning'; statusText = 'WARNING'; scoreClass = 'score-med';
            color = isCyber ? 'rgba(253, 245, 0, 0.6)' : 'rgba(255, 183, 77, 0.6)';
            border = isCyber ? '#fdf500' : 'rgba(255, 183, 77, 1)';
        }

        chartLabels.push(device.device); chartData.push(device.trust_score);
        chartColors.push(color); chartBorders.push(border);

        const tr = document.createElement('tr');
        let riskHtml = '<span style="color: var(--text-secondary)">No risks detected</span>';
        if (device.risk && device.risk.length > 0) {
            riskHtml = `<ul class="risk-list" aria-label="Risk details">`;
            device.risk.forEach(r => riskHtml += `<li>${r}</li>`);
            riskHtml += `</ul>`;
        }
        tr.innerHTML = `
            <td>${device.device}</td>
            <td class="score-text ${scoreClass}">${device.trust_score}%</td>
            <td><span class="badge ${statusClass}">${statusText}</span></td>
            <td>${riskHtml}</td>
        `;
        tableBody.appendChild(tr);
    });

    document.getElementById('total-devices').textContent = devices.length;
    const avgScore = devices.length > 0 ? Math.round(totalScore / devices.length) : 0;
    document.getElementById('avg-trust').innerHTML = `${avgScore}<span class="unit" aria-hidden="true">%</span>`;
    document.getElementById('critical-alerts').textContent = criticalCount;
    
    // Add glowing pulse to critical metrics if needed
    const alertCard = document.querySelector('.alert-card');
    if(criticalCount > 0) alertCard.classList.add('danger-pulse');
    else alertCard.classList.remove('danger-pulse');

    renderChart(chartLabels, chartData, chartColors, chartBorders);
}

function updateDevicesView(devices) {
    const grid = document.getElementById('detailed-devices-grid');
    grid.innerHTML = '';
    
    // Sort devices lexicographically to make it easier for users to scan
    devices.sort((a,b) => a.device.localeCompare(b.device));
    
    devices.forEach(device => {
        let themeClass = 'safe';
        if (device.trust_score < 50) themeClass = 'danger';
        else if (device.trust_score < 90) themeClass = 'warning';

        const card = document.createElement('div');
        card.className = `metric-card glass-panel hover-glow device-detail-card ${themeClass}`;
        
        let riskHtml = '';
        if (device.risk && device.risk.length > 0) {
            riskHtml = `<div style="margin: 1rem 0; padding: 0.5rem; background: rgba(0,0,0,0.2); border-radius: 8px;">`;
            device.risk.forEach(r => riskHtml += `<div style="font-size: 0.8rem; color: var(--danger)">› ${r}</div>`);
            riskHtml += `</div>`;
        }

        card.innerHTML = `
            <div class="card-header">
                <h3>${device.device}</h3>
                <span class="score-text" style="font-size: 1.5rem" aria-label="Trust score: ${device.trust_score} percent">${device.trust_score}%</span>
            </div>
            ${riskHtml}
            <div class="card-actions">
                <button class="styled-button secondary" aria-label="Inspect Logs for ${device.device}" style="font-size: 0.8rem; padding: 0.5rem 1rem">Inspect Logs</button>
                <button class="styled-button ${themeClass === 'danger' ? 'danger' : 'primary'}" aria-label="${themeClass === 'danger' ? 'Quarantine' : 'Diagnostics'} device ${device.device}" style="font-size: 0.8rem; padding: 0.5rem 1rem">
                    ${themeClass === 'danger' ? 'Quarantine' : 'Diagnostics'}
                </button>
            </div>
        `;
        grid.appendChild(card);
    });
}

function updateAlertsTimeline(allData) {
    const container = document.getElementById('alerts-timeline-container');
    container.innerHTML = `<h3>Threat Intelligence History</h3><hr style="border:0; border-bottom:1px solid rgba(255,255,255,0.05); margin-bottom: 2rem;">`;
    
    // Collect all risks from the raw log
    let alerts = [];
    allData.forEach((entry, idx) => {
        if(entry.risk && entry.risk.length > 0) {
            entry.risk.forEach(r => {
                alerts.push({
                    device: entry.device,
                    risk: r,
                    score: entry.trust_score,
                    // Simulate a time string based on order since JSON doesn't have timestamps
                    time: new Date(Date.now() - (alerts.length * Math.random() * 3600000)).toLocaleString()
                });
            });
        }
    });

    // Sort by simulated time (newest first)
    alerts.sort((a,b) => new Date(b.time) - new Date(a.time));

    if(alerts.length === 0) {
        container.innerHTML += `<p class="text-secondary">No historical security threats detected.</p>`;
        return;
    }

    alerts.forEach(alert => {
        const item = document.createElement('div');
        item.className = 'timeline-item';
        // Add tabindex for screen reader accessibility
        item.setAttribute('tabindex', '0');
        item.innerHTML = `
            <div class="timeline-date">${alert.time} - Unit: <strong style="color:var(--text-primary)">${alert.device}</strong></div>
            <div class="timeline-title">${alert.risk}</div>
            <div style="font-size: 0.85rem; color: var(--text-secondary)">
                Trust score dropped to ${alert.score}% during event. Action required.
            </div>
        `;
        container.appendChild(item);
    });
}

function renderChart(labels, data, colors, borders) {
    if(chartInstance) {
        chartInstance.destroy();
    }
    
    const ctx = document.getElementById('trustChart').getContext('2d');
    Chart.defaults.color = '#a0a5b8';
    Chart.defaults.font.family = 'Inter';

    chartInstance = new Chart(ctx, {
        type: 'bar', 
        data: {
            labels: labels,
            datasets: [{
                label: 'Trust Score %',
                data: data,
                backgroundColor: colors,
                borderColor: borders,
                borderWidth: 1,
                borderRadius: 4, 
                hoverBackgroundColor: borders
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(14, 16, 24, 0.9)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1,
                    padding: 10,
                    displayColors: false,
                    callbacks: {
                        label: function(context) { return ' Trust: ' + context.parsed.y + '%'; }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true, max: 100,
                    grid: { color: 'rgba(255, 255, 255, 0.05)', drawBorder: false },
                    ticks: { stepSize: 20 }
                },
                x: {
                    grid: { display: false, drawBorder: false }
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeOutQuart'
            }
        }
    });
}
