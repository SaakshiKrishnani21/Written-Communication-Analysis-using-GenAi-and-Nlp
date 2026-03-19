// ── chart_config.js ───────────────────────────────────────────
// Shared Chart.js defaults and helper factories
// Usage: import { makeLineChart, makeDonut, makeBar } from "../../charts/chart_config.js";

// ── Shared palette ─────────────────────────────────────────────
export const COLORS = {
  blue:   "#4f8ef7",
  purple: "#a78bfa",
  green:  "#22c55e",
  amber:  "#f59e0b",
  red:    "#ef4444",
  teal:   "#06b6d4",
  pink:   "#ec4899",
  lime:   "#84cc16",
  grid:   "rgba(255,255,255,0.05)",
  tick:   "#94a3b8",
  border: "#111827",
};

export const MULTI_COLORS = [
  COLORS.blue, COLORS.purple, COLORS.green,
  COLORS.amber, COLORS.red,   COLORS.teal,
  COLORS.pink,  COLORS.lime,
];

// ── Global Chart.js defaults ───────────────────────────────────
export function applyGlobalDefaults() {
  if (!window.Chart) return;
  Chart.defaults.font.family = "'DM Sans', sans-serif";
  Chart.defaults.color = COLORS.tick;
  Chart.defaults.plugins.legend.labels.boxWidth = 12;
  Chart.defaults.plugins.legend.labels.padding  = 16;
  Chart.defaults.plugins.tooltip.backgroundColor = "#1a2235";
  Chart.defaults.plugins.tooltip.borderColor     = "#2a3f5f";
  Chart.defaults.plugins.tooltip.borderWidth     = 1;
  Chart.defaults.plugins.tooltip.padding         = 10;
  Chart.defaults.plugins.tooltip.titleColor      = "#e2e8f0";
  Chart.defaults.plugins.tooltip.bodyColor       = "#94a3b8";
}

// ── Score Trend Line ───────────────────────────────────────────
/**
 * makeLineChart(canvasId, labels, scores)
 * Renders a clean score-over-time line chart.
 */
export function makeLineChart(canvasId, labels, scores, label = "Score") {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;
  return new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label,
        data: scores,
        borderColor: COLORS.blue,
        backgroundColor: "rgba(79,142,247,0.08)",
        fill: true,
        tension: 0.4,
        pointBackgroundColor: COLORS.blue,
        pointRadius: 4,
        pointHoverRadius: 6,
        borderWidth: 2,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: {
          min: 0, max: 100,
          grid: { color: COLORS.grid },
          ticks: { color: COLORS.tick, stepSize: 20 }
        },
        x: {
          grid: { display: false },
          ticks: { color: COLORS.tick }
        }
      }
    }
  });
}

// ── Donut / Pie ─────────────────────────────────────────────────
/**
 * makeDonut(canvasId, labels, data, colors?)
 */
export function makeDonut(canvasId, labels, data, colors = null) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;
  return new Chart(ctx, {
    type: "doughnut",
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: colors || MULTI_COLORS.slice(0, data.length),
        borderColor: COLORS.border,
        borderWidth: 3,
        hoverBorderWidth: 3,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "65%",
      plugins: {
        legend: {
          position: "bottom",
          labels: { color: COLORS.tick, padding: 14, font: { size: 12 } }
        }
      }
    }
  });
}

// ── Vertical Bar ──────────────────────────────────────────────
/**
 * makeBar(canvasId, labels, datasets)
 * datasets: [{ label, data, color }]
 */
export function makeBar(canvasId, labels, datasets) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;
  return new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: datasets.map(d => ({
        label: d.label,
        data: d.data,
        backgroundColor: d.color || COLORS.blue,
        borderRadius: 6,
        borderSkipped: false,
      }))
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: datasets.length > 1,
          position: "top",
          labels: { color: COLORS.tick, font: { size: 11 } }
        }
      },
      scales: {
        y: {
          grid: { color: COLORS.grid },
          ticks: { color: COLORS.tick }
        },
        x: {
          grid: { display: false },
          ticks: { color: COLORS.tick }
        }
      }
    }
  });
}

// ── Horizontal Bar ─────────────────────────────────────────────
/**
 * makeHBar(canvasId, labels, data, colors?)
 */
export function makeHBar(canvasId, labels, data, colors = null) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;
  return new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: colors || MULTI_COLORS.slice(0, data.length),
        borderRadius: 4,
        borderSkipped: false,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: "y",
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: COLORS.grid }, ticks: { color: COLORS.tick } },
        y: { grid: { display: false }, ticks: { color: COLORS.tick, font: { size: 11 } } }
      }
    }
  });
}

// ── Score Breakdown Radar ──────────────────────────────────────
/**
 * makeRadar(canvasId, labels, aiData, adminData?)
 */
export function makeRadar(canvasId, labels, aiData, adminData = null) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;
  const datasets = [{
    label: "AI Score",
    data: aiData,
    borderColor: COLORS.blue,
    backgroundColor: "rgba(79,142,247,0.12)",
    borderWidth: 2,
    pointBackgroundColor: COLORS.blue,
    pointRadius: 4,
  }];
  if (adminData) {
    datasets.push({
      label: "Admin Score",
      data: adminData,
      borderColor: COLORS.green,
      backgroundColor: "rgba(34,197,94,0.08)",
      borderWidth: 2,
      pointBackgroundColor: COLORS.green,
      pointRadius: 4,
    });
  }
  return new Chart(ctx, {
    type: "radar",
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          min: 0, max: 20,
          grid: { color: COLORS.grid },
          pointLabels: { color: COLORS.tick, font: { size: 11 } },
          ticks: { color: COLORS.tick, backdropColor: "transparent", stepSize: 5 }
        }
      },
      plugins: {
        legend: {
          display: !!adminData,
          position: "bottom",
          labels: { color: COLORS.tick, font: { size: 11 } }
        }
      }
    }
  });
}

// ── Score bucket bar (0-39, 40-59, 60-79, 80-100) ─────────────
export function makeBucketChart(canvasId, assessments) {
  const buckets = [0, 0, 0, 0];
  assessments.forEach(a => {
    if (a.ai_score === null) return;
    const s = Number(a.ai_score);
    if (s < 40) buckets[0]++;
    else if (s < 60) buckets[1]++;
    else if (s < 80) buckets[2]++;
    else buckets[3]++;
  });
  return makeBar(
    canvasId,
    ["0–39", "40–59", "60–79", "80–100"],
    [{ data: buckets, color: [COLORS.red, COLORS.amber, COLORS.blue, COLORS.green] }]
  );
}

// ── Domain submission breakdown ────────────────────────────────
export function makeDomainChart(canvasId, assessments) {
  const counts = {};
  assessments.forEach(a => {
    if (a.domain) counts[a.domain] = (counts[a.domain] || 0) + 1;
  });
  const labels = Object.keys(counts);
  const data   = Object.values(counts);
  return makeHBar(canvasId, labels, data, MULTI_COLORS.slice(0, labels.length));
}

// ── Utility: compute stats ─────────────────────────────────────
export function computeStats(assessments) {
  const scored = assessments.filter(a => a.ai_score !== null);
  if (!scored.length) return { avg: 0, highest: 0, lowest: 0, total: assessments.length, pending: assessments.length, scored: 0 };
  const scores = scored.map(a => Number(a.ai_score));
  return {
    total:    assessments.length,
    scored:   scored.length,
    pending:  assessments.length - scored.length,
    avg:      Math.round(scores.reduce((s, v) => s + v, 0) / scores.length),
    highest:  Math.max(...scores),
    lowest:   Math.min(...scores),
  };
}

// ── Utility: format date ───────────────────────────────────────
export function fmtDate(ts, opts = { day: "numeric", month: "short", year: "numeric" }) {
  return ts?.toDate?.()?.toLocaleDateString("en-IN", opts) || "—";
}

// ── Utility: score colour class ───────────────────────────────
export function scoreColorVar(score) {
  if (score >= 75) return "var(--green)";
  if (score >= 50) return "var(--amber)";
  return "var(--red)";
}

export function scoreBadgeClass(score) {
  if (score >= 75) return "badge-green";
  if (score >= 50) return "badge-amber";
  return "badge-red";
}

export function scoreLabel(score) {
  if (score >= 85) return "Excellent";
  if (score >= 70) return "Good";
  if (score >= 50) return "Average";
  return "Needs Work";
}