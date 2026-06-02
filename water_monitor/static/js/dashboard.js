/**
 * dashboard.js — AquaWatch Deep Intelligence Engine
 * ====================================================
 * Powers: SVG orb arcs, arc gauges, prediction ambient glow,
 * Chart.js charts with range switching, and 10s live refresh.
 */

'use strict';

/* ── App State ───────────────────────────────────────────────────────────── */
let chartPH = null, chartTurb = null, chartTemp = null;
let currentRange = 20;
let prevLatestId = null;
let allRecords   = [];

/* ── Chart colours ───────────────────────────────────────────────────────── */
let C = {
  ph:   { line: '#00FFDC', fill: 'rgba(0,255,220,0.07)',   zone: 'rgba(0,255,220,0.06)',   threshold: 'rgba(0,255,220,0.15)' },
  turb: { line: '#8B5CF6', fill: 'rgba(139,92,246,0.07)',  zone: 'rgba(139,92,246,0.06)',  threshold: 'rgba(139,92,246,0.15)' },
  temp: { line: '#F59E0B', fill: 'rgba(245,158,11,0.07)',  zone: 'rgba(245,158,11,0.06)',  threshold: 'rgba(245,158,11,0.15)' },
};

/* ── Font reference for Chart.js ─────────────────────────────────────────── */
const MONO = "'DM Mono', monospace";

/* ── Common chart options factory ────────────────────────────────────────── */
function makeOpts(yLabel, yMin, yMax) {
  const isLight = document.body.classList.contains('light-theme');
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 700, easing: 'easeInOutCubic' },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: isLight ? 'rgba(255,255,255,0.95)' : 'rgba(2,10,15,0.95)',
        borderColor:     isLight ? 'rgba(0,0,0,0.1)' : 'rgba(0,255,220,0.25)',
        borderWidth:     1,
        titleColor:      isLight ? '#008080' : '#00FFDC',
        bodyColor:       isLight ? '#0F172A' : '#D1F5F0',
        titleFont:       { family: MONO, size: 11 },
        bodyFont:        { family: MONO, size: 11 },
        padding:         12,
        cornerRadius:    8,
        displayColors:   false,
        callbacks: {
          label: ctx => ` ${ctx.parsed.y} ${yLabel}`
        }
      },
    },
    scales: {
      x: {
        grid:  { color: isLight ? 'rgba(0,0,0,0.04)' : 'rgba(0,255,220,0.04)', drawBorder: false },
        ticks: { color: isLight ? '#64748B' : '#1F4540', font: { family: MONO, size: 9 }, maxTicksLimit: 8, maxRotation: 0 },
        border: { display: false },
      },
      y: {
        grid:        { color: isLight ? 'rgba(0,0,0,0.04)' : 'rgba(0,255,220,0.04)', drawBorder: false },
        ticks:       { color: isLight ? '#64748B' : '#1F4540', font: { family: MONO, size: 9 } },
        title:       { display: false },
        suggestedMin: yMin,
        suggestedMax: yMax,
        border:      { display: false },
      },
    },
  };
}

/* ── Build dataset ───────────────────────────────────────────────────────── */
function makeDataset(color) {
  return {
    data:                [],
    borderColor:         color.line,
    backgroundColor:     color.fill,
    borderWidth:         2,
    pointRadius:         3.5,
    pointBackgroundColor: color.line,
    pointBorderColor:    'var(--bg)',
    pointBorderWidth:    1.5,
    pointHoverRadius:    6,
    fill:                true,
    tension:             0.45,
  };
}

/* ── Initialise charts ───────────────────────────────────────────────────── */
function initCharts() {
  chartPH = new Chart(document.getElementById('chart-ph'), {
    type: 'line',
    data: { labels: [], datasets: [makeDataset(C.ph)] },
    options: makeOpts('pH', 0, 14),
  });
  chartTurb = new Chart(document.getElementById('chart-turb'), {
    type: 'line',
    data: { labels: [], datasets: [makeDataset(C.turb)] },
    options: makeOpts('NTU', 0, 20),
  });
  chartTemp = new Chart(document.getElementById('chart-temp'), {
    type: 'line',
    data: { labels: [], datasets: [makeDataset(C.temp)] },
    options: makeOpts('°C', 0, 50),
  });
}

/* ── Update charts from records ──────────────────────────────────────────── */
function updateCharts(records) {
  const slice = [...records].reverse().slice(-currentRange);
  if (slice.length === 0) return;

  const labels = slice.map(r => {
    const d = new Date(r.created_at);
    return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
  });

  chartPH.data.labels   = chartTurb.data.labels   = chartTemp.data.labels   = labels;
  chartPH.data.datasets[0].data   = slice.map(r => +r.ph);
  chartTurb.data.datasets[0].data = slice.map(r => +r.turbidity);
  chartTemp.data.datasets[0].data = slice.map(r => +r.temperature);
  chartPH.update('none'); chartTurb.update('none'); chartTemp.update('none');

  // Update averages
  const avg = (arr) => arr.length ? (arr.reduce((a,b)=>a+b,0)/arr.length).toFixed(2) : '—';
  document.getElementById('cavg-ph').textContent   = `Avg: ${avg(slice.map(r=>+r.ph))} pH`;
  document.getElementById('cavg-turb').textContent = `Avg: ${avg(slice.map(r=>+r.turbidity))} NTU`;
  document.getElementById('cavg-temp').textContent = `Avg: ${avg(slice.map(r=>+r.temperature))} °C`;
}

/* ── Range tab switching ─────────────────────────────────────────────────── */
function setRange(el, n) {
  document.querySelectorAll('.ctab').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
  currentRange = n;
  updateCharts(allRecords);
}

/* ── SVG Orb Arc ─────────────────────────────────────────────────────────── */
function updateOrb(prediction, confidence) {
  const arc      = document.getElementById('orb-arc');
  const arcInner = document.getElementById('orb-arc-inner');
  const valText  = document.getElementById('orb-value-text');
  const confText = document.getElementById('orb-conf-text');
  const glow     = document.getElementById('orb-glow-circle');
  const body     = document.body;

  const pct = parseFloat(confidence) / 100 || 0;
  const C_OUTER = 741, C_INNER = 616;

  arc.style.strokeDashoffset      = C_OUTER - pct * C_OUTER;
  arcInner.style.strokeDashoffset = C_INNER - pct * C_INNER * 0.7;

  valText.textContent  = prediction || '—';
  confText.textContent = confidence ? `Confidence ${confidence}` : 'Awaiting sensor data';

  // Remove old classes
  body.classList.remove('status-hazard', 'status-good');

  let colour = 'var(--cyan)', glowColour = 'var(--cyan-glow)';
  if (prediction === 'Hazard') {
    colour = 'var(--hazard)'; glowColour = 'var(--hazard-glow)';
    body.classList.add('status-hazard');
  } else if (prediction === 'Good') {
    colour = 'var(--safe)'; glowColour = 'var(--safe-glow)';
    body.classList.add('status-good');
  }

  arc.style.stroke      = colour;
  arcInner.style.stroke = colour;
  valText.style.fill    = colour;
  glow.style.fill       = glowColour;

  // Ambient glow
  const ambientEl = document.getElementById('ambient-glow');
  if (ambientEl) ambientEl.style.background = `radial-gradient(ellipse at 20% 50%, ${glowColour} 0%, transparent 70%)`;
}

/* ── Gauge arc path helper ───────────────────────────────────────────────── */
function gaugeArcDash(pct, circumference = 377) {
  // The arc path covers ~250° of 360° (from -220° to 70°) ≈ 261.8/377 * circ
  const arcLength = circumference * 0.694; // 261.8/360 ≈ 69.4% of the circle
  const filled    = Math.max(0, Math.min(1, pct)) * arcLength;
  return `${filled} ${circumference}`;
}

/* ── Update arc gauges ───────────────────────────────────────────────────── */
function updateGauges(ph, turbidity, temperature) {
  // ── pH (0–14 scale, ideal 6.5–7.5)
  const phPct = ph / 14;
  document.getElementById('ag-val-ph').textContent  = ph.toFixed(2);
  document.getElementById('ag-fill-ph').style.strokeDasharray = gaugeArcDash(phPct);
  const phStatus  = ph < 6.5 || ph > 7.5 ? 'HAZARD' : 'NOMINAL';
  const phColor   = phStatus === 'HAZARD' ? 'var(--hazard)' : phStatus === 'WARNING' ? 'var(--warning)' : 'var(--cyan)';
  document.getElementById('ag-fill-ph').style.stroke   = phColor;
  document.getElementById('ag-val-ph').style.fill       = phColor;
  document.getElementById('ag-status-ph').textContent  = phStatus;
  document.getElementById('ag-status-ph').style.color   = phColor;

  // ── Turbidity (0–200 NTU scale)
  const turbPct = Math.min(turbidity / 100, 1);
  document.getElementById('ag-val-turb').textContent    = turbidity.toFixed(1);
  document.getElementById('ag-fill-turb').style.strokeDasharray = gaugeArcDash(turbPct);
  const turbStatus = turbidity > 100 ? 'HAZARD' : turbidity > 4 ? 'WARNING' : 'NOMINAL';
  const turbColor  = turbStatus === 'HAZARD' ? 'var(--hazard)' : turbStatus === 'WARNING' ? 'var(--warning)' : 'var(--violet)';
  document.getElementById('ag-fill-turb').style.stroke   = turbColor;
  document.getElementById('ag-val-turb').style.fill       = turbColor;
  document.getElementById('ag-status-turb').textContent  = turbStatus;
  document.getElementById('ag-status-turb').style.color   = turbColor;

  // ── Temperature (0–50°C scale)
  const tempPct = Math.min(Math.max(temperature + 10, 0) / 60, 1);
  document.getElementById('ag-val-temp').textContent    = temperature.toFixed(1);
  document.getElementById('ag-fill-temp').style.strokeDasharray = gaugeArcDash(tempPct);
  const tempStatus = temperature < 5 || temperature > 40 ? 'HAZARD' : temperature < 10 || temperature > 30 ? 'WARNING' : 'NOMINAL';
  const tempColor  = tempStatus === 'HAZARD' ? 'var(--hazard)' : tempStatus === 'WARNING' ? 'var(--warning)' : 'var(--amber)';
  document.getElementById('ag-fill-temp').style.stroke   = tempColor;
  document.getElementById('ag-val-temp').style.fill       = tempColor;
  document.getElementById('ag-status-temp').textContent  = tempStatus;
  document.getElementById('ag-status-temp').style.color   = tempColor;
}

/* ── Update class badges (probability) ──────────────────────────────────── */
function updateBadges(probs) {
  document.getElementById('cbadge-val-hazard').textContent = probs?.Hazard || '—';
  document.getElementById('cbadge-val-good').textContent = probs?.Good || '—';
}

/* ── Update hero stats ───────────────────────────────────────────────────── */
function updateStats(data) {
  document.getElementById('hs-total').textContent   = data.total   ?? 0;
  document.getElementById('hs-hazard').textContent = data.hazard  ?? 0;
  document.getElementById('hs-good').textContent  = data.good   ?? 0;
}

/* ── Update table ────────────────────────────────────────────────────────── */
function updateTable(records) {
  const tbody = document.getElementById('tbl-body');
  if (!records || records.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="tbl-empty">No readings yet — use the SIMULATE button above</td></tr>`;
    return;
  }

  const isFirstLoad = prevLatestId === null;
  const newLatestId = records[0]?.id;
  const hasNew = !isFirstLoad && newLatestId !== prevLatestId;
  prevLatestId = newLatestId;

  tbody.innerHTML = records.slice(0, 25).map((r, i) => {
    const d = new Date(r.created_at);
    const ts = d.toLocaleString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
    const tagC = (r.prediction || '').toLowerCase();
    return `<tr class="${hasNew && i === 0 ? 'row-new' : ''}">
      <td class="td-id">${r.id}</td>
      <td class="td-time">${ts}</td>
      <td class="td-num">${(+r.ph).toFixed(2)}</td>
      <td class="td-num">${(+r.turbidity).toFixed(2)}</td>
      <td class="td-num">${(+r.temperature).toFixed(2)}</td>
      <td><span class="pred-tag pred-${tagC}">${r.prediction}</span></td>
      <td class="td-conf">${r.confidence ?? '—'}</td>
    </tr>`;
  }).join('');
}

/* ── Update sys status dot & label ──────────────────────────────────────── */
function setSysStatus(ok) {
  const dot   = document.getElementById('sys-dot');
  const label = document.getElementById('sys-label');
  if (ok) {
    dot.style.background   = 'var(--safe)';
    dot.style.boxShadow    = '0 0 8px var(--safe)';
    dot.style.animation    = 'blink 2s ease-in-out infinite';
    label.textContent      = 'LIVE';
    label.style.color      = 'var(--safe)';
  } else {
    dot.style.background   = 'var(--hazard)';
    dot.style.boxShadow    = '0 0 8px var(--hazard)';
    dot.style.animation    = 'none';
    dot.style.opacity      = '1';
    label.textContent      = 'OFFLINE';
    label.style.color      = 'var(--hazard)';
  }
}

/* ── Main refresh ────────────────────────────────────────────────────────── */
async function refreshAll() {
  try {
    const [histRes, latestRes, statsRes] = await Promise.all([
      fetch('/api/history/?limit=200'),
      fetch('/api/latest/'),
      fetch('/api/stats/'),
    ]);

    if (!histRes.ok) throw new Error('History API failed');

    const histData = await histRes.json();
    allRecords = histData.results || [];

    if (allRecords.length > 0) {
      updateCharts(allRecords);
      updateTable(allRecords);
      const latest = allRecords[0];
      updateGauges(+latest.ph, +latest.turbidity, +latest.temperature);

      // update last reading meta
      const d = new Date(latest.created_at);
      document.getElementById('lm-time').textContent = 'Last reading: ' + d.toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'medium', hour12: false });
    }

    if (latestRes.ok) {
      const latest = await latestRes.json();
      if (latest.prediction) {
        updateOrb(latest.prediction, latest.confidence || '—');
        // Fetch probabilities from POST response — use latest data
      }
    }

    if (statsRes.ok) {
      const stats = await statsRes.json();
      updateStats(stats);
    }

    setSysStatus(true);
    document.getElementById('ftr-sync').textContent = 'Last sync ' + new Date().toLocaleTimeString('en-IN', { hour12: false });

  } catch (err) {
    console.warn('[AquaWatch] Refresh error:', err);
    setSysStatus(false);
  }
}

/* ── Simulate ESP32 reading ──────────────────────────────────────────────── */
async function sendTestReading() {
  const btn = document.getElementById('sim-btn');
  btn.disabled = true;
  btn.innerHTML = '<span class="btn-icon">⏳</span> SENDING…';

  // Randomize across all three quality categories for variety
  const roll = Math.random();
  let ph, turb, temp;
  if (roll < 0.5) {
    // Safe
    ph = +(6.8 + Math.random() * 1.4).toFixed(2);
    turb = +(Math.random() * 3.5).toFixed(2);
    temp = +(15 + Math.random() * 12).toFixed(2);
  } else if (roll < 0.8) {
    // Warning
    ph = +(Math.random() < 0.5 ? 5.8 + Math.random() * 0.7 : 8.6 + Math.random() * 0.9).toFixed(2);
    turb = +(5 + Math.random() * 15).toFixed(2);
    temp = +(30 + Math.random() * 8).toFixed(2);
  } else {
    // Hazard
    ph = +(Math.random() < 0.5 ? 3.5 + Math.random() * 1.4 : 10 + Math.random() * 2).toFixed(2);
    turb = +(110 + Math.random() * 60).toFixed(2);
    temp = +(40 + Math.random() * 10).toFixed(2);
  }

  try {
    const res = await fetch('/api/data/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ph, turbidity: turb, temperature: temp }),
    });
    const data = await res.json();
    if (data.probabilities) updateBadges(data.probabilities);
    await refreshAll();
  } catch (err) {
    console.error('[AquaWatch] Simulate failed:', err);
    setSysStatus(false);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<span class="btn-icon">⚡</span> SIMULATE ESP32';
  }
}

/* ── Countdown display ───────────────────────────────────────────────────── */
const INTERVAL_S = 10;
let countdown = INTERVAL_S;
function tickCountdown() {
  const el = document.getElementById('countdown-val');
  if (el) el.textContent = countdown + 's';
  countdown--;
  if (countdown < 0) countdown = INTERVAL_S;
  setTimeout(tickCountdown, 1000);
}

/* ── Theme Switcher ──────────────────────────────────────────────────────── */
function initTheme() {
  const toggleBtn = document.getElementById('theme-toggle');
  const sunIcon = document.getElementById('theme-icon-sun');
  const moonIcon = document.getElementById('theme-icon-moon');
  
  const currentTheme = localStorage.getItem('aquawatch-theme') || 'dark';
  
  const applyThemeClasses = (theme) => {
    if (theme === 'light') {
      document.body.classList.add('light-theme');
      sunIcon.style.display = 'block';
      moonIcon.style.display = 'none';
    } else {
      document.body.classList.remove('light-theme');
      sunIcon.style.display = 'none';
      moonIcon.style.display = 'block';
    }
  };

  applyThemeClasses(currentTheme);

  toggleBtn.addEventListener('click', () => {
    const isLight = document.body.classList.contains('light-theme');
    const newTheme = isLight ? 'dark' : 'light';
    localStorage.setItem('aquawatch-theme', newTheme);
    applyThemeClasses(newTheme);
    
    // Update chart colors by re-instantiating or updating their configs
    updateChartThemeConfigs(newTheme);
  });
}

function updateChartThemeConfigs(theme) {
  const isLight = theme === 'light';
  
  C = isLight ? {
    ph:   { line: '#008080', fill: 'rgba(0,128,128,0.07)',   zone: 'rgba(0,128,128,0.06)',   threshold: 'rgba(0,128,128,0.15)' },
    turb: { line: '#6D28D9', fill: 'rgba(109,40,217,0.07)',  zone: 'rgba(109,40,217,0.06)',  threshold: 'rgba(109,40,217,0.15)' },
    temp: { line: '#D97706', fill: 'rgba(217,119,6,0.07)',   zone: 'rgba(217,119,6,0.06)',   threshold: 'rgba(217,119,6,0.15)' },
  } : {
    ph:   { line: '#00FFDC', fill: 'rgba(0,255,220,0.07)',   zone: 'rgba(0,255,220,0.06)',   threshold: 'rgba(0,255,220,0.15)' },
    turb: { line: '#8B5CF6', fill: 'rgba(139,92,246,0.07)',  zone: 'rgba(139,92,246,0.06)',  threshold: 'rgba(139,92,246,0.15)' },
    temp: { line: '#F59E0B', fill: 'rgba(245,158,11,0.07)',  zone: 'rgba(245,158,11,0.06)',  threshold: 'rgba(245,158,11,0.15)' },
  };

  const cGrid = isLight ? 'rgba(0,0,0,0.04)' : 'rgba(0,255,220,0.04)';
  const cTick = isLight ? '#64748B' : '#1F4540';
  const cToolBg = isLight ? 'rgba(255,255,255,0.95)' : 'rgba(2,10,15,0.95)';
  const cToolText = isLight ? '#0F172A' : '#D1F5F0';

  [chartPH, chartTurb, chartTemp].forEach((ch, i) => {
    if(!ch) return;
    const key = ['ph', 'turb', 'temp'][i];
    
    ch.data.datasets[0].borderColor = C[key].line;
    ch.data.datasets[0].backgroundColor = C[key].fill;
    ch.data.datasets[0].pointBackgroundColor = C[key].line;
    
    ch.options.scales.x.grid.color = cGrid;
    ch.options.scales.y.grid.color = cGrid;
    ch.options.scales.x.ticks.color = cTick;
    ch.options.scales.y.ticks.color = cTick;
    
    ch.options.plugins.tooltip.backgroundColor = cToolBg;
    ch.options.plugins.tooltip.titleColor = C[key].line;
    ch.options.plugins.tooltip.bodyColor = cToolText;
    
    ch.update('none');
  });
}

/* ── Bootstrap ───────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initCharts();
  refreshAll();
  setInterval(refreshAll, INTERVAL_S * 1000);
  tickCountdown();
});
