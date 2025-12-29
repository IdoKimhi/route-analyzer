async function fetchJson(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`Request failed: ${url}`);
  return await r.json();
}

function setDownloadLink(hours, provider) {
  const p = new URLSearchParams();
  p.set("hours", String(hours));
  if (provider) p.set("provider", provider);
  const a = document.getElementById("downloadLink");
  if (a) a.href = `/download?${p.toString()}`;
}

function fillTable(items) {
  const tbody = document.querySelector("#samplesTable tbody");
  if (!tbody) return;
  tbody.innerHTML = "";
  const last = items.slice(-200).reverse();
  for (const it of last) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="mono">${it.ts}</td>
      <td>${it.provider}</td>
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
    datasets.push({
      label: provider,
      data: values,
      tension: 0.2
    });
  }
  return new Chart(ctx, {
    type: "line",
    data: { labels, datasets },
    options: {
      responsive: true,
      interaction: { mode: "index", intersect: false },
      scales: {
        y: { title: { display: true, text: "ETA (minutes)" } },
        x: { title: { display: true, text: "Time (UTC)" } }
      }
    }
  });
}

async function initStatusPage() {
  const hoursEl = document.getElementById("hours");
  const providerEl = document.getElementById("provider");
  const chartEl = document.getElementById("etaChart");
  if (!hoursEl || !providerEl || !chartEl) return;

  let chart = null;

  async function reload() {
    const hours = parseInt(hoursEl.value, 10);
    const provider = providerEl.value || "";
    setDownloadLink(hours, provider);

    const params = new URLSearchParams();
    params.set("hours", String(hours));
    if (provider) params.set("provider", provider);

    const items = await fetchJson(`/api/samples?${params.toString()}`);

    const labels = items.map(x => x.ts);
    const byProvider = {};
    for (const it of items) {
      if (!byProvider[it.provider]) byProvider[it.provider] = [];
      byProvider[it.provider].push(it.status === "ok" ? it.duration_min : null);
    }

    if (chart) chart.destroy();
    chart = buildLineChart(chartEl.getContext("2d"), labels, byProvider);

    fillTable(items);
  }

  hoursEl.addEventListener("change", reload);
  providerEl.addEventListener("change", reload);
  await reload();
}

async function initHomePage() {
  const mapEl = document.getElementById("map");
  const chartEl = document.getElementById("homeChart");

  // Map
  if (mapEl) {
    const cfg = await fetchJson("/api/config");
    if (cfg && window.L) {
      const start = cfg.start;
      const end = cfg.end;
      const center = [(start[0] + end[0]) / 2, (start[1] + end[1]) / 2];

      const map = L.map("map").setView(center, 12);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors"
      }).addTo(map);

      const a = L.marker(start).addTo(map).bindPopup("Start");
      const b = L.marker(end).addTo(map).bindPopup("End");
      L.polyline([start, end]).addTo(map);

      const group = L.featureGroup([a, b]);
      map.fitBounds(group.getBounds().pad(0.2));
    }
  }

  // Home chart (last 24h)
  if (chartEl) {
    const items = await fetchJson("/api/samples?hours=24");
    const labels = items.map(x => x.ts);
    const byProvider = {};
    for (const it of items) {
      if (!byProvider[it.provider]) byProvider[it.provider] = [];
      byProvider[it.provider].push(it.status === "ok" ? it.duration_min : null);
    }
    buildLineChart(chartEl.getContext("2d"), labels, byProvider);
  }
}

window.addEventListener("DOMContentLoaded", async () => {
  await initStatusPage();
  await initHomePage();
});
