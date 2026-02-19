
    let refreshInterval = null;
    let currentOrigin = null;
    let currentDestination = null;

    function switchTab(name) {
        document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
        document.querySelectorAll(".tab-content").forEach(t => t.classList.remove("active"));
        document.querySelector(`[onclick="switchTab('${name}')"]`).classList.add("active");
        document.getElementById(`tab-${name}`).classList.add("active");
    }

    async function loadRoute() {
        const origin = document.getElementById("origin").value.trim().toUpperCase();
        const destination = document.getElementById("destination").value.trim().toUpperCase();

        if (!origin || !destination || origin.length < 3 || destination.length < 3) {
            alert("Please enter valid ICAO codes (e.g. KORD, KDEN)");
            return;
        }

        currentOrigin = origin;
        currentDestination = destination;

        await refresh();

        // Auto-refresh every 5 minutes
        if (refreshInterval) clearInterval(refreshInterval);
        refreshInterval = setInterval(refresh, 5 * 60 * 1000);
    }

    async function refresh() {
        document.getElementById("refresh-status").textContent = "Refreshing...";
        await Promise.all([loadPireps(), loadAtis(), loadMap()]);
        const now = new Date().toLocaleTimeString();
        document.getElementById("refresh-status").textContent = `Last updated: ${now} — refreshes every 5 min`;
    }

    async function loadPireps() {
        const panel = document.getElementById("tab-pireps");
        panel.innerHTML = `<div class="loading">Fetching PIREPs...</div>`;
        try {
            const res = await fetch(`/api/pireps?origin=${currentOrigin}&destination=${currentDestination}`);
            const data = await res.json();
            if (!data.pireps || data.pireps.length === 0) {
                panel.innerHTML = `<div class="empty-state">No PIREPs found along this route.</div>`;
                return;
            }
             panel.innerHTML = data.pireps.map(p => {
                const turb = p.tbInt1 || null;
                const ice = p.icgInt1 || null;
                const alt = p.fltLvl ? `FL${String(p.fltLvl).padStart(3, '0')}` : "Unknown";
                const raw = p.rawOb || "";
                return `
                    <div class="data-card">
                        <div class="label">
                            ${turb && turb !== "NEG" ? `<span class="badge badge-turb">TURB</span>` : ""}
                            ${ice && ice !== "" ? `<span class="badge badge-ice">ICE</span>` : ""}
                            Alt: ${alt}ft &nbsp;|&nbsp; ${parseFloat(p.lat).toFixed(2)}, ${parseFloat(p.lon).toFixed(2)}
                        </div>
                        ${turb ? `<div>Turbulence: ${turb}</div>` : ""}
                        ${ice ? `<div>Icing: ${ice}</div>` : ""}
                        <div class="raw">${raw}</div>
                    </div>`;
            }).join("");
        } catch (e) {
            panel.innerHTML = `<div class="empty-state">Error loading PIREPs.</div>`;
        }
    }

    async function loadAtis() {
        const panel = document.getElementById("tab-atis");
        panel.innerHTML = `<div class="loading">Fetching ATIS...</div>`;
        try {
            const res = await fetch(`/api/atis?airports=${currentOrigin},${currentDestination}`);
            const data = await res.json();
            panel.innerHTML = data.airports.map(a => {
            const changed = a.changed;
            return `
                <div class="data-card">
                    <div class="label">
                        ${a.airport}
                        <span class="badge ${changed ? 'badge-changed' : 'badge-ok'}">
                            ${changed ? "CHANGED" : "NO CHANGE"}
                        </span>
                    </div>
                    ${changed ? `<div>Previous: <span class="raw">${a.previous}</span></div>` : ""}
                    <div class="raw">${a.current || a.reason || "No data available"}</div>
                </div>`;
        }).join("");
        } catch (e) {
            panel.innerHTML = `<div class="empty-state">Error loading ATIS.</div>`;
        }
    }

    async function loadMap() {
        const container = document.getElementById("map-container");
        const res = await fetch(`/api/map?origin=${currentOrigin}&destination=${currentDestination}`);
        if (res.ok) {
            const html = await res.text();
            const blob = new Blob([html], {type: "text/html"});
            const url = URL.createObjectURL(blob);
            container.innerHTML = `<iframe src="${url}"></iframe>`;
        }
    }