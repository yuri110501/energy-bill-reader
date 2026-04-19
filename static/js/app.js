/**
 * Energy Bill Reader — Frontend Application
 */

// ===== DOM Elements =====
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const els = {
  navUpload: $('#nav-upload'),
  navHistory: $('#nav-history'),
  viewUpload: $('#view-upload'),
  viewHistory: $('#view-history'),
  uploadZone: $('#upload-zone'),
  fileInput: $('#file-input'),
  filePreview: $('#file-preview'),
  filePreviewImg: $('#file-preview-img'),
  fileName: $('#file-name'),
  fileSize: $('#file-size'),
  btnRemoveFile: $('#btn-remove-file'),
  btnProcess: $('#btn-process'),
  processingContainer: $('#processing-container'),
  resultsContainer: $('#results-container'),
  resultsGrid: $('#results-grid'),
  errorContainer: $('#error-container'),
  errorMessage: $('#error-message'),
  btnNewUpload: $('#btn-new-upload'),
  btnRetry: $('#btn-retry'),
  btnCopyJson: $('#btn-copy-json'),
  btnDownloadJson: $('#btn-download-json'),
  btnRefreshHistory: $('#btn-refresh-history'),
  btnGoUpload: $('#btn-go-upload'),
  searchInput: $('#search-input'),
  historyCount: $('#history-count'),
  tableBody: $('#table-body'),
  dataTable: $('#data-table'),
  tableEmpty: $('#table-empty'),
  statTotal: $('#stat-total'),
  statAvgValue: $('#stat-avg-value'),
  statAvgKwh: $('#stat-avg-kwh'),
  statDistributors: $('#stat-distributors'),
  toast: $('#toast'),
  toastMessage: $('#toast-message'),
};

let selectedFile = null;
let lastResult = null;
let allBills = [];

// ===== Field Labels =====
const FIELD_LABELS = {
  distribuidora: 'Distribuidora',
  cpf_cnpj_titular: 'CPF / CNPJ',
  endereco_titular: 'Endereço',
  numero_instalacao: 'Nº Instalação',
  numero_fatura: 'Nº Fatura',
  mes_referencia: 'Mês Referência',
  data_vencimento: 'Vencimento',
  valor_total: 'Valor Total (R$)',
  consumo_kwh: 'Consumo (kWh)',
  leitura_atual: 'Leitura Atual',
  leitura_anterior: 'Leitura Anterior',
  bandeira_tarifaria: 'Bandeira Tarifária',
  tipo_fornecimento: 'Tipo Fornecimento',
  classe_consumidor: 'Classe',
  tarifa_rs_kwh: 'Tarifa (R$/kWh)',
};

const HIGHLIGHT_FIELDS = ['valor_total', 'consumo_kwh', 'distribuidora'];

// ===== Navigation =====
function switchView(view) {
  $$('.nav-btn').forEach(b => b.classList.remove('active'));
  $$('.view').forEach(v => v.classList.remove('active'));

  if (view === 'upload') {
    els.navUpload.classList.add('active');
    els.viewUpload.classList.add('active');
  } else {
    els.navHistory.classList.add('active');
    els.viewHistory.classList.add('active');
    loadHistory();
  }
}

els.navUpload.addEventListener('click', () => switchView('upload'));
els.navHistory.addEventListener('click', () => switchView('history'));

// ===== File Upload =====
els.uploadZone.addEventListener('click', () => els.fileInput.click());

els.uploadZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  els.uploadZone.classList.add('dragover');
});

els.uploadZone.addEventListener('dragleave', () => {
  els.uploadZone.classList.remove('dragover');
});

els.uploadZone.addEventListener('drop', (e) => {
  e.preventDefault();
  els.uploadZone.classList.remove('dragover');
  const file = e.dataTransfer.files[0];
  if (file) handleFileSelect(file);
});

els.fileInput.addEventListener('change', (e) => {
  if (e.target.files[0]) handleFileSelect(e.target.files[0]);
});

function handleFileSelect(file) {
  const maxSize = 10 * 1024 * 1024; // 10MB
  if (file.size > maxSize) {
    showToast('Arquivo muito grande. Máximo: 10 MB');
    return;
  }

  selectedFile = file;
  els.fileName.textContent = file.name;
  els.fileSize.textContent = formatFileSize(file.size);

  // Preview
  if (file.type.startsWith('image/')) {
    const reader = new FileReader();
    reader.onload = (e) => { els.filePreviewImg.src = e.target.result; };
    reader.readAsDataURL(file);
  } else {
    els.filePreviewImg.src = '';
  }

  els.uploadZone.classList.add('hidden');
  els.filePreview.classList.remove('hidden');
  els.resultsContainer.classList.add('hidden');
  els.errorContainer.classList.add('hidden');
}

els.btnRemoveFile.addEventListener('click', resetUpload);

function resetUpload() {
  selectedFile = null;
  els.fileInput.value = '';
  els.filePreview.classList.add('hidden');
  els.uploadZone.classList.remove('hidden');
  els.processingContainer.classList.add('hidden');
  els.resultsContainer.classList.add('hidden');
  els.errorContainer.classList.add('hidden');
}

// ===== Process =====
els.btnProcess.addEventListener('click', processFile);
els.btnRetry.addEventListener('click', processFile);
els.btnNewUpload.addEventListener('click', resetUpload);

async function processFile() {
  if (!selectedFile) return;

  // Show processing
  els.filePreview.classList.add('hidden');
  els.errorContainer.classList.add('hidden');
  els.resultsContainer.classList.add('hidden');
  els.processingContainer.classList.remove('hidden');

  // Animate steps
  const steps = ['step-ocr', 'step-extract', 'step-refine', 'step-save'];
  steps.forEach(s => {
    const el = $(`#${s}`);
    el.classList.remove('active', 'done');
  });
  $('#step-ocr').classList.add('active');

  let stepIndex = 0;
  const stepInterval = setInterval(() => {
    if (stepIndex < steps.length) {
      $(`#${steps[stepIndex]}`).classList.remove('active');
      $(`#${steps[stepIndex]}`).classList.add('done');
      stepIndex++;
      if (stepIndex < steps.length) {
        $(`#${steps[stepIndex]}`).classList.add('active');
      }
    }
  }, 1200);

  try {
    const formData = new FormData();
    formData.append('file', selectedFile);

    const response = await fetch('/energy-bill', { method: 'POST', body: formData });
    const data = await response.json();

    clearInterval(stepInterval);
    steps.forEach(s => {
      $(`#${s}`).classList.remove('active');
      $(`#${s}`).classList.add('done');
    });

    if (!response.ok) {
      throw new Error(data.error || 'Erro desconhecido no servidor');
    }

    await new Promise(r => setTimeout(r, 600));

    lastResult = data;
    showResults(data.dados_extraidos);
  } catch (err) {
    clearInterval(stepInterval);
    showError(err.message);
  }
}

function showResults(data) {
  els.processingContainer.classList.add('hidden');
  els.resultsContainer.classList.remove('hidden');

  els.resultsGrid.innerHTML = '';

  for (const [key, label] of Object.entries(FIELD_LABELS)) {
    const value = data[key];
    const isEmpty = !value || value === 'None' || value === 'null';
    const isHighlight = HIGHLIGHT_FIELDS.includes(key);

    const card = document.createElement('div');
    card.className = `result-card${isHighlight ? ' highlight' : ''}`;

    let displayValue = isEmpty ? 'Não identificado' : value;
    if (key === 'valor_total' && !isEmpty) {
      displayValue = `R$ ${parseFloat(value.replace(',', '.')).toFixed(2)}`;
    }

    card.innerHTML = `
      <span class="result-label">${label}</span>
      <span class="result-value${isEmpty ? ' empty' : ''}">${displayValue}</span>
    `;
    els.resultsGrid.appendChild(card);
  }
}

function showError(message) {
  els.processingContainer.classList.add('hidden');
  els.errorContainer.classList.remove('hidden');
  els.errorMessage.textContent = message;
}

// ===== Copy / Download JSON =====
els.btnCopyJson.addEventListener('click', () => {
  if (!lastResult) return;
  navigator.clipboard.writeText(JSON.stringify(lastResult.dados_extraidos, null, 2))
    .then(() => showToast('JSON copiado!'))
    .catch(() => showToast('Erro ao copiar'));
});

els.btnDownloadJson.addEventListener('click', () => {
  if (!lastResult) return;
  const blob = new Blob([JSON.stringify(lastResult.dados_extraidos, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'conta_energia.json';
  a.click();
  URL.revokeObjectURL(url);
});

// ===== History =====
els.btnRefreshHistory.addEventListener('click', loadHistory);
if (els.btnGoUpload) els.btnGoUpload.addEventListener('click', () => switchView('upload'));

async function loadHistory() {
  try {
    const response = await fetch('/bills');
    const data = await response.json();
    allBills = data.data || [];
    renderStats(allBills);
    renderTable(allBills);
    els.historyCount.textContent = `${allBills.length} conta${allBills.length !== 1 ? 's' : ''} processada${allBills.length !== 1 ? 's' : ''}`;
  } catch {
    els.historyCount.textContent = 'Erro ao carregar histórico';
  }
}

els.searchInput.addEventListener('input', (e) => {
  const query = e.target.value.toLowerCase();
  if (!query) {
    renderTable(allBills);
    return;
  }
  const filtered = allBills.filter(bill =>
    Object.values(bill).some(v => String(v).toLowerCase().includes(query))
  );
  renderTable(filtered);
});

function renderStats(bills) {
  els.statTotal.textContent = bills.length;

  const values = bills.map(b => parseFloat(String(b.valor_total || '0').replace(',', '.'))).filter(v => v > 0);
  const avgVal = values.length ? (values.reduce((a, b) => a + b, 0) / values.length) : 0;
  els.statAvgValue.textContent = avgVal > 0 ? `R$ ${avgVal.toFixed(2)}` : '—';

  const kwhs = bills.map(b => parseFloat(String(b.consumo_kwh || '0').replace(',', '.'))).filter(v => v > 0);
  const avgKwh = kwhs.length ? (kwhs.reduce((a, b) => a + b, 0) / kwhs.length) : 0;
  els.statAvgKwh.textContent = avgKwh > 0 ? `${Math.round(avgKwh)} kWh` : '—';

  const distributors = new Set(bills.map(b => b.distribuidora).filter(d => d && d !== 'None'));
  els.statDistributors.textContent = distributors.size || '—';
}

function renderTable(bills) {
  if (!bills.length) {
    els.dataTable.classList.add('hidden');
    els.tableEmpty.classList.remove('hidden');
    return;
  }

  els.dataTable.classList.remove('hidden');
  els.tableEmpty.classList.add('hidden');

  els.tableBody.innerHTML = bills.map(bill => {
    const dist = formatCell(bill.distribuidora);
    const ref = formatCell(bill.mes_referencia);
    const venc = formatCell(bill.data_vencimento);
    const valor = formatCell(bill.valor_total, true);
    const kwh = formatCell(bill.consumo_kwh);
    const bandeira = formatBandeira(bill.bandeira_tarifaria);
    const proc = bill.data_processamento
      ? new Date(bill.data_processamento).toLocaleDateString('pt-BR')
      : '—';

    return `<tr>
      <td>${dist}</td>
      <td>${ref}</td>
      <td>${venc}</td>
      <td>${valor}</td>
      <td>${kwh}</td>
      <td>${bandeira}</td>
      <td>${proc}</td>
    </tr>`;
  }).join('');
}

function formatCell(value, isCurrency = false) {
  if (!value || value === 'None' || value === 'null') {
    return '<span class="cell-none">—</span>';
  }
  if (isCurrency) {
    const num = parseFloat(String(value).replace(',', '.'));
    return isNaN(num) ? value : `R$ ${num.toFixed(2)}`;
  }
  return value;
}

function formatBandeira(value) {
  if (!value || value === 'None') return '<span class="badge badge-gray">—</span>';
  const lower = value.toLowerCase();
  if (lower.includes('verde')) return `<span class="badge badge-green">${value}</span>`;
  if (lower.includes('amarela')) return `<span class="badge badge-yellow">${value}</span>`;
  if (lower.includes('vermelha')) return `<span class="badge badge-red">${value}</span>`;
  return `<span class="badge badge-gray">${value}</span>`;
}

// ===== Toast =====
function showToast(message) {
  els.toastMessage.textContent = message;
  els.toast.classList.remove('hidden');
  els.toast.classList.add('show');
  setTimeout(() => {
    els.toast.classList.remove('show');
    setTimeout(() => els.toast.classList.add('hidden'), 300);
  }, 2500);
}

// ===== Utilities =====
function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}
