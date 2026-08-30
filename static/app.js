/**
 * AuditDesk Client-Side Application Logic
 * Interactive UI reactivity, Benford's Law Chart rendering, API connectors, and Workpaper state management.
 */

let CURRENT_DATASET = [];
let BENFORD_CHART = null;
let VENDOR_SPEND_CHART = null;
let DAILY_VOLUME_CHART = null;
let ANOMALY_DONUT_CHART = null;

// Initialization
document.addEventListener("DOMContentLoaded", () => {
  loadStoredAISettings();
  initAllCharts();
  fetchCurrentDataset();
  updateRiskScore();
});

// Navigation / Tabs
function switchTab(tabId) {
  document.querySelectorAll(".tab-content").forEach(el => el.classList.add("hidden"));
  document.getElementById(tabId).classList.remove("hidden");

  document.querySelectorAll(".nav-btn").forEach(btn => {
    btn.classList.remove("text-white", "bg-indigo-600/20", "border", "border-indigo-500/30");
    btn.classList.add("text-slate-300");
  });

  const activeBtn = document.getElementById("nav-" + tabId);
  if (activeBtn) {
    activeBtn.classList.add("text-white", "bg-indigo-600/20", "border", "border-indigo-500/30");
    activeBtn.classList.remove("text-slate-300");
  }
}

// 1. Data Studio Logic
async function fetchCurrentDataset() {
  try {
    const res = await fetch("/api/dataset/current");
    const data = await res.json();
    if (data.records && data.records.length > 0) {
      renderDataset(data.records, data.meta);
    } else {
      loadDemoData();
    }
  } catch (err) {
    console.error("Failed to fetch dataset:", err);
  }
}

async function loadDemoData() {
  try {
    const res = await fetch("/api/dataset/load-demo");
    const data = await res.json();
    if (data.success) {
      renderDataset(data.records, data.meta);
      alert("Demo Accounts Payable dataset loaded successfully!");
    }
  } catch (err) {
    alert("Error loading demo dataset: " + err);
  }
}

function renderDataset(records, meta) {
  CURRENT_DATASET = records;
  document.getElementById("meta-dataset-name").innerText = meta.name || "Loaded Dataset";
  document.getElementById("meta-row-count").innerText = `${records.length} Records`;
  
  const totalAmt = records.reduce((sum, r) => sum + (parseFloat(r.amount) || 0), 0);
  document.getElementById("meta-total-amount").innerText = "$" + totalAmt.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  const tbody = document.getElementById("grid-body");
  tbody.innerHTML = "";

  records.forEach((r, idx) => {
    const tr = document.createElement("tr");
    tr.className = "hover:bg-slate-800/40 transition";
    tr.innerHTML = `
      <td class="p-3 font-mono text-indigo-300">${r.invoice_no || r.id || idx + 1}</td>
      <td class="p-3 font-semibold text-white">${r.vendor || "N/A"}</td>
      <td class="p-3 text-right font-mono text-emerald-400 font-bold">$${(parseFloat(r.amount) || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
      <td class="p-3 text-slate-400">${r.date || "N/A"}</td>
      <td class="p-3 text-slate-400">${r.cost_center || "N/A"}</td>
      <td class="p-3 text-slate-400">${r.approver || "N/A"}</td>
      <td class="p-3 text-slate-400 truncate max-w-xs">${r.description || ""}</td>
    `;
    tbody.appendChild(tr);
  });

  updateDataStudioCharts(records);
}

function updateDataStudioCharts(records) {
  if (!records || records.length === 0) return;

  // 1. Vendor Spend Concentration (Top 5)
  const vendorTotals = {};
  records.forEach(r => {
    const v = r.vendor || "Unknown Vendor";
    const amt = parseFloat(r.amount) || 0;
    vendorTotals[v] = (vendorTotals[v] || 0) + amt;
  });

  const sortedVendors = Object.entries(vendorTotals)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  if (VENDOR_SPEND_CHART) {
    VENDOR_SPEND_CHART.data.labels = sortedVendors.map(x => x[0].length > 18 ? x[0].substring(0, 16) + '...' : x[0]);
    VENDOR_SPEND_CHART.data.datasets[0].data = sortedVendors.map(x => x[1]);
    VENDOR_SPEND_CHART.update();
  }

  // 2. Daily / Day of Week Posting Distribution
  const daysMap = { "Mon": 0, "Tue": 0, "Wed": 0, "Thu": 0, "Fri": 0, "Sat": 0, "Sun": 0 };
  const dayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

  records.forEach(r => {
    if (r.date) {
      try {
        const d = new Date(r.date);
        if (!isNaN(d.getDay())) {
          const dayName = dayNames[d.getDay()];
          daysMap[dayName] = (daysMap[dayName] || 0) + 1;
        }
      } catch (e) {}
    }
  });

  if (DAILY_VOLUME_CHART) {
    DAILY_VOLUME_CHART.data.datasets[0].data = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map(d => daysMap[d]);
    DAILY_VOLUME_CHART.update();
  }
}

function handleFileUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = async (e) => {
    const csvText = e.target.result;
    try {
      const res = await fetch("/api/dataset/upload-csv", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ csv_text: csvText, file_name: file.name })
      });
      const data = await res.json();
      if (data.success) {
        renderDataset(data.records, data.meta);
        alert(`Successfully ingested ${file.name} (${data.records.length} rows).`);
      }
    } catch (err) {
      alert("Failed to upload CSV: " + err);
    }
  };
  reader.readAsText(file);
}

function filterGrid() {
  const query = document.getElementById("grid-search").value.toLowerCase();
  const filtered = CURRENT_DATASET.filter(r => 
    (r.vendor && r.vendor.toLowerCase().includes(query)) ||
    (r.invoice_no && r.invoice_no.toLowerCase().includes(query)) ||
    (r.cost_center && r.cost_center.toLowerCase().includes(query)) ||
    (r.description && r.description.toLowerCase().includes(query))
  );

  const tbody = document.getElementById("grid-body");
  tbody.innerHTML = "";
  filtered.forEach((r, idx) => {
    const tr = document.createElement("tr");
    tr.className = "hover:bg-slate-800/40 transition";
    tr.innerHTML = `
      <td class="p-3 font-mono text-indigo-300">${r.invoice_no || r.id || idx + 1}</td>
      <td class="p-3 font-semibold text-white">${r.vendor || "N/A"}</td>
      <td class="p-3 text-right font-mono text-emerald-400 font-bold">$${(parseFloat(r.amount) || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
      <td class="p-3 text-slate-400">${r.date || "N/A"}</td>
      <td class="p-3 text-slate-400">${r.cost_center || "N/A"}</td>
      <td class="p-3 text-slate-400">${r.approver || "N/A"}</td>
      <td class="p-3 text-slate-400 truncate max-w-xs">${r.description || ""}</td>
    `;
    tbody.appendChild(tr);
  });
}

// 2. Forensic Scanner Logic
async function runForensics() {
  const threshold = parseFloat(document.getElementById("forensic-threshold").value) || 5000.0;
  const buffer_pct = parseFloat(document.getElementById("forensic-buffer").value) || 0.15;

  try {
    const res = await fetch("/api/forensics/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ threshold, buffer_pct })
    });

    const data = await res.json();
    if (data.success) {
      const sum = data.summary;
      document.getElementById("card-split-count").innerText = `${sum.split_count} Items`;
      document.getElementById("card-duplicate-count").innerText = `${sum.duplicate_count} Pairs`;
      document.getElementById("card-weekend-count").innerText = `${sum.out_of_hours_count} Entries`;
      document.getElementById("card-benford-status").innerText = sum.benford_status.split(" ")[0] || "Calculated";

      const details = data.details;

      // Populate Splits Table
      const splitsBody = document.getElementById("table-splits-body");
      splitsBody.innerHTML = "";
      if (details.splits && details.splits.length > 0) {
        document.getElementById("badge-splits-total").innerText = `${details.splits.length} flagged`;
        details.splits.forEach(item => {
          const tr = document.createElement("tr");
          tr.className = "hover:bg-slate-800/40";
          tr.innerHTML = `
            <td class="p-2.5 font-mono text-amber-300 font-semibold">${item.invoice_no || item.id}</td>
            <td class="p-2.5 font-medium text-white">${item.vendor || "N/A"}</td>
            <td class="p-2.5 text-right font-mono text-amber-400 font-bold">$${(parseFloat(item.amount) || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
            <td class="p-2.5 text-slate-400 truncate max-w-xs">${item.risk_reason || "Near threshold limit"}</td>
          `;
          splitsBody.appendChild(tr);
        });
      } else {
        splitsBody.innerHTML = '<tr><td colspan="4" class="p-4 text-center text-slate-500">No split transactions detected.</td></tr>';
      }

      // Populate Duplicates Table
      const dupesBody = document.getElementById("table-duplicates-body");
      dupesBody.innerHTML = "";
      if (details.duplicates && details.duplicates.length > 0) {
        document.getElementById("badge-duplicates-total").innerText = `${details.duplicates.length} flagged`;
        details.duplicates.forEach(pair => {
          const item1 = pair.item1 || {};
          const item2 = pair.item2 || {};
          const tr = document.createElement("tr");
          tr.className = "hover:bg-slate-800/40";
          tr.innerHTML = `
            <td class="p-2.5 font-bold text-red-400">${pair.type || "Duplicate Match"}</td>
            <td class="p-2.5 font-medium text-white">${item1.vendor || "N/A"}</td>
            <td class="p-2.5 text-right font-mono text-red-400 font-bold">$${(parseFloat(item1.amount) || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
            <td class="p-2.5 font-mono text-[11px] text-slate-400">${item1.invoice_no} vs ${item2.invoice_no}</td>
          `;
          dupesBody.appendChild(tr);
        });
      } else {
        dupesBody.innerHTML = '<tr><td colspan="4" class="p-4 text-center text-slate-500">No duplicate payments found.</td></tr>';
      }

      // Update Charts
      updateBenfordChart(details.benford);
      updateAnomalyDonutChart(CURRENT_DATASET.length, details.splits.length, details.duplicates.length, details.out_of_hours.length);
    }
  } catch (err) {
    alert("Error running forensic analysis: " + err);
  }
}

function initAllCharts() {
  // 1. Benford Chart
  const ctxBenford = document.getElementById("benfordChart").getContext("2d");
  BENFORD_CHART = new Chart(ctxBenford, {
    type: "bar",
    data: {
      labels: ["1", "2", "3", "4", "5", "6", "7", "8", "9"],
      datasets: [
        {
          label: "Expected (Benford's Law %)",
          data: [30.1, 17.6, 12.5, 9.7, 7.9, 6.7, 5.8, 5.1, 4.6],
          backgroundColor: "rgba(99, 102, 241, 0.4)",
          borderColor: "#6366f1",
          borderWidth: 1.5
        },
        {
          label: "Observed Dataset Frequency (%)",
          data: [0, 0, 0, 0, 0, 0, 0, 0, 0],
          backgroundColor: "rgba(245, 158, 11, 0.7)",
          borderColor: "#f59e0b",
          borderWidth: 1.5
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: "rgba(255, 255, 255, 0.05)" },
          ticks: { color: "#94a3b8" }
        },
        x: {
          grid: { display: false },
          ticks: { color: "#94a3b8" }
        }
      },
      plugins: {
        legend: { labels: { color: "#cbd5e1", font: { size: 11 } } }
      }
    }
  });

  // 2. Vendor Spend Bar Chart
  const ctxVendor = document.getElementById("vendorSpendChart").getContext("2d");
  VENDOR_SPEND_CHART = new Chart(ctxVendor, {
    type: "bar",
    data: {
      labels: ["Vendor A", "Vendor B", "Vendor C", "Vendor D", "Vendor E"],
      datasets: [{
        label: "Spend ($)",
        data: [0, 0, 0, 0, 0],
        backgroundColor: "rgba(99, 102, 241, 0.8)",
        borderRadius: 4
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          grid: { color: "rgba(255, 255, 255, 0.05)" },
          ticks: { color: "#94a3b8", callback: (val) => '$' + (val >= 1000 ? (val/1000) + 'k' : val) }
        },
        y: {
          grid: { display: false },
          ticks: { color: "#cbd5e1", font: { size: 10 } }
        }
      },
      plugins: {
        legend: { display: false }
      }
    }
  });

  // 3. Daily Volume Line Chart
  const ctxDaily = document.getElementById("dailyVolumeChart").getContext("2d");
  DAILY_VOLUME_CHART = new Chart(ctxDaily, {
    type: "line",
    data: {
      labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
      datasets: [{
        label: "Postings",
        data: [0, 0, 0, 0, 0, 0, 0],
        borderColor: "#10b981",
        backgroundColor: "rgba(16, 185, 129, 0.15)",
        fill: true,
        tension: 0.35,
        pointBackgroundColor: "#10b981"
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: "rgba(255, 255, 255, 0.05)" },
          ticks: { color: "#94a3b8", stepSize: 1 }
        },
        x: {
          grid: { display: false },
          ticks: { color: "#94a3b8" }
        }
      },
      plugins: {
        legend: { display: false }
      }
    }
  });

  // 4. Anomaly Donut Chart
  const ctxDonut = document.getElementById("anomalyDonutChart").getContext("2d");
  ANOMALY_DONUT_CHART = new Chart(ctxDonut, {
    type: "doughnut",
    data: {
      labels: ["Normal Transactions", "Split PO Limits", "Duplicate Payments", "Weekend Postings"],
      datasets: [{
        data: [100, 0, 0, 0],
        backgroundColor: ["#334155", "#f59e0b", "#ef4444", "#a855f7"],
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "70%",
      plugins: {
        legend: {
          position: "bottom",
          labels: { color: "#cbd5e1", boxWidth: 10, font: { size: 10 } }
        }
      }
    }
  });
}

function updateBenfordChart(benfordData) {
  if (!benfordData || !benfordData.digits) return;
  const observed = benfordData.digits.map(d => d.observed_pct);
  BENFORD_CHART.data.datasets[1].data = observed;
  BENFORD_CHART.update();
  document.getElementById("benford-stat-badge").innerText = `Chi-Square: ${benfordData.chi_square} (${benfordData.conformity})`;
}

function updateAnomalyDonutChart(totalRows, splitsCount, dupesCount, weekendCount) {
  if (!ANOMALY_DONUT_CHART) return;
  const totalAnomalies = splitsCount + dupesCount + weekendCount;
  const normalRows = Math.max(0, totalRows - totalAnomalies);
  ANOMALY_DONUT_CHART.data.datasets[0].data = [normalRows, splitsCount, dupesCount, weekendCount];
  ANOMALY_DONUT_CHART.update();
}

// 3. Sampling Studio Logic
async function drawSample() {
  const method = document.getElementById("sampling-method").value;
  const confidence = parseFloat(document.getElementById("sampling-confidence").value);
  const tdr = parseFloat(document.getElementById("sampling-tdr").value) / 100.0;
  const epdr = parseFloat(document.getElementById("sampling-epdr").value) / 100.0;
  const seed = parseInt(document.getElementById("sampling-seed").value) || 42;

  try {
    const res = await fetch("/api/sampling/draw", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ method, confidence, tdr, epdr, seed })
    });
    const data = await res.json();
    if (data.success) {
      const result = data.result;
      document.getElementById("sample-count-badge").innerText = `${result.sample_size} Items Extracted (Seed: ${result.seed})`;
      document.getElementById("sample-rationale-text").innerText = result.rationale;

      const tbody = document.getElementById("table-sample-body");
      tbody.innerHTML = "";

      result.sample.forEach((item, idx) => {
        const tr = document.createElement("tr");
        tr.className = "hover:bg-slate-800/40";
        tr.innerHTML = `
          <td class="p-2.5 font-mono text-slate-500">${idx + 1}</td>
          <td class="p-2.5 font-mono text-emerald-300 font-semibold">${item.invoice_no || item.id}</td>
          <td class="p-2.5 font-medium text-white">${item.vendor || "N/A"}</td>
          <td class="p-2.5 text-right font-mono text-emerald-400 font-bold">$${(parseFloat(item.amount) || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
          <td class="p-2.5">
            <select class="bg-slate-900 text-[11px] border border-slate-700 rounded px-2 py-1 text-slate-200 focus:outline-none">
              <option value="Compliant">✓ Compliant (Supported)</option>
              <option value="Deviation">✗ Deviation / Exception</option>
              <option value="Not Tested" selected>• Not Tested</option>
            </select>
          </td>
          <td class="p-2.5">
            <input type="text" placeholder="Add testing initials/notes..." class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-[11px] text-slate-200">
          </td>
        `;
        tbody.appendChild(tr);
      });
    }
  } catch (err) {
    alert("Error drawing sample: " + err);
  }
}

// 4. IIA 5C Finding Drafter Logic
function handleTopicChange() {
  const topic = document.getElementById("finding-topic-select").value;
  const titleInput = document.getElementById("finding-title");
  const policyInput = document.getElementById("finding-policy-input");

  if (topic === "splits") {
    titleInput.value = "Circumvention of Delegation of Authority Approval Thresholds (Split POs)";
    policyInput.value = "Delegation of Authority (DOA) Policy Section 4.1 & Procurement SOP";
  } else if (topic === "duplicates") {
    titleInput.value = "Duplicate Vendor Disbursements and Insufficient Invoicing Controls";
    policyInput.value = "Financial Control Standard 2.4 (3-Way Matching & Duplicate Verification)";
  } else if (topic === "weekends") {
    titleInput.value = "Non-Business Hours and Weekend Journal Entries Without Supervisory Approval";
    policyInput.value = "Financial Reporting SOP 5.1 (Standard Business Hours & Posting Controls)";
  } else if (topic === "benford") {
    titleInput.value = "Benford's Law Non-Conformity and Irregular Numeric Distribution in Ledger";
    policyInput.value = "IIA Fraud Risk Management Standard 2120.A1 (Forensic Ledger Integrity)";
  } else {
    titleInput.value = "Comprehensive Accounts Payable Internal Control & Compliance Observations";
    policyInput.value = "Corporate Procurement, DOA Policy, and Financial Reporting Framework";
  }
}

async function draft5CFinding() {
  const btn = document.getElementById("btn-draft-5c");
  const origHtml = btn.innerHTML;
  btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i><span>Synthesizing 5C Finding...</span>';
  btn.disabled = true;

  const aiConfig = getAIConfig();
  const title = document.getElementById("finding-title").value;
  const policy = document.getElementById("finding-policy-input").value;
  const topic = document.getElementById("finding-topic-select").value;

  try {
    const res = await fetch("/api/ai/draft-5c", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        provider: aiConfig.provider,
        api_key: aiConfig.api_key,
        model: aiConfig.model,
        custom_endpoint: aiConfig.custom_endpoint,
        title: title,
        policy_context: policy,
        topic: topic,
        department: "Procurement & Accounts Payable"
      })
    });
    const data = await res.json();
    if (data.success && data.finding) {
      const f = data.finding;
      document.getElementById("finding-title").value = f.title || title;
      document.getElementById("finding-condition").value = f.condition || "";
      document.getElementById("finding-criteria").value = f.criteria || "";
      document.getElementById("finding-cause").value = f.cause || "";
      document.getElementById("finding-consequence").value = f.consequence || "";
      document.getElementById("finding-action").value = f.corrective_action || "";

      if (f.likelihood_score) document.getElementById("range-likelihood").value = f.likelihood_score;
      if (f.impact_score) document.getElementById("range-impact").value = f.impact_score;
      updateRiskScore();
    }
  } catch (err) {
    alert("Error drafting 5C finding: " + err);
  } finally {
    btn.innerHTML = origHtml;
    btn.disabled = false;
  }
}

function updateRiskScore() {
  const l = parseInt(document.getElementById("range-likelihood").value);
  const i = parseInt(document.getElementById("range-impact").value);
  document.getElementById("score-likelihood-val").innerText = `${l} / 5`;
  document.getElementById("score-impact-val").innerText = `${i} / 5`;

  const total = l * i;
  const badge = document.getElementById("badge-overall-risk");
  if (total >= 15) {
    badge.innerText = `CRITICAL RISK (${total})`;
    badge.className = "text-xl font-extrabold text-red-500 mt-1";
  } else if (total >= 10) {
    badge.innerText = `HIGH RISK (${total})`;
    badge.className = "text-xl font-extrabold text-orange-500 mt-1";
  } else if (total >= 5) {
    badge.innerText = `MEDIUM RISK (${total})`;
    badge.className = "text-xl font-extrabold text-amber-400 mt-1";
  } else {
    badge.innerText = `LOW RISK (${total})`;
    badge.className = "text-xl font-extrabold text-emerald-400 mt-1";
  }
}

// 5. Workpaper & Sign-off State Machine
async function signoffWorkpaper(action) {
  const name = action === "prepare" 
    ? document.getElementById("sign-preparer-name").value 
    : document.getElementById("sign-reviewer-name").value;

  try {
    const res = await fetch("/api/workpaper/signoff", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, user_name: name })
    });
    const data = await res.json();
    if (data.success) {
      const status = data.workpaper.status;
      document.getElementById("header-status-badge").innerText = `✓ ${status}`;
      alert(`Workpaper successfully signed off as '${action.toUpperCase()}' by ${name}. Status: ${status}`);
    }
  } catch (err) {
    alert("Sign-off error: " + err);
  }
}

// 5b. Full Executive Report Logic
async function generateFullAuditReport() {
  const btn = document.getElementById("btn-generate-full-report");
  const origHtml = btn.innerHTML;
  btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i><span>Synthesizing Board Report...</span>';
  btn.disabled = true;

  const aiConfig = getAIConfig();
  const container = document.getElementById("full-report-container");

  try {
    const res = await fetch("/api/ai/draft-full-report", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        provider: aiConfig.provider,
        api_key: aiConfig.api_key,
        model: aiConfig.model,
        custom_endpoint: aiConfig.custom_endpoint,
        engagement_title: "Accounts Payable & Procurement Fieldwork Audit",
        audit_scope: "Review of vendor procurement, split delegation of authority limits, duplicate invoicing, and non-business hours postings."
      })
    });
    const data = await res.json();
    if (data.success && data.report) {
      const rep = data.report;
      
      const opinionColor = rep.overall_opinion === "Satisfactory" 
        ? "border-emerald-500 text-emerald-400 bg-emerald-950/30"
        : (rep.overall_opinion === "Needs Improvement" ? "border-amber-500 text-amber-400 bg-amber-950/30" : "border-red-500 text-red-400 bg-red-950/30");

      let findingsHtml = "";
      (rep.key_findings || []).forEach((f, idx) => {
        findingsHtml += `
          <div class="glass-panel p-4 rounded-xl space-y-3 border-l-4 ${f.risk_rating === 'Critical' ? 'border-red-500' : 'border-amber-500'}">
            <div class="flex items-center justify-between">
              <span class="font-bold text-sm text-white">Observation ${idx + 1}: ${f.title}</span>
              <span class="px-2 py-0.5 rounded text-[10px] font-bold ${f.risk_rating === 'Critical' ? 'bg-red-500/20 text-red-400' : 'bg-amber-500/20 text-amber-400'}">${f.risk_rating || 'High'} Risk</span>
            </div>
            <div class="grid grid-cols-1 gap-2 text-xs">
              <div><strong class="text-indigo-300">Condition:</strong> <span class="text-slate-300">${f.condition}</span></div>
              <div><strong class="text-blue-300">Criteria:</strong> <span class="text-slate-400">${f.criteria}</span></div>
              <div><strong class="text-amber-300">Root Cause:</strong> <span class="text-slate-400">${f.cause}</span></div>
              <div><strong class="text-red-300">Consequence:</strong> <span class="text-slate-300">${f.consequence}</span></div>
              <div class="p-2.5 rounded bg-slate-950/60 border border-slate-800"><strong class="text-emerald-300">Recommendation:</strong> <span class="text-slate-200">${f.corrective_action}</span></div>
            </div>
          </div>
        `;
      });

      let actionsHtml = "";
      (rep.management_action_plan || []).forEach((act, idx) => {
        actionsHtml += `
          <tr class="hover:bg-slate-800/40 transition">
            <td class="p-3 font-mono text-slate-500">${idx + 1}</td>
            <td class="p-3 font-medium text-white">${act.action_item}</td>
            <td class="p-3 text-slate-300">${act.owner}</td>
            <td class="p-3"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${act.priority === 'High' ? 'bg-red-500/20 text-red-400' : 'bg-amber-500/20 text-amber-400'}">${act.priority}</span></td>
            <td class="p-3 font-mono text-indigo-300">${act.target_days}</td>
          </tr>
        `;
      });

      container.innerHTML = `
        <!-- Audit Opinion Banner -->
        <div class="p-5 rounded-xl border ${opinionColor} flex items-center justify-between">
          <div>
            <div class="text-xs uppercase font-bold tracking-wider">Overall Internal Audit Opinion</div>
            <div class="text-2xl font-extrabold mt-1">${rep.overall_opinion}</div>
          </div>
          <i class="fa-solid fa-stamp text-4xl opacity-40"></i>
        </div>

        <!-- Executive Summary -->
        <div class="glass-panel p-5 rounded-xl space-y-2">
          <h4 class="font-bold text-xs uppercase tracking-wider text-indigo-400">Executive Summary & Context</h4>
          <p class="text-xs text-slate-200 leading-relaxed">${rep.executive_summary}</p>
        </div>

        <!-- Root Cause Analysis -->
        <div class="glass-panel p-5 rounded-xl space-y-2">
          <h4 class="font-bold text-xs uppercase tracking-wider text-amber-400">Systemic Root Cause Assessment</h4>
          <p class="text-xs text-slate-300 leading-relaxed">${rep.root_cause_summary}</p>
        </div>

        <!-- Key Observations -->
        <div class="space-y-3">
          <h4 class="font-bold text-sm text-white flex items-center gap-2">
            <i class="fa-solid fa-triangle-exclamation text-amber-400"></i> Key Audit Observations & 5C Analysis
          </h4>
          ${findingsHtml}
        </div>

        <!-- Management Action Plan (CAPA) -->
        <div class="glass-panel rounded-xl overflow-hidden">
          <div class="p-4 border-b border-slate-800 flex items-center justify-between">
            <h4 class="font-bold text-xs uppercase tracking-wider text-emerald-400">Prioritized Management Action Plan (CAPA)</h4>
          </div>
          <table class="w-full text-left text-xs text-slate-300">
            <thead class="bg-slate-950 text-[10px] text-slate-400">
              <tr>
                <th class="p-3">#</th>
                <th class="p-3">Corrective Action Item</th>
                <th class="p-3">Responsible Owner</th>
                <th class="p-3">Priority</th>
                <th class="p-3">Target Timeline</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-800/60">
              ${actionsHtml}
            </tbody>
          </table>
        </div>
      `;
    }
  } catch (err) {
    alert("Error generating full audit report: " + err);
  } finally {
    btn.innerHTML = origHtml;
    btn.disabled = false;
  }
}

// 6. Export Functions
async function exportHtmlMemo() {
  try {
    const finding = {
      title: document.getElementById("finding-title").value,
      condition: document.getElementById("finding-condition").value,
      criteria: document.getElementById("finding-criteria").value,
      cause: document.getElementById("finding-cause").value,
      consequence: document.getElementById("finding-consequence").value,
      corrective_action: document.getElementById("finding-action").value,
      likelihood_score: document.getElementById("range-likelihood").value,
      impact_score: document.getElementById("range-impact").value,
      risk_rating: document.getElementById("badge-overall-risk").innerText.split(" ")[0]
    };

    const res = await fetch("/api/export/html-memo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ finding })
    });
    const data = await res.json();
    if (data.success && data.html) {
      const blob = new Blob([data.html], { type: "text/html" });
      const url = URL.createObjectURL(blob);
      const win = window.open(url, "_blank");
      if (!win) {
        const a = document.createElement("a");
        a.href = url;
        a.download = "Audit_Observation_Memo.html";
        a.click();
      }
    }
  } catch (err) {
    alert("Export failed: " + err);
  }
}

async function exportExcelXml() {
  try {
    const res = await fetch("/api/export/excel-xml", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({})
    });
    const data = await res.json();
    if (data.success && data.xml) {
      const blob = new Blob([data.xml], { type: "application/vnd.ms-excel" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "AuditDesk_Master_Workpaper.xls";
      a.click();
    }
  } catch (err) {
    alert("Excel export failed: " + err);
  }
}

async function exportIcaewDocx() {
  try {
    const res = await fetch("/api/export/icaew-docx", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({})
    });
    
    if (!res.ok) {
      throw new Error(`Server returned HTTP ${res.status}`);
    }

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "IIA_Internal_Audit_Report.docx";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (err) {
    alert("IIA DOCX export failed: " + err);
  }
}

// 7. BYOK AI Configuration
function updateProviderFields() {
  const provider = document.getElementById("ai-provider").value;
  const keyField = document.getElementById("field-api-key");
  const modelField = document.getElementById("field-model");
  const endField = document.getElementById("field-endpoint");

  if (provider === "offline") {
    keyField.classList.add("hidden");
    modelField.classList.add("hidden");
    endField.classList.add("hidden");
  } else if (provider === "ollama" || provider === "custom") {
    keyField.classList.remove("hidden");
    modelField.classList.remove("hidden");
    endField.classList.remove("hidden");
  } else {
    keyField.classList.remove("hidden");
    modelField.classList.remove("hidden");
    endField.classList.add("hidden");
  }
}

function saveAISettings() {
  const provider = document.getElementById("ai-provider").value;
  const key = document.getElementById("ai-api-key").value;
  const model = document.getElementById("ai-model").value;
  const endpoint = document.getElementById("ai-endpoint").value;

  localStorage.setItem("auditdesk_ai_provider", provider);
  localStorage.setItem("auditdesk_ai_key", key);
  localStorage.setItem("auditdesk_ai_model", model);
  localStorage.setItem("auditdesk_ai_endpoint", endpoint);

  document.getElementById("header-ai-badge").innerText = provider.toUpperCase();
  alert("AI Settings successfully saved to local browser storage!");
}

function loadStoredAISettings() {
  const provider = localStorage.getItem("auditdesk_ai_provider") || "offline";
  const key = localStorage.getItem("auditdesk_ai_key") || "";
  const model = localStorage.getItem("auditdesk_ai_model") || "";
  const endpoint = localStorage.getItem("auditdesk_ai_endpoint") || "";

  document.getElementById("ai-provider").value = provider;
  document.getElementById("ai-api-key").value = key;
  document.getElementById("ai-model").value = model;
  document.getElementById("ai-endpoint").value = endpoint;

  updateProviderFields();
  document.getElementById("header-ai-badge").innerText = provider.toUpperCase();
}

function getAIConfig() {
  return {
    provider: localStorage.getItem("auditdesk_ai_provider") || "offline",
    api_key: localStorage.getItem("auditdesk_ai_key") || "",
    model: localStorage.getItem("auditdesk_ai_model") || "",
    custom_endpoint: localStorage.getItem("auditdesk_ai_endpoint") || ""
  };
}

// 8. Single Button Solution: 1-Click Auto-Pilot Audit Pipeline
async function runAutoPilotAudit() {
  const headerBtn = document.getElementById("btn-autopilot-header");
  const bannerBtn = document.getElementById("btn-autopilot-banner");

  const originalHeaderHtml = headerBtn ? headerBtn.innerHTML : "";
  const originalBannerHtml = bannerBtn ? bannerBtn.innerHTML : "";

  if (headerBtn) {
    headerBtn.disabled = true;
    headerBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin text-amber-200"></i> <span>Running Auto-Pilot...</span>';
  }
  if (bannerBtn) {
    bannerBtn.disabled = true;
    bannerBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin text-amber-200"></i> <span>Running Full Fieldwork Pipeline...</span>';
  }

  try {
    const aiConfig = getAIConfig();
    const res = await fetch("/api/autopilot/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        threshold: 5000.0,
        buffer_pct: 0.15,
        provider: aiConfig.provider,
        api_key: aiConfig.api_key,
        model: aiConfig.model,
        custom_endpoint: aiConfig.custom_endpoint,
        engagement_title: "Accounts Payable & Procurement Fieldwork Audit"
      })
    });

    const data = await res.json();

    if (data.success) {
      // 1. Hydrate Dataset Grid & Stats
      if (data.records) {
        renderDataset(data.records, data.meta);
      }

      // 2. Hydrate Forensics
      if (data.anomalies) {
        const anoms = data.anomalies;
        document.getElementById("badge-split-count").innerText = (anoms.splits || []).length;
        document.getElementById("badge-duplicate-count").innerText = (anoms.duplicates || []).length;
        document.getElementById("badge-weekend-count").innerText = (anoms.out_of_hours || []).length;
        document.getElementById("badge-benford-status").innerText = (anoms.benford && anoms.benford.conformity) ? anoms.benford.conformity.split(" ")[0] : "Assessed";
        
        if (anoms.benford && anoms.benford.actual_distribution) {
          updateBenfordChart(anoms.benford.actual_distribution);
        }
        updateAnomalyDonutChart(
          (data.records || CURRENT_DATASET).length,
          (anoms.splits || []).length,
          (anoms.duplicates || []).length,
          (anoms.out_of_hours || []).length
        );
      }

      // 3. Hydrate Sample
      const sampleItems = (data.sample && (data.sample.sample || data.sample.sampled_items)) || [];
      if (sampleItems.length > 0) {
        renderSampleTable(sampleItems);
        document.getElementById("sample-rationale-box").innerText = data.sample.rationale || "AICPA statistical attribute sample drawn.";
      }

      // 4. Hydrate Executive Report & 5C Observations
      if (data.report) {
        renderFullAuditReport(data.report);
      }

      // 5. Hydrate Workpaper status
      if (data.workpaper) {
        document.getElementById("wp-status-val").innerText = data.workpaper.status || "Prepared";
        document.getElementById("header-status-badge").innerText = data.workpaper.status || "Prepared";
      }

      // Switch to Executive Report tab
      switchTab("report-tab");

      alert("⚡ Auto-Pilot Fieldwork Completed Successfully!\n\n• Ingested & Scanned Dataset\n• Detected DOA Splits & Duplicate Disbursements\n• Calculated Benford's Law Chi-Square\n• Extracted AICPA Statistical Sample\n• Synthesized Full IIA Board Report with AI\n\nYou can now 1-click download your DOCX or XLSX workpapers!");
    } else {
      alert("Auto-Pilot failed: " + (data.error || "Unknown error"));
    }
  } catch (err) {
    alert("Auto-Pilot execution error: " + err);
  } finally {
    if (headerBtn) {
      headerBtn.disabled = false;
      headerBtn.innerHTML = originalHeaderHtml;
    }
    if (bannerBtn) {
      bannerBtn.disabled = false;
      bannerBtn.innerHTML = originalBannerHtml;
    }
  }
}


