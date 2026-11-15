

// Market price estimates (TRY / kg) — approximate for demo
const CROP_MARKET_PRICES = {
  nohut:   { price: 28, unit: '₺/kg' },
  mercan:  { price: 30, unit: '₺/kg' },
  buğday:  { price: 10, unit: '₺/kg' },
  arpa:    { price: 8,  unit: '₺/kg' },
  mısır:   { price: 7,  unit: '₺/kg' },
  bezelye: { price: 25, unit: '₺/kg' },
  patates: { price: 9,  unit: '₺/kg' },
  domates: { price: 6,  unit: '₺/kg' },
};

// Yield data per decare
const CROP_METRICS = {
  nohut:   { ratio_en: 'Yields 1:10', ratio_tr: "1'e 10 Verir", yield_en: '160 - 200 kg / decare', yield_tr: '160 - 200 kg / dönüm', yield_mid: 180 },
  mercan:  { ratio_en: 'Yields 1:12', ratio_tr: "1'e 12 Verir", yield_en: '180 - 230 kg / decare', yield_tr: '180 - 230 kg / dönüm', yield_mid: 205 },
  buğday:  { ratio_en: 'Yields 1:8',  ratio_tr: "1'e 8 Verir",  yield_en: '280 - 380 kg / decare', yield_tr: '280 - 380 kg / dönüm', yield_mid: 330 },
  arpa:    { ratio_en: 'Yields 1:9',  ratio_tr: "1'e 9 Verir",  yield_en: '300 - 420 kg / decare', yield_tr: '300 - 420 kg / dönüm', yield_mid: 360 },
  mısır:   { ratio_en: 'Yields 1:14', ratio_tr: "1'e 14 Verir", yield_en: '950 - 1250 kg / decare', yield_tr: '950 - 1250 kg / dönüm', yield_mid: 1100 },
  bezelye: { ratio_en: 'Yields 1:10', ratio_tr: "1'e 10 Verir", yield_en: '200 - 260 kg / decare', yield_tr: '200 - 260 kg / dönüm', yield_mid: 230 },
  patates: { ratio_en: 'Yields 1:6',  ratio_tr: "1'e 6 Verir",  yield_en: '2500 - 3500 kg / decare', yield_tr: '2500 - 3500 kg / dönüm', yield_mid: 3000 },
  domates: { ratio_en: 'Yields 1:15', ratio_tr: "1'e 15 Verir", yield_en: '4000 - 6000 kg / decare', yield_tr: '4000 - 6000 kg / dönüm', yield_mid: 5000 },
};

function getFarmerJudgment(score, lang) {
  if (score >= 75) {
    return {
      title: lang === 'tr' ? 'Tam Tarlanın Malı' : 'Prime Field Match',
      sub: lang === 'tr' ? 'Bu hava ve toprakta gözün kapalı ekebilirsin' : 'Ideal climate & soil conditions with minimum risk'
    };
  } else if (score >= 50) {
    return {
      title: lang === 'tr' ? 'Güzel Tutar (Bakım İster)' : 'Good Fit (Requires Care)',
      sub: lang === 'tr' ? 'Sulamayı ve bakımı aksatmazsan iyi ürün verir' : 'Healthy yields expected with steady irrigation & care'
    };
  } else {
    return {
      title: lang === 'tr' ? 'Tarlayı Yorma (Riskli)' : 'High Risk for Field',
      sub: lang === 'tr' ? 'Bu sezon iklim ve su şartları masrafını zor kurtarır' : 'Climate stress may suppress yield below investment cost'
    };
  }
}

function getDroughtAssessment(precipMmDay, lang) {
  // daily average precipitation
  if (precipMmDay >= 2.5) {
    return {
      levelClass: 'status-low',
      level: lang === 'tr' ? 'Düşük' : 'Low',
      desc: lang === 'tr'
        ? 'Yağış yeterli. Kuraklık riski minimal, çoğu ürün güvenli.'
        : 'Rainfall is sufficient. Drought risk is minimal; most crops are safe.'
    };
  } else if (precipMmDay >= 1.2) {
    return {
      levelClass: 'status-mid',
      level: lang === 'tr' ? 'Orta' : 'Moderate',
      desc: lang === 'tr'
        ? 'Yağış sınırda. Su tasarruflu ürün tercih edin veya sulama planlayın.'
        : 'Rainfall is borderline. Prefer drought-tolerant crops or plan supplemental irrigation.'
    };
  } else {
    return {
      levelClass: 'status-high',
      level: lang === 'tr' ? 'Yüksek' : 'High',
      desc: lang === 'tr'
        ? 'Ciddi kuraklık riski. Yalnızca kurak dayanıklı ürün ekin, sulamayı güvence altına alın.'
        : 'Serious drought risk. Plant only drought-resistant crops and secure irrigation.'
    };
  }
}

let currentLang = 'tr';
let appState = {
  ort: null,
  raw: null,
  aylik: null,
  cok_yillik: null,
  rotationResult: null
};

// DOM references
const latInput = document.getElementById('latInput');
const lonInput = document.getElementById('lonInput');
const fieldSizeInput = document.getElementById('fieldSizeInput');
const startDateInput = document.getElementById('startDate');
const endDateInput = document.getElementById('endDate');
const mevcutCropSelect = document.getElementById('mevcutCrop');
const previousCropSelect = document.getElementById('previousCrop');
const addressInput = document.getElementById('addressInput');
const btnGeocode = document.getElementById('btnGeocode');

const pSu = document.getElementById('p_su');
const pToprak = document.getElementById('p_toprak');
const pKara = document.getElementById('p_kara');
const pGuclu = document.getElementById('p_guclu');

const judgmentTitle = document.getElementById('judgmentTitle');
const judgmentSub = document.getElementById('judgmentSub');
const bestYieldRatio = document.getElementById('bestYieldRatio');
const bestYieldPerDecare = document.getElementById('bestYieldPerDecare');

const scPrecip = document.getElementById('sc_precip');
const scTemp = document.getElementById('sc_temp');
const valScPrecip = document.getElementById('val_sc_precip');
const valScTemp = document.getElementById('val_sc_temp');

const cIrrigation = document.getElementById('c_irrigation');
const cMarket = document.getElementById('c_market');

const btnAnalyze = document.getElementById('btnAnalyze');
const btnLang = document.getElementById('btnLang');
const langText = document.getElementById('langText');
const statusBanner = document.getElementById('statusBanner');
const statusBannerText = document.getElementById('statusBannerText');

const welcomePlaceholder = document.getElementById('welcomePlaceholder');
const analysisContent = document.getElementById('analysisContent');

const valTemp = document.getElementById('valTemp');
const valPrecip = document.getElementById('valPrecip');
const valSolar = document.getElementById('valSolar');
const valWind = document.getElementById('valWind');

const bestCropName = document.getElementById('bestCropName');
const bestCropSub = document.getElementById('bestCropSub');

const strategiesContainer = document.getElementById('strategiesContainer');
const riskWarningsRow = document.getElementById('riskWarningsRow');

const incTotalYield = document.getElementById('incTotalYield');
const incPricePerKg = document.getElementById('incPricePerKg');
const incGrossRevenue = document.getElementById('incGrossRevenue');

const droughtLevel = document.getElementById('droughtLevel');
const droughtDesc = document.getElementById('droughtDesc');

let stressChartInstance = null;
let timelineChartInstance = null;
let leafletMap = null;
let mapMarker = null;

function showBanner(msg, isSuccess = false) {
  statusBannerText.textContent = msg;
  statusBanner.className = 'status-banner' + (isSuccess ? ' success' : '');
  statusBanner.style.display = 'block';
  setTimeout(() => { statusBanner.style.display = 'none'; }, 5000);
}

function formatDateForAPI(dateStr) {
  return dateStr.replace(/-/g, '');
}

function initLeaflet() {
  const initLat = parseFloat(latInput.value) || 37.8746;
  const initLon = parseFloat(lonInput.value) || 32.4932;

  leafletMap = L.map('map', {
    zoomControl: false,
    scrollWheelZoom: true
  }).setView([initLat, initLon], 7);

  L.control.zoom({ position: 'bottomright' }).addTo(leafletMap);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
    attribution: '© OpenStreetMap'
  }).addTo(leafletMap);

  mapMarker = L.marker([initLat, initLon], { draggable: true }).addTo(leafletMap);

  leafletMap.on('click', (e) => { updateCoords(e.latlng.lat, e.latlng.lng); });
  mapMarker.on('dragend', (e) => {
    const latlng = e.target.getLatLng();
    updateCoords(latlng.lat, latlng.lng);
  });
}

function updateCoords(lat, lon) {
  const roundedLat = parseFloat(lat.toFixed(4));
  const roundedLon = parseFloat(lon.toFixed(4));
  latInput.value = roundedLat;
  lonInput.value = roundedLon;
  if (mapMarker) mapMarker.setLatLng([roundedLat, roundedLon]);
}

async function geocodeAddress() {
  const query = addressInput.value.trim();
  if (!query) return;

  btnGeocode.disabled = true;
  try {
    const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=1`;
    const res = await fetch(url, { headers: { 'Accept-Language': 'en' } });
    const data = await res.json();
    if (data && data.length > 0) {
      const lat = parseFloat(data[0].lat);
      const lon = parseFloat(data[0].lon);
      updateCoords(lat, lon);
      if (leafletMap) leafletMap.setView([lat, lon], 11);
      showBanner(data[0].display_name, true);
    } else {
      showBanner(currentLang === 'tr' ? 'Adres bulunamadı.' : 'Address not found.');
    }
  } catch {
    showBanner(currentLang === 'tr' ? 'Adres araması başarısız.' : 'Address search failed.');
  } finally {
    btnGeocode.disabled = false;
  }
}

let loadedCropsData = {};

async function loadCrops() {
  try {
    const res = await fetch('/api/bitkiler');
    if (!res.ok) throw new Error('Crops could not be loaded');
    loadedCropsData = await res.json();

    const emptyOpt = `<option value="">${I18N[currentLang].opt_empty_crop}</option>`;
    mevcutCropSelect.innerHTML = emptyOpt;

    populateHistorySelects();

    for (const [key, crop] of Object.entries(loadedCropsData)) {
      const opt = document.createElement('option');
      opt.value = key;
      opt.textContent = (currentLang === 'en' && crop.ad_en) ? crop.ad_en : crop.ad;
      mevcutCropSelect.appendChild(opt);
    }
  } catch (err) {
    console.error(err);
  }
}

function populateHistorySelects() {
  const selects = document.querySelectorAll('.previous-crop-select');
  selects.forEach(sel => {
    const currentVal = sel.value;
    sel.innerHTML = `<option value="">${I18N[currentLang].opt_prev_none}</option>`;
    for (const [key, crop] of Object.entries(loadedCropsData)) {
      const opt = document.createElement('option');
      opt.value = key;
      opt.textContent = (currentLang === 'en' && crop.ad_en) ? crop.ad_en : crop.ad;
      sel.appendChild(opt);
    }
    sel.value = currentVal;
  });
}

function getSelectedCropHistory() {
  const history = [];
  document.querySelectorAll('.previous-crop-select').forEach(sel => {
    if (sel.value) history.push(sel.value);
  });
  return history;
}

let historyCount = 1;
function addHistoryCropRow() {
  if (historyCount >= 4) return; // En fazla 4 yıl geçmiş
  historyCount++;
  const container = document.getElementById('cropHistoryContainer');
  const row = document.createElement('div');
  row.className = 'field-select-row crop-history-row';
  row.setAttribute('data-history-idx', historyCount);

  const labelText = currentLang === 'tr' 
    ? `${historyCount}. ${I18N.tr.lbl_year_prev}` 
    : `${historyCount} ${I18N.en.lbl_year_prev}`;

  row.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center;">
      <label class="cell-label">${labelText}</label>
      <button type="button" class="subtle-link remove-hist-btn" style="color:var(--c-risk-red); font-size:11px;">✕</button>
    </div>
    <select class="field-select previous-crop-select">
      <option value="">${I18N[currentLang].opt_prev_none}</option>
    </select>
  `;

  const sel = row.querySelector('.previous-crop-select');
  for (const [key, crop] of Object.entries(loadedCropsData)) {
    const opt = document.createElement('option');
    opt.value = key;
    opt.textContent = (currentLang === 'en' && crop.ad_en) ? crop.ad_en : crop.ad;
    sel.appendChild(opt);
  }

  row.querySelector('.remove-hist-btn').addEventListener('click', () => {
    row.remove();
    historyCount--;
    if (appState.ort) debounceRotation();
  });

  sel.addEventListener('change', () => {
    if (appState.ort) debounceRotation();
  });

  container.appendChild(row);
}

function initPills() {
  document.querySelectorAll('.choice-pills').forEach(group => {
    const parentRow = group.closest('.weight-row');
    const hiddenInput = parentRow.querySelector('input[type="hidden"]');
    group.querySelectorAll('.choice-pill').forEach(btn => {
      btn.addEventListener('click', () => {
        group.querySelectorAll('.choice-pill').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        hiddenInput.value = btn.dataset.val;
        if (appState.ort) debounceRotation();
      });
    });
  });

  scPrecip.addEventListener('input', () => {
    valScPrecip.textContent = `${scPrecip.value}%`;
    if (appState.ort) debounceRotation();
  });

  scTemp.addEventListener('input', () => {
    valScTemp.textContent = `${scTemp.value}°C`;
    if (appState.ort) debounceRotation();
  });

  mevcutCropSelect.addEventListener('change', () => { if (appState.ort) debounceRotation(); });
  document.querySelectorAll('.previous-crop-select').forEach(sel => {
    sel.addEventListener('change', () => { if (appState.ort) debounceRotation(); });
  });
  cIrrigation.addEventListener('change', () => { if (appState.ort) debounceRotation(); });
  cMarket.addEventListener('change', () => { if (appState.ort) debounceRotation(); });
  fieldSizeInput.addEventListener('change', () => { if (appState.rotationResult) updateIncomeCard(appState.rotationResult); });
}

let debounceTimer = null;
function debounceRotation() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => runRotationCalculation(), 250);
}

function setLanguage(lang) {
  currentLang = lang;
  try { localStorage.setItem('sage_lang', lang); } catch (e) {}
  langText.textContent = I18N[lang].lang_code;
  document.documentElement.lang = lang;

  document.querySelectorAll('[data-i18n]').forEach((el) => {
    const key = el.getAttribute('data-i18n');
    if (I18N[lang][key]) el.textContent = I18N[lang][key];
  });

  // Update placeholders
  if (addressInput) {
    addressInput.placeholder = I18N[lang].ph_address;
  }

  // Update crop select option labels for language
  updateSelectOptionsLanguage(lang);

  // Update history crop labels
  document.querySelectorAll('.crop-history-row').forEach(row => {
    const idx = row.getAttribute('data-history-idx');
    const lbl = row.querySelector('.cell-label');
    if (lbl) {
      if (idx === '1') {
        lbl.textContent = I18N[lang].lbl_prev_crop;
      } else {
        lbl.textContent = lang === 'tr' ? `${idx}. ${I18N.tr.lbl_year_prev}` : `${idx} ${I18N.en.lbl_year_prev}`;
      }
    }
  });

  const btnAdd = document.getElementById('btnAddHistoryCrop');
  if (btnAdd && I18N[lang].btn_add_history) {
    btnAdd.textContent = I18N[lang].btn_add_history;
  }

  if (appState.ort) {
    runRotationCalculation();
  }
}

function updateSelectOptionsLanguage(lang) {
  // Update fallow option in mevcut
  if (mevcutCropSelect && mevcutCropSelect.options.length > 0) {
    mevcutCropSelect.options[0].textContent = I18N[lang].opt_empty_crop;
    for (let i = 1; i < mevcutCropSelect.options.length; i++) {
      const opt = mevcutCropSelect.options[i];
      const crop = loadedCropsData[opt.value];
      if (crop) {
        opt.textContent = (lang === 'en' && crop.ad_en) ? crop.ad_en : crop.ad;
      }
    }
  }

  // Update history selects
  document.querySelectorAll('.previous-crop-select').forEach(sel => {
    if (sel.options.length > 0) {
      sel.options[0].textContent = I18N[lang].opt_prev_none;
      for (let i = 1; i < sel.options.length; i++) {
        const opt = sel.options[i];
        const crop = loadedCropsData[opt.value];
        if (crop) {
          opt.textContent = (lang === 'en' && crop.ad_en) ? crop.ad_en : crop.ad;
        }
      }
    }
  });
}

async function runFullAnalysis() {
  const lat = parseFloat(latInput.value);
  const lon = parseFloat(lonInput.value);
  const start = formatDateForAPI(startDateInput.value);
  const end = formatDateForAPI(endDateInput.value);

  if (isNaN(lat) || isNaN(lon)) {
    showBanner(currentLang === 'tr' ? 'Lütfen geçerli koordinat girin.' : 'Please enter valid coordinates.');
    return;
  }

  if (!start || !end || start >= end) {
    showBanner(currentLang === 'tr' ? 'Bitiş tarihi başlangıçtan sonra olmalı.' : 'End date must be after start date.');
    return;
  }

  btnAnalyze.disabled = true;
  btnAnalyze.querySelector('.btn-spinner').style.display = 'inline-block';
  btnAnalyze.querySelector('.btn-label').textContent = I18N[currentLang].btn_running;

  try {
    const res = await fetch('/api/analiz', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lat, lon, start, end })
    });

    const data = await res.json();
    if (!res.ok || data.error) throw new Error(data.error || 'NASA POWER data unavailable.');

    appState.ort = data.ortalama;
    appState.raw = data.raw;
    appState.aylik = data.aylik || null;
    appState.cok_yillik = data.cok_yillik || null;

    valTemp.textContent = appState.ort.sıcaklık_C;
    valPrecip.textContent = appState.ort.yağış_mm_gun;
    valSolar.textContent = appState.ort.güneş_MJ_m2_gun;
    valWind.textContent = appState.ort.rüzgar_m_s;

    // Drought risk
    updateDroughtCard(appState.ort.yağış_mm_gun);

    welcomePlaceholder.style.display = 'none';
    analysisContent.style.display = 'block';

    renderTimelineChart(appState.raw);
    await runRotationCalculation();

    showBanner(currentLang === 'tr' ? 'NASA iklim verileri başarıyla işlendi!' : 'NASA climate data loaded successfully!', true);
  } catch (err) {
    showBanner(`Error: ${err.message}`);
  } finally {
    btnAnalyze.disabled = false;
    btnAnalyze.querySelector('.btn-spinner').style.display = 'none';
    btnAnalyze.querySelector('.btn-label').textContent = I18N[currentLang].btn_run_analysis;
  }
}

function updateDroughtCard(precipMmDay) {
  const assessment = getDroughtAssessment(precipMmDay, currentLang);
  droughtLevel.innerHTML = `<span class="status-indicator ${assessment.levelClass}"></span><span>${assessment.level}</span>`;
  droughtDesc.textContent = assessment.desc;
}

function updateIncomeCard(data) {
  if (!data || !data.en_iyi_bitki) return;
  const bitkiKey = data.en_iyi_bitki.anahtar || '';
  const cropInfo = loadedCropsData[bitkiKey] || {};
  const fieldSize = parseFloat(fieldSizeInput.value) || 50;

  const verim = cropInfo.verim_kg_donum || 300;
  const fiyat = cropInfo.fiyat_tl_kg || 15.0;

  const totalYield = Math.round(verim * fieldSize);
  const gross = Math.round(totalYield * fiyat);

  incTotalYield.textContent = `${totalYield.toLocaleString()} kg`;
  incPricePerKg.textContent = `${fiyat} ₺/kg`;
  incGrossRevenue.textContent = `${gross.toLocaleString()} ₺`;
}

async function runRotationCalculation() {
  if (!appState.ort) return;

  const oncelikler = {
    su_tasarimi: parseInt(pSu.value),
    toprak_sagligi: parseInt(pToprak.value),
    kararli_verim: parseInt(pKara.value),
    guclu_koşullar: parseInt(pGuclu.value)
  };

  const scenario = {
    precip_change_pct: parseFloat(scPrecip.value),
    temp_change_c: parseFloat(scTemp.value)
  };

  const constraints = {
    irrigation: cIrrigation.value || null,
    market_preference: cMarket.value || null
  };

  const historyList = getSelectedCropHistory();

  const payload = {
    ortalama: appState.ort,
    aylik: appState.aylik || null,
    cok_yillik: appState.cok_yillik || null,
    oncelikler,
    mevcut: mevcutCropSelect.value || null,
    onceki: historyList.length > 0 ? historyList[0] : null,
    gecmis_bitkiler: historyList,
    scenario,
    constraints,
    lang: currentLang
  };

  try {
    const res = await fetch('/api/rotasyon', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (!res.ok || data.error) throw new Error(data.error || 'Rotation could not be calculated.');

    appState.rotationResult = data;
    renderResultsUI(data);

    // Also update drought card with fresh lang
    if (appState.ort) updateDroughtCard(appState.ort.yağış_mm_gun);
  } catch (err) {
    console.error(err);
  }
}

function renderResultsUI(data) {
  // Risk notices
  riskWarningsRow.innerHTML = '';
  if (data.risk_uyarilari && data.risk_uyarilari.length > 0) {
    riskWarningsRow.style.display = 'flex';
    data.risk_uyarilari.forEach((risk) => {
      const box = document.createElement('div');
      box.className = 'risk-notice-entry';
      box.textContent = risk.mesaj;
      riskWarningsRow.appendChild(box);
    });
  } else {
    riskWarningsRow.style.display = 'none';
  }

  // Hero Crop Card
  if (data.en_iyi_bitki) {
    const bitkiKey = data.en_iyi_bitki.anahtar || '';
    const cropInfo = loadedCropsData[bitkiKey] || {};
    bestCropName.textContent = (currentLang === 'en' && cropInfo.ad_en) ? cropInfo.ad_en : data.en_iyi_bitki.bitki;

    const judgment = getFarmerJudgment(data.en_iyi_bitki.skor, currentLang);
    judgmentTitle.textContent = judgment.title;
    judgmentSub.textContent = judgment.sub;

    const metrics = CROP_METRICS[bitkiKey] || {
      ratio_en: cropInfo.oran_en || 'Yields 1:8', ratio_tr: cropInfo.oran || "1'e 8 Verir",
      yield_en: `${cropInfo.verim_kg_donum || 300} kg / decare`, yield_tr: `${cropInfo.verim_kg_donum || 300} kg / dönüm`
    };
    bestYieldRatio.textContent = currentLang === 'tr' ? metrics.ratio_tr : metrics.ratio_en;
    bestYieldPerDecare.textContent = currentLang === 'tr' ? metrics.yield_tr : metrics.yield_en;

    const grup = data.en_iyi_bitki.grup ? ` · ${data.en_iyi_bitki.grup.toUpperCase()}` : '';
    bestCropSub.textContent = (currentLang === 'tr'
      ? 'Mevcut iklim rejimine ve toprak hedeflerinize en yüksek bereketi sağlayan ana ürün'
      : 'Highest yielding and most suitable crop for your field conditions') + grup;

    // Income card
    updateIncomeCard(data);
  }

  // Statistical Trend Analysis (SI) Panel
  renderSITrendUI(data.si_analiz);

  // 3-Year Rotation Plan Roadmap Cards
  const rotationGrid = document.getElementById('rotationCardsGrid');
  if (rotationGrid && data.rotasyon_plani) {
    rotationGrid.innerHTML = '';
    data.rotasyon_plani.forEach(item => {
      const card = document.createElement('div');
      card.className = 'roadmap-year-card';
      const isHealing = item.toprak_etkisi === 'iyileştirici';
      const roleText = currentLang === 'tr' ? item.rol : (item.rol_en || item.rol);
      const descText = currentLang === 'tr' ? item.aciklama : (item.aciklama_en || item.aciklama);
      const yearLabel = currentLang === 'tr' ? `${item.yil}. Yıl` : `Year ${item.yil}`;

      const cropInfo = loadedCropsData[item.anahtar] || {};
      const cropName = (currentLang === 'en' && cropInfo.ad_en) ? cropInfo.ad_en : item.bitki;

      card.innerHTML = `
        <span class="year-pill">${yearLabel}</span>
        <h4 class="year-crop-name">${cropName}</h4>
        <span class="year-role-tag ${isHealing ? '' : 'neutral'}">${roleText}</span>
        <p class="year-desc">${descText}</p>
        <div class="year-metrics-strip">
          <span>${currentLang === 'tr' ? 'Tahmini Verim:' : 'Est. Yield:'} <strong>${item.verim_kg} kg/da</strong></span>
          <span>${currentLang === 'tr' ? 'Piyasa:' : 'Market:'} <strong>${item.fiyat_tl} ₺/kg</strong></span>
        </div>
      `;
      rotationGrid.appendChild(card);
    });

    // Update dynamic ecological impact strip
    const hasLegume = data.rotasyon_plani.some(item => item.toprak_etkisi === 'iyileştirici');
    const ecoNitrogen = document.getElementById('ecoNitrogenSave');
    const ecoWater = document.getElementById('ecoWaterSave');
    const ecoSoil = document.getElementById('ecoSoilHealth');

    if (ecoNitrogen) ecoNitrogen.textContent = hasLegume ? '~%32' : '~%15';
    if (ecoWater) ecoWater.textContent = (appState.ort && appState.ort.yağış_mm_gun < 1.5) ? '~%38' : '~%25';
    if (ecoSoil) ecoSoil.textContent = hasLegume ? (currentLang === 'tr' ? 'Onarıcı (+%1.8)' : 'Restorative (+1.8%)') : (currentLang === 'tr' ? 'Dengeli' : 'Balanced');
  }

  // 3 Strategy Cards
  strategiesContainer.innerHTML = '';
  if (data.stratejiler) {
    data.stratejiler.forEach((strat, idx) => {
      const card = document.createElement('div');
      card.className = 'strategy-column-card';
      const stratCropInfo = loadedCropsData[strat.anahtar || ''] || {};
      const stratCropName = (currentLang === 'en' && stratCropInfo.ad_en) ? stratCropInfo.ad_en : strat.bitki;

      card.innerHTML = `
        <span class="strat-card-tag">${currentLang === 'tr' ? (idx + 1) + '. Yol' : 'Route ' + (idx + 1)}</span>
        <h4 class="strat-card-title">${strat.ad}</h4>
        <div class="strat-crop-row">
          <span class="strat-crop-name">${stratCropName}</span>
          <span class="strat-crop-score">${strat.skor} / 100</span>
        </div>
        <p class="strat-narrative">${strat.neden}</p>
        <ul class="strat-points">
          <li><strong>${currentLang === 'tr' ? 'Kanıt:' : 'Evidence:'}</strong> ${strat.kanit || '--'}</li>
          <li><strong>${currentLang === 'tr' ? 'Kazanım:' : 'Gain:'}</strong> ${(strat.faydalar || []).join(', ')}</li>
          <li><strong>${currentLang === 'tr' ? 'Önlem:' : 'Precaution:'}</strong> ${(strat.riskler || []).join(', ')}</li>
        </ul>
      `;
      strategiesContainer.appendChild(card);
    });
  }

  // Stress Chart
  if (data.stres_takvimi) renderStressChart(data.stres_takvimi);
}

function renderSITrendUI(si) {
  const section = document.getElementById('siTrendSection');
  const cardsContainer = document.getElementById('siTrendCards');
  const interpEl = document.getElementById('siInterpretation');
  const badgeEl = document.getElementById('siConfidenceBadge');

  if (!section || !cardsContainer) return;

  if (!si || !si.sicaklik_trend || !si.yagis_trend) {
    section.style.display = 'none';
    return;
  }

  section.style.display = 'block';

  const tTrend = si.sicaklik_trend;
  const pTrend = si.yagis_trend;
  const tSlopeStr = `${tTrend.slope > 0 ? '+' : ''}${tTrend.slope.toFixed(2)}°C${I18N[currentLang].si_per_year}`;
  const pSlopeStr = `${pTrend.slope > 0 ? '+' : ''}${pTrend.slope.toFixed(3)} mm${I18N[currentLang].si_per_year}`;

  const tAnom = tTrend.anomali;
  const pAnom = pTrend.anomali;

  function anomalyBadge(anom) {
    if (!anom) return '';
    if (anom.anomaly) {
      const dirText = anom.direction === 'above' 
        ? (currentLang === 'tr' ? 'Ortalama Üstü (+Z)' : 'Above Mean (+Z)')
        : (currentLang === 'tr' ? 'Ortalama Altı (-Z)' : 'Below Mean (-Z)');
      return `<span class="si-card-anomaly anomaly-warn">Z=${anom.z} · ${dirText}</span>`;
    }
    return `<span class="si-card-anomaly anomaly-norm">${currentLang === 'tr' ? 'Normal Aralık (Z=' + anom.z + ')' : 'Normal Range (Z=' + anom.z + ')'}</span>`;
  }

  cardsContainer.innerHTML = `
    <div class="si-card">
      <span class="si-card-label">${I18N[currentLang].si_temp_trend}</span>
      <div class="si-card-metric">${tSlopeStr}</div>
      <span class="si-card-sub">OLS: R² = ${tTrend.r2.toFixed(2)}</span>
      ${anomalyBadge(tAnom)}
    </div>
    <div class="si-card">
      <span class="si-card-label">${I18N[currentLang].si_precip_trend}</span>
      <div class="si-card-metric">${pSlopeStr}</div>
      <span class="si-card-sub">OLS: R² = ${pTrend.r2.toFixed(2)}</span>
      ${anomalyBadge(pAnom)}
    </div>
    <div class="si-card">
      <span class="si-card-label">${I18N[currentLang].si_confidence}</span>
      <div class="si-card-metric">${si.guven_duzeyi}%</div>
      <span class="si-card-sub">${currentLang === 'tr' ? 'Ortalama Korelasyon Uyumu' : 'Mean Correlation Fit'}</span>
    </div>
  `;

  if (interpEl) interpEl.textContent = si.yorumlama || '';
  if (badgeEl && si.yillar && si.yillar.length) {
    badgeEl.textContent = currentLang === 'tr' 
      ? `NASA POWER ${si.yillar[0]}–${si.yillar[si.yillar.length - 1]} (${si.yillar.length} Yıl)`
      : `NASA POWER ${si.yillar[0]}–${si.yillar[si.yillar.length - 1]} (${si.yillar.length} Years)`;
  }
}

function renderStressChart(stress) {
  const ctx = document.getElementById('stressChart').getContext('2d');
  if (stressChartInstance) stressChartInstance.destroy();

  const labels = stress.aylar.map(a => a.ay_adi);
  const tempStress = stress.aylar.map(a => a.temp_stress);
  const waterStress = stress.aylar.map(a => a.water_stress);
  const ndvi = stress.aylar.map(a => Math.round(a.ndvi_proxy * 100));

  stressChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: currentLang === 'tr' ? 'Sıcaklık Stresi (%)' : 'Thermal Stress (%)',
          data: tempStress,
          borderColor: '#b47b2b',
          backgroundColor: 'rgba(180,123,43,0.08)',
          fill: true, tension: 0.3, pointRadius: 3
        },
        {
          label: currentLang === 'tr' ? 'Su Stresi (%)' : 'Moisture Deficit (%)',
          data: waterStress,
          borderColor: '#236477',
          backgroundColor: 'rgba(35,100,119,0.08)',
          fill: true, tension: 0.3, pointRadius: 3
        },
        {
          label: currentLang === 'tr' ? 'NDVI Büyüme Eğrisi' : 'NDVI Phenology',
          data: ndvi,
          borderColor: '#255d36',
          backgroundColor: 'transparent',
          borderDash: [4, 4], tension: 0.3, pointRadius: 3
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, max: 100, grid: { color: '#e5ebe0' }, ticks: { font: { family: 'JetBrains Mono', size: 11 }, color: '#5e6b5f' } },
        x: { grid: { display: false }, ticks: { font: { family: 'Plus Jakarta Sans', size: 11 }, color: '#5e6b5f' } }
      }
    }
  });
}

function renderTimelineChart(raw) {
  const ctx = document.getElementById('timelineChart').getContext('2d');
  if (timelineChartInstance) timelineChartInstance.destroy();

  const p = raw.properties?.parameter || {};
  const dates = Object.keys(p.T2M || {}).sort();
  if (!dates.length) return;

  const labels = dates.map(d => `${d.slice(6, 8)}/${d.slice(4, 6)}`);
  const t2mData = dates.map(d => p.T2M[d]);
  const precData = dates.map(d => p.PRECTOTCORR[d]);

  timelineChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: currentLang === 'tr' ? 'Sıcaklık (°C)' : 'Temperature (°C)',
          data: t2mData, borderColor: '#b47b2b',
          backgroundColor: 'transparent', tension: 0.2, yAxisID: 'y'
        },
        {
          label: currentLang === 'tr' ? 'Yağış (mm/gün)' : 'Rain (mm/day)',
          data: precData, borderColor: '#236477',
          backgroundColor: 'rgba(35,100,119,0.15)', tension: 0.2, yAxisID: 'y1'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { type: 'linear', position: 'left', grid: { color: '#e5ebe0' }, ticks: { font: { family: 'JetBrains Mono', size: 11 } } },
        y1: { type: 'linear', position: 'right', grid: { display: false }, ticks: { font: { family: 'JetBrains Mono', size: 11 } } },
        x: { grid: { display: false }, ticks: { font: { family: 'JetBrains Mono', size: 10 } } }
      }
    }
  });
}

function downloadReport() {
  if (!appState.ort || !appState.rotationResult) {
    showBanner(currentLang === 'tr' ? 'Lütfen önce analizi tamamlayın.' : 'Please complete analysis first.');
    return;
  }
  const ort = appState.ort;
  const res = appState.rotationResult;
  const fieldSize = parseFloat(fieldSizeInput.value) || 50;
  const lines = [
    '=====================================================',
    '  SAGE — NASA POWER & COPERNICUS DECISION REPORT    ',
    '=====================================================',
    `Date: ${new Date().toLocaleString()}`,
    `Location: Lat ${latInput.value}°N, Lon ${lonInput.value}°E`,
    `Period: ${startDateInput.value} → ${endDateInput.value}`,
    `Field size: ${fieldSize} decare`,
    '',
    '1. NASA POWER CLIMATE OBSERVATIONS (DAILY AVG)',
    '-----------------------------------------------------',
    `- Mean Temperature: ${ort.sıcaklık_C} °C`,
    `- Daily Rainfall: ${ort.yağış_mm_gun} mm/day`,
    `- Solar Radiation: ${ort.güneş_MJ_m2_gun} MJ/m²/day`,
    `- Wind Speed: ${ort.rüzgar_m_s} m/s`,
    '',
    '2. ROTATION STRATEGIES',
    '-----------------------------------------------------'
  ];

  (res.stratejiler || []).forEach((strat, i) => {
    lines.push(`Route ${i + 1}: ${strat.ad}`);
    lines.push(`  Crop: ${strat.bitki} (Score: ${strat.skor}/100)`);
    lines.push(`  Rationale: ${strat.neden}`);
    lines.push(`  Evidence: ${strat.kanit}`);
    lines.push(`  Gains: ${(strat.faydalar || []).join(', ')}`);
    lines.push(`  Precautions: ${(strat.riskler || []).join(', ')}`);
    lines.push('');
  });

  if (res.si_analiz) {
    const si = res.si_analiz;
    lines.push('3. STATISTICAL INFERENCE (SI) & 5-YEAR CLIMATE TREND');
    lines.push('-----------------------------------------------------');
    lines.push(`- Temperature Trend: ${si.sicaklik_trend.slope > 0 ? '+' : ''}${si.sicaklik_trend.slope}°C/yr (R²=${si.sicaklik_trend.r2})`);
    if (si.sicaklik_trend.anomali) {
      lines.push(`  Anomaly (latest year): Z=${si.sicaklik_trend.anomali.z} (${si.sicaklik_trend.anomali.anomaly ? 'Significant Anomaly' : 'Normal Range'})`);
    }
    lines.push(`- Precipitation Trend: ${si.yagis_trend.slope > 0 ? '+' : ''}${si.yagis_trend.slope} mm/day/yr (R²=${si.yagis_trend.r2})`);
    if (si.yagis_trend.anomali) {
      lines.push(`  Anomaly (latest year): Z=${si.yagis_trend.anomali.z} (${si.yagis_trend.anomali.anomaly ? 'Significant Anomaly' : 'Normal Range'})`);
    }
    lines.push(`- Model Fit / Confidence: ${si.guven_duzeyi}%`);
    lines.push(`- Interpretation: ${si.yorumlama}`);
    lines.push('');
  }

  if (res.risk_uyarilari && res.risk_uyarilari.length) {
    lines.push('4. RISK WARNINGS');
    lines.push('-----------------------------------------------------');
    res.risk_uyarilari.forEach(r => lines.push(`- ${r.mesaj}`));
    lines.push('');
  }

  lines.push('Data Source: NASA POWER Daily Agroclimatology (power.larc.nasa.gov)');
  lines.push('Note: This report is a decision support simulation.');

  const blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `sage_decision_report_${formatDateForAPI(startDateInput.value)}.txt`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function setupUIListeners() {
  // Geocode button
  btnGeocode?.addEventListener('click', geocodeAddress);
  addressInput?.addEventListener('keydown', (e) => { if (e.key === 'Enter') geocodeAddress(); });

  // Geolocate
  document.getElementById('btnGeolocate')?.addEventListener('click', () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(pos => {
        updateCoords(pos.coords.latitude, pos.coords.longitude);
        if (leafletMap) leafletMap.setView([pos.coords.latitude, pos.coords.longitude], 10);
      }, () => {
        showBanner(currentLang === 'tr' ? 'Cihaz konumuna erişilemedi.' : 'Could not access device location.');
      });
    }
  });

  // Tabs
  document.querySelectorAll('.tabs-group .tab-toggle').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tabs-group .tab-toggle').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const targetId = btn.dataset.tab;
      document.querySelectorAll('.tab-pane').forEach(p => p.style.display = 'none');
      const activePane = document.getElementById(targetId);
      if (activePane) activePane.style.display = 'block';
    });
  });

  document.getElementById('btnDownloadReport')?.addEventListener('click', downloadReport);
  document.getElementById('btnPrintReport')?.addEventListener('click', () => { window.print(); });
  btnAnalyze.addEventListener('click', runFullAnalysis);
  btnLang.addEventListener('click', () => { setLanguage(currentLang === 'en' ? 'tr' : 'en'); });
  document.getElementById('btnAddHistoryCrop')?.addEventListener('click', addHistoryCropRow);

  // Theme Toggle (Dark / Light Mode)
  const btnTheme = document.getElementById('btnThemeToggle');
  const iconMoon = btnTheme?.querySelector('.icon-moon');
  const iconSun = btnTheme?.querySelector('.icon-sun');

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    try { localStorage.setItem('sage_theme', theme); } catch (e) {}
    if (iconMoon && iconSun) {
      if (theme === 'dark') {
        iconMoon.style.display = 'none';
        iconSun.style.display = 'inline-block';
      } else {
        iconMoon.style.display = 'inline-block';
        iconSun.style.display = 'none';
      }
    }
  }

  btnTheme?.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
    applyTheme(current === 'dark' ? 'light' : 'dark');
  });

  // Load saved theme or system preference
  try {
    const savedTheme = localStorage.getItem('sage_theme');
    if (savedTheme) {
      applyTheme(savedTheme);
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      applyTheme('dark');
    }
  } catch (e) {}

  // Smooth scroll for nav anchor buttons
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      const targetId = this.getAttribute('href').slice(1);
      const targetEl = document.getElementById(targetId);
      if (targetEl) {
        e.preventDefault();
        targetEl.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });

  // Action sample buttons inside story flow
  const sampleMap = {
    konya: { lat: 37.8746, lon: 32.4932, crop: 'misir', prev: 'bugday', name: 'Konya Ovası' },
    urfa: { lat: 37.1674, lon: 38.7955, crop: 'pamuk', prev: 'pamuk', name: 'Şanlıurfa Harran' },
    trakya: { lat: 41.4033, lon: 27.3578, crop: 'aycicegi', prev: 'bugday', name: 'Trakya' }
  };

  document.querySelectorAll('.action-sample-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const key = btn.dataset.demo;
      const data = sampleMap[key];
      if (!data) return;

      const appEl = document.getElementById('appWorkspace');
      if (appEl) appEl.scrollIntoView({ behavior: 'smooth' });

      updateCoords(data.lat, data.lon);
      if (leafletMap) leafletMap.setView([data.lat, data.lon], 10);
      if (mevcutCropSelect) mevcutCropSelect.value = data.crop || '';

      const firstPrevSelect = document.querySelector('.previous-crop-select');
      if (firstPrevSelect && data.prev) firstPrevSelect.value = data.prev;

      showBanner(currentLang === 'tr' ? `${data.name} tarlası yüklendi, NASA analizi başlatılıyor…` : `${data.name} field loaded, starting NASA analysis…`, true);
      await runFullAnalysis();
    });
  });

  // Quick demo buttons for Jury
  document.querySelectorAll('.quick-demo-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const lat = parseFloat(btn.dataset.lat);
      const lon = parseFloat(btn.dataset.lon);
      const crop = btn.dataset.crop;
      const prev = btn.dataset.prev;

      updateCoords(lat, lon);
      if (leafletMap) leafletMap.setView([lat, lon], 10);
      if (mevcutCropSelect) mevcutCropSelect.value = crop || '';

      const firstPrevSelect = document.querySelector('.previous-crop-select');
      if (firstPrevSelect && prev) firstPrevSelect.value = prev;

      showBanner(currentLang === 'tr' ? `${btn.querySelector('.demo-city').textContent} tarlası yüklendi, NASA analizi başlatılıyor…` : `${btn.querySelector('.demo-city').textContent} field loaded, starting NASA analysis…`, true);
      await runFullAnalysis();
    });
  });
  [latInput, lonInput].forEach(inp => {
    inp.addEventListener('change', () => {
      const lat = parseFloat(latInput.value);
      const lon = parseFloat(lonInput.value);
      if (!isNaN(lat) && !isNaN(lon) && mapMarker) {
        mapMarker.setLatLng([lat, lon]);
        leafletMap.panTo([lat, lon]);
      }
    });
  });
}

document.addEventListener('DOMContentLoaded', async () => {
  initLeaflet();
  await loadCrops();
  initPills();
  setupUIListeners();
  let savedLang = 'tr';
  try { savedLang = localStorage.getItem('sage_lang') === 'en' ? 'en' : 'tr'; } catch (e) {}
  setLanguage(savedLang);
  const demo = new URLSearchParams(window.location.search).get('demo');
  const demoButtons = { konya: 'btnDemoKonya', urfa: 'btnDemoUrfa', trakya: 'btnDemoTrakya' };
  if (Object.hasOwn(demoButtons, demo)) document.getElementById(demoButtons[demo])?.click();
});
