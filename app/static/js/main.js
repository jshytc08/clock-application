// Function to clean the timezone string for display
function formatZoneName(zone) {
    const parts = zone.split('/');
    return parts.length > 1 ? parts[1].replace(/_/g, ' ') : zone;
}

async function initClocks() {
    const response = await fetch('/api/timezones');
    const data = await response.json();
    const zoneList = data.zones; 
    
    const grid = document.getElementById('clock-grid');
    grid.innerHTML = ''; 

    zoneList.forEach(zone => {
        const zoneId = zone.replace(/\//g, '-');
        const readableName = formatZoneName(zone);
        const regionName = zone.split('/')[0];
        
        // Ensure data-zone is lowercase for easier matching
        grid.innerHTML += `
            <div class="clock-card" id="${zoneId}" data-zone="${zone.toLowerCase()}">
                <div class="label-container">
                    <h3 style="margin:0; font-size: 0.8rem; color: #8e8e93;">${regionName}</h3>
                    <div style="font-size: 1.1rem; font-weight: 500;">${readableName}</div>
                </div>
                <div class="time-display" id="time-${zoneId}">--:--:--</div>
            </div>`;
    });
}

function filterClocks() {
    const query = document.getElementById('searchInput').value.toLowerCase();
    const region = document.getElementById('regionSelect').value; // Keep region as is for matching
    
    const cards = document.querySelectorAll('.clock-card');
    cards.forEach(card => {
        const zoneData = card.getAttribute('data-zone'); // e.g., "asia/manila"
        
        const matchesText = zoneData.includes(query);
        // If region is empty, it matches. Otherwise, check if zone starts with region (lowercase)
        const matchesRegion = (region === "") || zoneData.startsWith(region.toLowerCase());
        
        // Show if both conditions are met
        card.classList.toggle('hidden', !(matchesText && matchesRegion));
    });
}

async function updateWorldClock() {
    const visibleCards = document.querySelectorAll('.clock-card:not(.hidden)');
    
    // Using for...of loop for async reliability
    for (const card of visibleCards) {
        const zone = card.id.replace(/-/g, '/');
        try {
            const response = await fetch(`/api/world-clock/${zone}`);
            const data = await response.json();
            if (data.time) {
                const display = card.querySelector('.time-display');
                if (display) display.innerText = data.time;
            }
        } catch (e) { console.error(e); }
    }
}

// Execution
initClocks().then(() => {
    updateWorldClock();
    setInterval(updateWorldClock, 1000);
});