const zones = [
    'Asia/Manila', 'UTC', 'America/New_York', 'Europe/London', 
    'Asia/Tokyo', 'Australia/Sydney', 'Europe/Berlin', 'America/Los_Angeles'
];

function initClocks() {
    const grid = document.getElementById('clock-grid');
    zones.forEach(zone => {
        const zoneId = zone.replace('/', '-');
        grid.innerHTML += `
            <div class="clock-card" id="${zoneId}">
                <h3>${zone}</h3>
                <div class="time-display">--:--:--</div>
            </div>`;
    });
}

async function updateWorldClock() {
    for (let zone of zones) {
        const zoneId = zone.replace('/', '-');
        try {
            const response = await fetch(`/api/world-clock/${zone.replace('/', '-')}`);
            const data = await response.json();
            const card = document.getElementById(zoneId);
            if (card) card.querySelector('.time-display').innerText = data.time;
        } catch (e) { console.error(e); }
    }
}

initClocks();
setInterval(updateWorldClock, 1000);