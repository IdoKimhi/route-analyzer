async function fetchJson(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`Request failed: ${url}`);
  return await r.json();
}

const israelDateFormatter = new Intl.DateTimeFormat("en-CA", {
  timeZone: "Asia/Jerusalem",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false
});

function formatIsraelTime(iso) {
  const parts = israelDateFormatter.formatToParts(new Date(iso));
  const lookup = Object.fromEntries(parts.map(p => [p.type, p.value]));
  return `${lookup.year}-${lookup.month}-${lookup.day} ${lookup.hour}:${lookup.minute}`;
}

function setDownloadLink(hours, routeId) {
  const p = new URLSearchParams();
  p.set("hours", String(hours));
  if (routeId) p.set("route_id", routeId);
  const a = document.getElementById("downloadLink");
  if (a) a.href = `/download?${p.toString()}`;
}

function fillTable(items, routesById) {
  const tbody = document.querySelector("#samplesTable tbody");
  if (!tbody) return;
  tbody.innerHTML = "";
  const last = items.slice(-200).reverse();
  for (const it of last) {
    const routeName = routesById[it.route_id] ? routesById[it.route_id].name : String(it.route_id);
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="mono">${formatIsraelTime(it.ts)}</td>
      <td>${routeName}</td>
      <td>${it.status}</td>
      <td>${it.duration_min ?? ""}</td>
      <td>${it.distance_km ?? ""}</td>
      <td class="err">${it.error ?? ""}</td>
    `;
    tbody.appendChild(tr);
  }
}

function buildLineChart(ctx, labels, seriesByProvider) {
  const datasets = [];
  for (const [provider, values] of Object.entries(seriesByProvider)) {
    datasets.push({ label: provider, data: values, tension: 0.2 });
  }
  return new Chart(ctx, {
    type: "line",
    data: { labels, datasets },
    options: {
      responsive: true,
      interaction: { mode: "index", intersect: false },
      scales: {
        y: { title: { display: true, text: "ETA (minutes)" } },
        x: { title: { display: true, text: "Time (Israel)" } }
      }
    }
  });
}

async function initStatusPage() {
  const hoursEl = document.getElementById("hours");
  const routeEl = document.getElementById("route");
  const chartEl = document.getElementById("etaChart");
  if (!hoursEl || !routeEl || !chartEl) return;

  const routes = await fetchJson("/api/routes");
  const routesById = {};
  for (const r of routes) routesById[r.id] = r;

  for (const r of routes) {
    const opt = document.createElement("option");
    opt.value = String(r.id);
    opt.textContent = `${r.name}${r.enabled ? "" : " (off)"}`;
    routeEl.appendChild(opt);
  }

  let chart = null;

  async function reload() {
    const hours = parseInt(hoursEl.value, 10);
    const routeId = routeEl.value || "";

    setDownloadLink(hours, routeId);

    const params = new URLSearchParams();
    params.set("hours", String(hours));
    if (routeId) params.set("route_id", routeId);

    const items = await fetchJson(`/api/samples?${params.toString()}`);

    const labels = items.map(x => formatIsraelTime(x.ts));
    const byProvider = {};
    for (const it of items) {
      if (!byProvider[it.provider]) byProvider[it.provider] = [];
      byProvider[it.provider].push(it.status === "ok" ? it.duration_min : null);
    }

    if (chart) chart.destroy();
    chart = buildLineChart(chartEl.getContext("2d"), labels, byProvider);

    fillTable(items, routesById);
  }

  hoursEl.addEventListener("change", reload);
  routeEl.addEventListener("change", reload);

  await reload();
}

function setProviderStatus(routeId) {
  const el = document.getElementById("providerStatus");
  if (!el) return;

  const d = window.__lastByRoute ? window.__lastByRoute[String(routeId)] : null;
  if (!d) {
    el.textContent = "No data yet for this route.";
    return;
  }

  const w = d.waze;

  el.innerHTML = `
    <div class="statusRow">
      <div>
        <div class="label">Waze</div>
        <div class="mono">${w ? `${w.status} at ${formatIsraelTime(w.ts)}` : "No data"}</div>
        ${w && w.eta !== null ? `<div>ETA: ${w.eta} min</div>` : ""}
        ${w && w.err ? `<div class="err">${w.err}</div>` : ""}
      </div>
    </div>
  `;
}

async function initHomePage() {
  const mapEl = document.getElementById("map");
  const chartEl = document.getElementById("homeChart");
  const routeSelect = document.getElementById("homeRoute");
  if (!routeSelect) return;

  const routes = await fetchJson("/api/routes");
  const routesById = {};
  for (const r of routes) routesById[r.id] = r;

  let map = null;
  let markers = null;
  let routeLine = null;
  let chart = null;

  async function renderMap(routeId) {
    if (!mapEl || !window.L) return;
    const r = routesById[routeId];
    if (!r) return;

    const start = r.start;
    const end = r.end;
    const center = [(start[0] + end[0]) / 2, (start[1] + end[1]) / 2];

    if (!map) {
      map = L.map("map").setView(center, 12);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors"
      }).addTo(map);
    }

    if (markers) {
      markers.forEach(x => map.removeLayer(x));
      markers = null;
    }
    if (routeLine) {
      map.removeLayer(routeLine);
      routeLine = null;
    }

    const a = L.marker(start).addTo(map).bindPopup("Start");
    const b = L.marker(end).addTo(map).bindPopup("End");
    markers = [a, b];

    let points = [start, end];
    try {
      const data = await fetchJson(`/api/routes/${routeId}/path`);
      if (Array.isArray(data.points) && data.points.length) {
        points = data.points;
      }
    } catch (err) {
      console.warn("Route path fetch failed", err);
    }

    routeLine = L.polyline(points, { color: "#4aa3ff", weight: 4 }).addTo(map);

    const group = L.featureGroup([a, b]);
    map.fitBounds(group.getBounds().pad(0.2));
  }

  async function renderChart(routeId) {
    if (!chartEl) return;

    const params = new URLSearchParams();
    params.set("hours", "24");
    params.set("route_id", String(routeId));

    const items = await fetchJson(`/api/samples?${params.toString()}`);

    const labels = items.map(x => formatIsraelTime(x.ts));
    const byProvider = {};
    for (const it of items) {
      if (!byProvider[it.provider]) byProvider[it.provider] = [];
      byProvider[it.provider].push(it.status === "ok" ? it.duration_min : null);
    }

    if (chart) chart.destroy();
    chart = buildLineChart(chartEl.getContext("2d"), labels, byProvider);
  }

  async function reloadHome() {
    const routeId = parseInt(routeSelect.value, 10);
    if (!routeId) return;

    setProviderStatus(routeId);
    await renderMap(routeId);
    await renderChart(routeId);
  }

  routeSelect.addEventListener("change", reloadHome);

  await reloadHome();
}

window.addEventListener("DOMContentLoaded", async () => {
  await initStatusPage();
  await initHomePage();
});
