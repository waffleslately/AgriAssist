// ===== NEON INTERACTIVE CONTROLLER (THEME, DRONE SIMULATOR, ANALYTICS) =====

const NeonState = {
  droneSensorMode: 'ndvi',
  isFlying: false,
  dronePos: { x: 40, y: 30 },
  gridData: [],
  currentCrop: 'wheat',
  analyticsData: {},
  cropProfiles: {
    wheat: {
      name: "Wheat",
      nameHi: "गेहूं",
      icon: "🌾",
      season: "Rabi",
      kpiRevenue: "₹ 14.8 L",
      kpiRain: "505 mm",
      kpiStress: "7.2%",
      maxRevScale: 6.0,
      maxRevLabel: "₹6L",
      midRevLabel: "₹3L",
      revHistory: [
        { year: 2021, val: 1.9, label: "₹1.9L" },
        { year: 2022, val: 2.4, label: "₹2.4L" },
        { year: 2023, val: 3.1, label: "₹3.1L" },
        { year: 2024, val: 4.2, label: "₹4.2L" },
        { year: 2025, val: 4.9, label: "₹4.9L" },
        { year: 2026, val: 5.4, label: "₹5.4L" }
      ],
      stressHistory: [38.0, 34.0, 21.0, 12.0, 8.5, 6.8],
      auditNotes: {
        2021: { rev: "₹ 1.92 L", rain: "420 mm", stress: "38.0%", note: "Conventional flood irrigation, high yellow rust incidence in lower field." },
        2022: { rev: "₹ 2.41 L", rain: "580 mm", stress: "34.0%", note: "Heavy monsoon, moderate waterlogging in lower khet; nitrogen leaching observed." },
        2023: { rev: "₹ 3.12 L", rain: "385 mm", stress: "21.0%", note: "Soil Health Card overrides adopted, NPK balance calibrated for Ludhiana loam." },
        2024: { rev: "₹ 4.25 L", rain: "640 mm", stress: "12.0%", note: "DGCA drone ultra-low volume spray introduced, weed clusters eradicated." },
        2025: { rev: "₹ 4.90 L", rain: "510 mm", stress: "8.5%", note: "Precision multispectral scouting; record wheat yield (25.5 quintals/Acre)." },
        2026: { rev: "₹ 5.40 L (Proj)", rain: "495 mm (Est)", stress: "6.8%", note: "AI forecasted yield based on current 0.74 Sentinel NDVI and healthy vigor." }
      }
    },
    paddy: {
      name: "Paddy / Rice",
      nameHi: "धान",
      icon: "🍃",
      season: "Kharif",
      kpiRevenue: "₹ 16.5 L",
      kpiRain: "635 mm",
      kpiStress: "6.2%",
      maxRevScale: 7.0,
      maxRevLabel: "₹7L",
      midRevLabel: "₹3.5L",
      revHistory: [
        { year: 2021, val: 2.1, label: "₹2.1L" },
        { year: 2022, val: 2.6, label: "₹2.6L" },
        { year: 2023, val: 3.4, label: "₹3.4L" },
        { year: 2024, val: 4.5, label: "₹4.5L" },
        { year: 2025, val: 5.2, label: "₹5.2L" },
        { year: 2026, val: 5.8, label: "₹5.8L" }
      ],
      stressHistory: [36.0, 31.0, 19.0, 11.0, 7.5, 6.2],
      auditNotes: {
        2021: { rev: "₹ 2.10 L", rain: "590 mm", stress: "36.0%", note: "Bacterial leaf blight incidence during humid monsoon conditions." },
        2022: { rev: "₹ 2.65 L", rain: "680 mm", stress: "31.0%", note: "Yellow stem borer managed with trichogramma cards and pheromone traps." },
        2023: { rev: "₹ 3.40 L", rain: "540 mm", stress: "19.0%", note: "AWD (Alternate Wetting & Drying) water saving protocol adopted." },
        2024: { rev: "₹ 4.55 L", rain: "710 mm", stress: "11.0%", note: "Neem coated urea and zinc application significantly increased effective tillers." },
        2025: { rev: "₹ 5.20 L", rain: "620 mm", stress: "7.5%", note: "Optimal panicle density achieved with PR-126 short duration seed." },
        2026: { rev: "₹ 5.80 L (Proj)", rain: "605 mm (Est)", stress: "6.2%", note: "Sentinel-2 canopy moisture index predicts high biomass harvest." }
      }
    },
    cotton: {
      name: "Cotton",
      nameHi: "कपास",
      icon: "☁️",
      season: "Kharif",
      kpiRevenue: "₹ 22.8 L",
      kpiRain: "465 mm",
      kpiStress: "9.5%",
      maxRevScale: 9.0,
      maxRevLabel: "₹9L",
      midRevLabel: "₹4.5L",
      revHistory: [
        { year: 2021, val: 2.8, label: "₹2.8L" },
        { year: 2022, val: 3.4, label: "₹3.4L" },
        { year: 2023, val: 4.3, label: "₹4.3L" },
        { year: 2024, val: 5.6, label: "₹5.6L" },
        { year: 2025, val: 6.4, label: "₹6.4L" },
        { year: 2026, val: 7.2, label: "₹7.2L" }
      ],
      stressHistory: [42.0, 35.0, 22.0, 14.0, 10.0, 9.5],
      auditNotes: {
        2021: { rev: "₹ 2.80 L", rain: "410 mm", stress: "42.0%", note: "Early squaring stage faced severe pink bollworm pressure." },
        2022: { rev: "₹ 3.40 L", rain: "520 mm", stress: "35.0%", note: "Whitefly resurgence checked with yellow sticky cards and neem oil." },
        2023: { rev: "₹ 4.30 L", rain: "380 mm", stress: "22.0%", note: "Drip fertigation adoption cut square shedding by 40%." },
        2024: { rev: "₹ 5.60 L", rain: "560 mm", stress: "14.0%", note: "Targeted drone ultra-low volume canopy spray saved critical upper bolls." },
        2025: { rev: "₹ 6.40 L", rain: "450 mm", stress: "10.0%", note: "High micronaire premium staple fetched ₹7,450/qtl at APMC mandi." },
        2026: { rev: "₹ 7.20 L (Proj)", rain: "440 mm (Est)", stress: "9.5%", note: "Thermal-NDVI vigor index confirms superior boll retention forecast." }
      }
    },
    maize: {
      name: "Maize",
      nameHi: "मक्का",
      icon: "🌽",
      season: "Kharif",
      kpiRevenue: "₹ 15.2 L",
      kpiRain: "520 mm",
      kpiStress: "7.0%",
      maxRevScale: 6.5,
      maxRevLabel: "₹6.5L",
      midRevLabel: "₹3.2L",
      revHistory: [
        { year: 2021, val: 1.8, label: "₹1.8L" },
        { year: 2022, val: 2.3, label: "₹2.3L" },
        { year: 2023, val: 3.0, label: "₹3.0L" },
        { year: 2024, val: 4.1, label: "₹4.1L" },
        { year: 2025, val: 4.8, label: "₹4.8L" },
        { year: 2026, val: 5.3, label: "₹5.3L" }
      ],
      stressHistory: [35.0, 29.0, 18.0, 11.5, 8.0, 7.0],
      auditNotes: {
        2021: { rev: "₹ 1.80 L", rain: "430 mm", stress: "35.0%", note: "Fall armyworm whorl feeding damage reduced early vegetative leaf area." },
        2022: { rev: "₹ 2.30 L", rain: "560 mm", stress: "29.0%", note: "Emamectin benzoate bio-pesticide spray stabilized central tassel emergence." },
        2023: { rev: "₹ 3.00 L", rain: "390 mm", stress: "18.0%", note: "Ridge and furrow planting improved root anchorage against lodging." },
        2024: { rev: "₹ 4.10 L", rain: "610 mm", stress: "11.5%", note: "Balanced potash fertilization accelerated kernel filling and cob girth." },
        2025: { rev: "₹ 4.80 L", rain: "530 mm", stress: "8.0%", note: "High test-weight grain procured smoothly at local Mandi." },
        2026: { rev: "₹ 5.30 L (Proj)", rain: "510 mm (Est)", stress: "7.0%", note: "Thermal canopy sensor shows zero drought stress during silking." }
      }
    },
    mustard: {
      name: "Mustard & Rapeseed",
      nameHi: "सरसों",
      icon: "🌼",
      season: "Rabi",
      kpiRevenue: "₹ 13.9 L",
      kpiRain: "320 mm",
      kpiStress: "5.8%",
      maxRevScale: 5.5,
      maxRevLabel: "₹5.5L",
      midRevLabel: "₹2.8L",
      revHistory: [
        { year: 2021, val: 1.6, label: "₹1.6L" },
        { year: 2022, val: 2.1, label: "₹2.1L" },
        { year: 2023, val: 2.8, label: "₹2.8L" },
        { year: 2024, val: 3.7, label: "₹3.7L" },
        { year: 2025, val: 4.4, label: "₹4.4L" },
        { year: 2026, val: 4.9, label: "₹4.9L" }
      ],
      stressHistory: [31.0, 26.0, 16.0, 10.0, 7.0, 5.8],
      auditNotes: {
        2021: { rev: "₹ 1.60 L", rain: "290 mm", stress: "31.0%", note: "Mustard aphid outbreak during cloudy winter flowering period." },
        2022: { rev: "₹ 2.10 L", rain: "360 mm", stress: "26.0%", note: "Yellow sticky traps and neem spray managed aphid colonies effectively." },
        2023: { rev: "₹ 2.80 L", rain: "280 mm", stress: "16.0%", note: "Sulfur application (25 kg/ha) raised seed oil content to 41.5%." },
        2024: { rev: "₹ 3.70 L", rain: "390 mm", stress: "10.0%", note: "Drone spray eradicated Alternaria blight patches in lower valley." },
        2025: { rev: "₹ 4.40 L", rain: "310 mm", stress: "7.0%", note: "Giriraj high-yielding variety produced 8.2 qtl/acre harvest." },
        2026: { rev: "₹ 4.90 L (Proj)", rain: "300 mm (Est)", stress: "5.8%", note: "Excellent pod development index recorded across plot." }
      }
    },
    sugarcane: {
      name: "Sugarcane",
      nameHi: "गन्ना",
      icon: "🎋",
      season: "Annual",
      kpiRevenue: "₹ 31.5 L",
      kpiRain: "790 mm",
      kpiStress: "8.1%",
      maxRevScale: 12.0,
      maxRevLabel: "₹12L",
      midRevLabel: "₹6L",
      revHistory: [
        { year: 2021, val: 3.6, label: "₹3.6L" },
        { year: 2022, val: 4.8, label: "₹4.8L" },
        { year: 2023, val: 6.2, label: "₹6.2L" },
        { year: 2024, val: 7.9, label: "₹7.9L" },
        { year: 2025, val: 9.4, label: "₹9.4L" },
        { year: 2026, val: 10.8, label: "₹10.8L" }
      ],
      stressHistory: [39.0, 32.0, 20.0, 13.0, 9.5, 8.1],
      auditNotes: {
        2021: { rev: "₹ 3.60 L", rain: "710 mm", stress: "39.0%", note: "Early shoot borer attack in spring cane planting." },
        2022: { rev: "₹ 4.80 L", rain: "840 mm", stress: "32.0%", note: "Trichogramma chilonis release controlled internode borer." },
        2023: { rev: "₹ 6.20 L", rain: "690 mm", stress: "20.0%", note: "Trash mulching and wide-row trench planting preserved subsoil moisture." },
        2024: { rev: "₹ 7.90 L", rain: "880 mm", stress: "13.0%", note: "Bio-fertilizer inoculation and ratoon management boosted cane weight." },
        2025: { rev: "₹ 9.40 L", rain: "760 mm", stress: "9.5%", note: "Co-0238 variety delivered 335 quintals/acre to local sugar mill." },
        2026: { rev: "₹ 10.8 L (Proj)", rain: "740 mm (Est)", stress: "8.1%", note: "High sucrose Brix reading forecasted based on thermal vigor." }
      }
    },
    chickpea: {
      name: "Gram / Chickpea",
      nameHi: "चना",
      icon: "🌿",
      season: "Rabi",
      kpiRevenue: "₹ 12.6 L",
      kpiRain: "340 mm",
      kpiStress: "6.5%",
      maxRevScale: 5.0,
      maxRevLabel: "₹5L",
      midRevLabel: "₹2.5L",
      revHistory: [
        { year: 2021, val: 1.5, label: "₹1.5L" },
        { year: 2022, val: 1.9, label: "₹1.9L" },
        { year: 2023, val: 2.6, label: "₹2.6L" },
        { year: 2024, val: 3.4, label: "₹3.4L" },
        { year: 2025, val: 4.1, label: "₹4.1L" },
        { year: 2026, val: 4.6, label: "₹4.6L" }
      ],
      stressHistory: [33.0, 27.0, 17.0, 11.0, 7.8, 6.5],
      auditNotes: {
        2021: { rev: "₹ 1.50 L", rain: "310 mm", stress: "33.0%", note: "Fusarium wilt spots noticed in low-lying clay patches." },
        2022: { rev: "₹ 1.90 L", rain: "370 mm", stress: "27.0%", note: "Trichoderma viride seed treatment halted wilt progression." },
        2023: { rev: "₹ 2.60 L", rain: "290 mm", stress: "17.0%", note: "Rhizobium inoculation enhanced root nodulation and nitrogen uptake." },
        2024: { rev: "₹ 3.40 L", rain: "410 mm", stress: "11.0%", note: "Pheromone traps successfully restricted Helicoverpa pod borer damage." },
        2025: { rev: "₹ 4.10 L", rain: "330 mm", stress: "7.8%", note: "Desi Chana fetched solid returns at government procurement center." },
        2026: { rev: "₹ 4.60 L (Proj)", rain: "320 mm (Est)", stress: "6.5%", note: "High branching canopy density confirms positive harvest outlook." }
      }
    },
    soybean: {
      name: "Soybean",
      nameHi: "सोयाबीन",
      icon: "🌱",
      season: "Kharif",
      kpiRevenue: "₹ 14.1 L",
      kpiRain: "580 mm",
      kpiStress: "7.4%",
      maxRevScale: 6.0,
      maxRevLabel: "₹6L",
      midRevLabel: "₹3L",
      revHistory: [
        { year: 2021, val: 1.7, label: "₹1.7L" },
        { year: 2022, val: 2.2, label: "₹2.2L" },
        { year: 2023, val: 2.9, label: "₹2.9L" },
        { year: 2024, val: 3.8, label: "₹3.8L" },
        { year: 2025, val: 4.5, label: "₹4.5L" },
        { year: 2026, val: 5.1, label: "₹5.1L" }
      ],
      stressHistory: [34.0, 28.0, 18.5, 12.0, 8.5, 7.4],
      auditNotes: {
        2021: { rev: "₹ 1.70 L", rain: "510 mm", stress: "34.0%", note: "Girdle beetle and semilooper infestation during pod initiation." },
        2022: { rev: "₹ 2.20 L", rain: "640 mm", stress: "28.0%", note: "Yellow mosaic virus vectors suppressed with early border trapping." },
        2023: { rev: "₹ 2.90 L", rain: "460 mm", stress: "18.5%", note: "Broad bed furrow (BBF) layout prevented waterlogging." },
        2024: { rev: "₹ 3.80 L", rain: "680 mm", stress: "12.0%", note: "Foliar boron and potassium spray increased seed filling rate." },
        2025: { rev: "₹ 4.50 L", rain: "570 mm", stress: "8.5%", note: "JS-2034 variety produced uniform yellow grain with high oil content." },
        2026: { rev: "₹ 5.10 L (Proj)", rain: "550 mm (Est)", stress: "7.4%", note: "Canopy reflectance indicates optimal biomass accumulation." }
      }
    },
    potato: {
      name: "Potato",
      nameHi: "आलू",
      icon: "🥔",
      season: "Rabi",
      kpiRevenue: "₹ 18.9 L",
      kpiRain: "310 mm",
      kpiStress: "6.9%",
      maxRevScale: 8.0,
      maxRevLabel: "₹8L",
      midRevLabel: "₹4L",
      revHistory: [
        { year: 2021, val: 2.4, label: "₹2.4L" },
        { year: 2022, val: 3.0, label: "₹3.0L" },
        { year: 2023, val: 3.9, label: "₹3.9L" },
        { year: 2024, val: 4.8, label: "₹4.8L" },
        { year: 2025, val: 5.8, label: "₹5.8L" },
        { year: 2026, val: 6.5, label: "₹6.5L" }
      ],
      stressHistory: [37.0, 30.0, 19.0, 12.0, 8.2, 6.9],
      auditNotes: {
        2021: { rev: "₹ 2.40 L", rain: "280 mm", stress: "37.0%", note: "Late blight scare during unseasonal foggy week in January." },
        2022: { rev: "₹ 3.00 L", rain: "350 mm", stress: "30.0%", note: "Mancozeb preventive protective spray prevented tuber infection." },
        2023: { rev: "₹ 3.90 L", rain: "270 mm", stress: "19.0%", note: "Drip fertigation with water-soluble 13-0-45 improved tuber size grade." },
        2024: { rev: "₹ 4.80 L", rain: "380 mm", stress: "12.0%", note: "Dehaulming 10 days before harvest ensured tough skin formation." },
        2025: { rev: "₹ 5.80 L", rain: "290 mm", stress: "8.2%", note: "Kufri Pukhraj delivered 112 quintals/acre premium table potatoes." },
        2026: { rev: "₹ 6.50 L (Proj)", rain: "280 mm (Est)", stress: "6.9%", note: "Thermal canopy mapping confirms healthy underground tuber bulking." }
      }
    }
  }
};

// =========================================================
// 1. THEME SWITCHER (ORGANIC LIGHT <-> CYBER NEON DARK)
// =========================================================
window.toggleTheme = function() {
  const current = document.documentElement.getAttribute('data-theme') || 'light';
  const nextTheme = current === 'light' ? 'dark' : 'light';
  
  document.documentElement.setAttribute('data-theme', nextTheme);
  localStorage.setItem('agriassist-theme', nextTheme);
  
  const icon = document.getElementById('theme-icon');
  const text = document.getElementById('theme-text');
  
  if (nextTheme === 'dark') {
    if (icon) icon.textContent = '⚡';
    if (text) text.textContent = 'Neon Black';
    showToast("⚡ Cyber Neon-Black Mode Activated!");
  } else {
    if (icon) icon.textContent = '🌓';
    if (text) text.textContent = 'Theme: Light';
    showToast("🌾 Organic Light Theme Activated!");
  }

  if (window.map) {
    try { window.map.invalidateSize(); } catch(e) {}
  }
  initDroneCanvas();
};

// Apply saved theme on page load
document.addEventListener('DOMContentLoaded', () => {
  const savedTheme = localStorage.getItem('agriassist-theme');
  if (savedTheme) {
    document.documentElement.setAttribute('data-theme', savedTheme);
    const icon = document.getElementById('theme-icon');
    const text = document.getElementById('theme-text');
    if (savedTheme === 'dark') {
      if (icon) icon.textContent = '⚡';
      if (text) text.textContent = 'Neon Black';
    }
  }
  initDroneCanvas();
});

// =========================================================
// 2. DRONE SIMULATOR 🚁
// =========================================================
window.initDroneCanvas = function() {
  const canvas = document.getElementById('drone-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  if (NeonState.gridData.length === 0) {
    for (let r = 0; r < 6; r++) {
      for (let c = 0; c < 14; c++) {
        let type = "healthy";
        if (r === 2 && (c === 4 || c === 5)) type = "weed";
        else if (r === 4 && (c >= 8 && c <= 10)) type = "stressed";
        else if (r === 0 && c === 12) type = "bare";
        NeonState.gridData.push({ row: r, col: c, type: type, scanned: false });
      }
    }
  }

  renderDroneCanvas(ctx, canvas);

  canvas.onclick = function(e) {
    const rect = canvas.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    const colW = canvas.width / 14;
    const rowH = canvas.height / 6;
    const col = Math.floor(clickX / colW);
    const row = Math.floor(clickY / rowH);

    const cell = NeonState.gridData.find(g => g.row === row && g.col === col);
    if (cell) {
      let info = "";
      if (cell.type === 'healthy') info = "🟢 <strong>Zone Row " + (row+1) + ", Col " + (col+1) + "</strong>: Vigorous Canopy (NDVI 0.78). Chlorophyll optimum. Standard irrigation recommended.";
      else if (cell.type === 'weed') info = "🔴 <strong>Zone Row " + (row+1) + ", Col " + (col+1) + "</strong>: Invasive Weed Cluster (Phalaris minor). Targeted spot herbicide uploaded to mission.";
      else if (cell.type === 'stressed') info = "🟡 <strong>Zone Row " + (row+1) + ", Col " + (col+1) + "</strong>: Nitrogen Deficiency / Moisture Deficit (NDVI 0.46). Supplementary foliar urea spray advised.";
      else info = "🟤 <strong>Zone Row " + (row+1) + ", Col " + (col+1) + "</strong>: Emergence Gap. Soil exposed, check seed drill calibration.";
      
      const inspectEl = document.getElementById('zone-inspect-txt');
      if (inspectEl) inspectEl.innerHTML = info;
      showToast("Inspected Field Zone (" + (row+1) + ", " + (col+1) + ")");
    }
  };
};

function renderDroneCanvas(ctx, canvas) {
  if (!ctx || !canvas) return;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const colW = canvas.width / 14;
  const rowH = canvas.height / 6;
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';

  NeonState.gridData.forEach(cell => {
    const x = cell.col * colW;
    const y = cell.row * rowH;

    let color = isDark ? "#091a11" : "#1b4332";
    if (NeonState.droneSensorMode === 'ndvi') {
      if (cell.type === 'healthy') color = cell.scanned ? (isDark ? "#00ff88" : "#22c55e") : (isDark ? "#062113" : "#1e4834");
      else if (cell.type === 'weed') color = cell.scanned ? (isDark ? "#ff2a5f" : "#ef4444") : (isDark ? "#2a0610" : "#4a2424");
      else if (cell.type === 'stressed') color = cell.scanned ? (isDark ? "#ffd166" : "#f59e0b") : (isDark ? "#2b2204" : "#483e20");
      else color = cell.scanned ? "#8c5b36" : (isDark ? "#17120e" : "#38291f");
    } else if (NeonState.droneSensorMode === 'rgb') {
      color = cell.type === 'bare' ? "#a87146" : (cell.type === 'weed' ? "#3f6212" : "#15803d");
    } else {
      color = cell.type === 'stressed' ? "#ff2a5f" : "#00f0ff";
    }

    ctx.fillStyle = color;
    ctx.fillRect(x + 1, y + 1, colW - 2, rowH - 2);
  });

  // RENDER THE DRONE 🚁
  ctx.save();
  ctx.font = "26px sans-serif";
  ctx.fillText("🚁", NeonState.dronePos.x - 13, NeonState.dronePos.y + 8);

  // Neon Ion Thruster Ring
  ctx.strokeStyle = isDark ? "#00ff88" : "rgba(116, 198, 157, 0.6)";
  ctx.lineWidth = isDark ? 2.5 : 1.5;
  if (isDark) {
    ctx.shadowColor = "#00ff88";
    ctx.shadowBlur = 10;
  }
  ctx.beginPath();
  ctx.arc(NeonState.dronePos.x, NeonState.dronePos.y, 22, 0, Math.PI * 2);
  ctx.stroke();
  ctx.restore();
}

window.setDroneSensorMode = function(mode) {
  NeonState.droneSensorMode = mode;
  document.querySelectorAll('.drone-mode-btn').forEach(b => b.classList.remove('active'));
  const activeBtn = document.getElementById('btn-mode-' + mode);
  if (activeBtn) activeBtn.classList.add('active');

  // Also sync the select dropdown if present
  const sensorSelect = document.getElementById('drone-sensor');
  if (sensorSelect) {
    if (mode === 'ndvi') sensorSelect.value = 'multispectral_ndvi';
    else if (mode === 'rgb') sensorSelect.value = 'rgb_vari';
    else if (mode === 'thermal') sensorSelect.value = 'thermal_canopy';
  }

  const canvas = document.getElementById('drone-canvas');
  if (canvas) renderDroneCanvas(canvas.getContext('2d'), canvas);
  showToast("Sensor set to: " + mode.toUpperCase());
};

window.startDroneFlightSimulation = function() {
  if (NeonState.isFlying) return;
  NeonState.isFlying = true;

  const btn = document.getElementById('drone-launch-btn');
  if (btn) {
    btn.innerHTML = "<span>🚁</span> Drone Scanning...";
    btn.disabled = true;
  }

  const canvas = document.getElementById('drone-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  const waypoints = [
    { x: 30, y: 25 }, { x: 420, y: 25 },
    { x: 420, y: 65 }, { x: 30, y: 65 },
    { x: 30, y: 110 }, { x: 420, y: 110 },
    { x: 420, y: 155 }, { x: 30, y: 155 }
  ];

  let currentWpt = 0;
  const interval = setInterval(() => {
    const target = waypoints[currentWpt];
    const dx = target.x - NeonState.dronePos.x;
    const dy = target.y - NeonState.dronePos.y;

    NeonState.dronePos.x += dx * 0.16;
    NeonState.dronePos.y += dy * 0.16;

    const colW = canvas.width / 14;
    const rowH = canvas.height / 6;
    const col = Math.floor(NeonState.dronePos.x / colW);
    const row = Math.floor(NeonState.dronePos.y / rowH);
    const cell = NeonState.gridData.find(g => g.row === row && g.col === col);
    if (cell) cell.scanned = true;

    renderDroneCanvas(ctx, canvas);

    const scannedCount = NeonState.gridData.filter(g => g.scanned).length;
    const battEl = document.getElementById('hud-battery');
    const wptEl = document.getElementById('hud-wpt');
    const areaEl = document.getElementById('hud-area');

    if (battEl) battEl.textContent = Math.max(78, 98 - Math.floor(scannedCount / 4)) + "%";
    if (wptEl) wptEl.textContent = (currentWpt + 1) + " / " + waypoints.length;
    if (areaEl) areaEl.textContent = ((scannedCount / NeonState.gridData.length) * 3.8).toFixed(1) + " Ac";

    if (Math.abs(dx) < 6 && Math.abs(dy) < 6) {
      currentWpt++;
      if (currentWpt >= waypoints.length) {
        clearInterval(interval);
        NeonState.isFlying = false;
        if (btn) {
          btn.innerHTML = "<span>🚁</span> Launch Drone Flight Mission";
          btn.disabled = false;
        }
        showToast("🎉 Drone survey completed! Computing NDVI Grid...");
        if (typeof window.triggerDroneAnalysis === 'function') {
          window.triggerDroneAnalysis();
        }
      }
    }
  }, 45);
};

window.resetDroneCanvas = function() {
  NeonState.gridData.forEach(g => g.scanned = false);
  NeonState.dronePos = { x: 40, y: 30 };
  const wptEl = document.getElementById('hud-wpt');
  const areaEl = document.getElementById('hud-area');
  const battEl = document.getElementById('hud-battery');
  if (wptEl) wptEl.textContent = "0 / 8";
  if (areaEl) areaEl.textContent = "0.0 Ac";
  if (battEl) battEl.textContent = "98%";
  initDroneCanvas();
  showToast("Drone scan reset.");
};

// =========================================================
// 3. PEST CARDS & SEVERITY
// =========================================================
window.selectPestCard = function(elem, pestId) {
  document.querySelectorAll('.pest-card-item').forEach(c => c.classList.remove('selected'));
  if (elem) elem.classList.add('selected');

  // Sync with pest dropdown
  const pestKeySelect = document.getElementById('pest-key');
  if (pestKeySelect) pestKeySelect.value = pestId;

  const cropSelect = document.getElementById('pest-crop');
  if (cropSelect) {
    if (pestId === 'yellow_rust') cropSelect.value = 'wheat';
    else if (pestId === 'pink_bollworm' || pestId === 'whitefly') cropSelect.value = 'cotton';
    else if (pestId === 'fall_armyworm') cropSelect.value = 'maize';
    else if (pestId === 'blast' || pestId === 'yellow_stem_borer') cropSelect.value = 'paddy';
    else if (pestId === 'sugarcane_borer') cropSelect.value = 'sugarcane';
    else if (pestId === 'gram_pod_borer') cropSelect.value = 'gram';
    else if (pestId === 'mustard_aphid') cropSelect.value = 'mustard';
    else if (pestId === 'potato_late_blight') cropSelect.value = 'potato';
  }

  showToast("Selected pest: " + pestId.replace(/_/g, ' ').toUpperCase());
};

window.updateSeverityIndicator = function(val) {
  const label = document.getElementById('severity-val');
  if (label) label.textContent = val + '%';

  const alertBox = document.getElementById('etl-alert-box');
  if (alertBox) {
    if (val >= 25) {
      alertBox.style.display = 'block';
      alertBox.innerHTML = `🚨 <strong>ETL Breached (${val}%)</strong>: Economic Threshold Level exceeded. Immediate CIBRC-approved drone spray mandatory.`;
      alertBox.style.background = 'var(--chart-red-bg)';
      alertBox.style.color = 'var(--chart-red-primary)';
      alertBox.style.borderLeftColor = 'var(--chart-red-primary)';
    } else if (val >= 10) {
      alertBox.style.display = 'block';
      alertBox.innerHTML = `⚠️ <strong>Approaching Critical Threshold (${val}%)</strong>: Monitor trap catch counts daily and prep bio-pesticide.`;
      alertBox.style.background = 'var(--chart-green-bg)';
      alertBox.style.color = 'var(--ag-wheat)';
      alertBox.style.borderLeftColor = 'var(--ag-wheat)';
    } else {
      alertBox.style.display = 'block';
      alertBox.innerHTML = `✅ <strong>Below Economic Threshold (${val}%)</strong>: Safe level. Continue natural predator biological control.`;
      alertBox.style.background = 'var(--chart-green-bg)';
      alertBox.style.color = 'var(--chart-green-primary)';
      alertBox.style.borderLeftColor = 'var(--chart-green-primary)';
    }
  }
};

window.testDroneSprayAnimation = function() {
  showToast("💨 Testing Centrifugal Spray Atomizer: 180 Micron Droplet Cloud Active!");
};

// =========================================================
// 4. ANALYTICS SYNCHRONIZED YEAR INSPECTOR & CROP CONTROLLER
// =========================================================

window.getAnalyticsCropProfile = function(cropKey) {
  const key = (cropKey || 'wheat').toLowerCase().trim();
  if (NeonState.cropProfiles[key]) {
    return NeonState.cropProfiles[key];
  }
  // Generic profile for crops not predefined
  const cap = key.charAt(0).toUpperCase() + key.slice(1);
  return {
    name: cap,
    nameHi: cap,
    icon: "🌱",
    season: "Annual",
    kpiRevenue: "₹ 15.0 L",
    kpiRain: "480 mm",
    kpiStress: "7.0%",
    maxRevScale: 6.0,
    maxRevLabel: "₹6L",
    midRevLabel: "₹3L",
    revHistory: [
      { year: 2021, val: 1.8, label: "₹1.8L" },
      { year: 2022, val: 2.3, label: "₹2.3L" },
      { year: 2023, val: 3.1, label: "₹3.1L" },
      { year: 2024, val: 4.1, label: "₹4.1L" },
      { year: 2025, val: 4.8, label: "₹4.8L" },
      { year: 2026, val: 5.3, label: "₹5.3L" }
    ],
    stressHistory: [35.0, 30.0, 19.0, 12.0, 8.0, 7.0],
    auditNotes: {
      2021: { rev: "₹ 1.80 L", rain: "420 mm", stress: "35.0%", note: `Initial baseline cultivation for ${cap}.` },
      2022: { rev: "₹ 2.30 L", rain: "530 mm", stress: "30.0%", note: `Monsoon irrigation with organic mulch protection.` },
      2023: { rev: "₹ 3.10 L", rain: "380 mm", stress: "19.0%", note: `Soil Health Card calibrated nutrient management adopted.` },
      2024: { rev: "₹ 4.10 L", rain: "610 mm", stress: "12.0%", note: `Precision drone monitoring and weed suppression.` },
      2025: { rev: "₹ 4.80 L", rain: "490 mm", stress: "8.0%", note: `Optimal yield realization via government MSP/APMC mandi.` },
      2026: { rev: "₹ 5.30 L (Proj)", rain: "475 mm (Est)", stress: "7.0%", note: `Projected healthy harvest based on satellite vegetation index.` }
    }
  };
};

window.renderAnalyticsCropData = function(profile) {
  if (!profile) return;

  // 1. Update Titles & Tags
  const titleTag = document.getElementById('analytics-crop-title-tag');
  if (titleTag) titleTag.textContent = `${profile.name} (${profile.nameHi})`;

  const cardCropTag = document.getElementById('rev-card-crop-tag');
  if (cardCropTag) cardCropTag.textContent = `${profile.name} (${profile.nameHi})`;

  // 2. Update KPI Cards
  const kpiRev = document.getElementById('kpi-rev-val');
  if (kpiRev) kpiRev.textContent = profile.kpiRevenue;
  const kpiRain = document.getElementById('kpi-rain-val');
  if (kpiRain) kpiRain.textContent = profile.kpiRain;
  const kpiStress = document.getElementById('kpi-stress-val');
  if (kpiStress) kpiStress.textContent = profile.kpiStress;

  // 3. Update Graph 1 (Crop Revenue History SVG)
  const maxScale = profile.maxRevScale || 6.0;
  const yTop = document.getElementById('graph-rev-y-top');
  if (yTop) yTop.textContent = profile.maxRevLabel || `₹${maxScale}L`;
  const yMid = document.getElementById('graph-rev-y-mid');
  if (yMid) yMid.textContent = profile.midRevLabel || `₹${(maxScale/2).toFixed(1)}L`;

  const xCoords = [65, 140, 215, 290, 365, 440];
  const polyPoints = [];
  let nodesHtml = '';

  profile.revHistory.forEach((item, idx) => {
    const x = xCoords[idx];
    const y = Math.round(85 - (item.val / maxScale) * 70);
    polyPoints.push(`${x},${y}`);

    const isLast = (idx === profile.revHistory.length - 1);
    const yearLabel = isLast ? `${item.year}*` : `${item.year}`;
    const yearColor = isLast ? 'var(--chart-blue-primary)' : 'var(--ag-text-muted)';
    const yearWeight = isLast ? '800' : '700';

    nodesHtml += `
      <circle class="graph-dot-elem" cx="${x}" cy="${y}" r="4.5" fill="var(--chart-blue-primary)" stroke="#ffffff" stroke-width="2" onclick="selectAnalyticsYear(${item.year})"/>
      <text x="${x - 9}" y="99" font-size="9.5" fill="${yearColor}" font-weight="${yearWeight}">${yearLabel}</text>
      <text x="${x - 10}" y="${y - 8}" font-size="9" fill="var(--chart-blue-primary)" font-weight="800">${item.label}</text>
    `;
  });

  const polylineEl = document.getElementById('graph-rev-polyline');
  if (polylineEl) polylineEl.setAttribute('points', polyPoints.join(' '));

  const polygonEl = document.getElementById('graph-rev-polygon');
  if (polygonEl) {
    const polygonPoints = `65,85 ${polyPoints.join(' ')} 440,85`;
    polygonEl.setAttribute('points', polygonPoints);
  }

  const revNodesEl = document.getElementById('graph-rev-nodes');
  if (revNodesEl) revNodesEl.innerHTML = nodesHtml;

  // 4. Update Graph 3 (Field Stress SVG)
  const stressPoints = [];
  let stressNodesHtml = '';
  const stressHistory = profile.stressHistory || [38.0, 34.0, 21.0, 12.0, 8.5, 6.8];
  const years = [2021, 2022, 2023, 2024, 2025, 2026];

  stressHistory.forEach((val, idx) => {
    const x = xCoords[idx];
    const y = Math.round(85 - (val / 50.0) * 70);
    stressPoints.push(`${x},${y}`);

    const yr = years[idx];
    const isLast = (idx === years.length - 1);
    const yrLabel = isLast ? `${yr}*` : `${yr}`;
    const yrColor = isLast ? 'var(--chart-red-primary)' : 'var(--ag-text-muted)';
    const yrWeight = isLast ? '800' : '700';

    stressNodesHtml += `
      <circle class="graph-dot-elem" cx="${x}" cy="${y}" r="4.5" fill="var(--chart-red-primary)" stroke="#ffffff" stroke-width="2" onclick="selectAnalyticsYear(${yr})"/>
      <text x="${x - 9}" y="99" font-size="9.5" fill="${yrColor}" font-weight="${yrWeight}">${yrLabel}</text>
      <text x="${x - 9}" y="${y - 6}" font-size="9" fill="var(--chart-red-primary)" font-weight="800">${val}%</text>
    `;
  });

  const stressPolylineEl = document.getElementById('graph-stress-polyline');
  if (stressPolylineEl) stressPolylineEl.setAttribute('points', stressPoints.join(' '));

  const stressNodesEl = document.getElementById('graph-stress-nodes');
  if (stressNodesEl) stressNodesEl.innerHTML = stressNodesHtml;

  // 5. Update Synchronized Audit Data
  NeonState.analyticsData = profile.auditNotes;
  window.selectAnalyticsYear(2026, true);
};

window.setAnalyticsCrop = function(cropKey, silent) {
  const normKey = (cropKey || 'wheat').toLowerCase().trim();
  NeonState.currentCrop = normKey;

  // Sync dropdown
  const cropSelect = document.getElementById('analytics-crop-select');
  if (cropSelect && cropSelect.value !== normKey) {
    cropSelect.value = normKey;
  }

  // Sync quick-switch pill highlights
  document.querySelectorAll('.crop-pill').forEach(btn => {
    if (btn.getAttribute('data-crop') === normKey) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  // Render SVG graphs & KPIs
  const profile = window.getAnalyticsCropProfile(normKey);
  window.renderAnalyticsCropData(profile);

  // Re-fetch live Revenue Calculator for this crop
  const areaInput = document.getElementById('analytics-area-input');
  const areaVal = areaInput ? parseFloat(areaInput.value) : 2.5;
  if (typeof window.loadRevenueCalculator === 'function') {
    window.loadRevenueCalculator(null, normKey, areaVal);
  }

  if (!silent) {
    window.showToast(`${profile.icon} Analytics updated for ${profile.name} (${profile.nameHi})`);
  }
};

window.onAnalyticsCropChanged = function(cropKey) {
  window.setAnalyticsCrop(cropKey, false);
};

window.selectCropPill = function(cropKey) {
  window.setAnalyticsCrop(cropKey, false);
};

window.onAnalyticsPlotChanged = function(plotId) {
  const select = document.getElementById('analytics-plot-select');
  if (!select) return;
  const opt = select.options[select.selectedIndex];
  if (!opt) return;

  const area = parseFloat(opt.getAttribute('data-area')) || 2.5;
  const crop = opt.getAttribute('data-crop') || 'wheat';
  const state = opt.getAttribute('data-state') || 'Punjab';
  const district = opt.getAttribute('data-district') || 'Ludhiana';

  const areaInput = document.getElementById('analytics-area-input');
  if (areaInput) areaInput.value = area;

  window._currentRevenuePlotId = plotId;
  window._currentRevenueArea = area;
  window._currentRevenueState = state;
  window._currentRevenueDistrict = district;

  window.setAnalyticsCrop(crop, true);
  window.showToast(`📍 Switched to ${opt.text.split('(')[0].trim()}`);
};

window.onAnalyticsAreaChanged = function(val) {
  const area = parseFloat(val);
  if (isNaN(area) || area <= 0) return;
  window._currentRevenueArea = area;
  const crop = NeonState.currentCrop || 'wheat';
  if (typeof window.loadRevenueCalculator === 'function') {
    window.loadRevenueCalculator(null, crop, area);
  }
};

window.selectAnalyticsYear = function(year, silent) {
  const data = NeonState.analyticsData[year];
  if (!data) return;

  const syncBox = document.getElementById('analytics-sync-box');
  if (syncBox) {
    syncBox.innerHTML = `
      <div>
        <strong style="color:var(--ag-wheat);font-size:12px">📅 Year ${year} Synchronized Audit</strong>:
        <span style="color:var(--chart-blue-primary);margin-left:8px">🟦 Revenue: <strong>${data.rev}</strong></span> | 
        <span style="color:var(--chart-green-primary);margin-left:8px">🟩 Rainfall: <strong>${data.rain}</strong></span> | 
        <span style="color:var(--chart-red-primary);margin-left:8px">🟥 Stress Index: <strong>${data.stress}</strong></span>
        <div style="font-size:11px;color:var(--ag-text-muted);margin-top:4px;line-height:1.4">${data.note}</div>
      </div>
    `;
  }

  if (!silent) {
    showToast(`Loaded ${year} synchronized multi-variable metrics!`);
  }
};

// =========================================================
// 5. TOAST NOTIFICATION COMPONENT
// =========================================================
window.showToast = function(msg) {
  let t = document.getElementById('ag-toast');
  if (!t) {
    t = document.createElement('div');
    t.id = 'ag-toast';
    t.className = 'ag-toast';
    t.innerHTML = `<span>🌾</span> <span id="toast-text"></span>`;
    document.body.appendChild(t);
  }
  const textEl = document.getElementById('toast-text');
  if (textEl) textEl.textContent = msg;
  t.classList.add('show');
  clearTimeout(window._toastTimeout);
  window._toastTimeout = setTimeout(() => t.classList.remove('show'), 3500);
};

// =========================================================
// 6. TAB SWITCHING WITH CANVAS INIT HOOKS
// =========================================================
(function initTabSwitcher() {
  function switchTab(tabName) {
    // Deactivate all buttons and contents
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

    // Activate the selected button
    const btn = document.querySelector(`.tab-btn[data-tab="${tabName}"]`);
    if (btn) btn.classList.add('active');

    // Activate the selected content
    const content = document.getElementById(`tab-${tabName}`);
    if (content) content.classList.add('active');

    // Tab-specific hooks
    if (tabName === 'drone') {
      setTimeout(() => {
        if (typeof window.initDroneCanvas === 'function') {
          window.initDroneCanvas();
        }
      }, 50);
    }

    if (tabName === 'analytics') {
      setTimeout(() => {
        const crop = document.getElementById('analytics-crop-select')?.value || 'wheat';
        if (typeof window.setAnalyticsCrop === 'function') {
          window.setAnalyticsCrop(crop, true);
        } else if (typeof window.loadRevenueCalculator === 'function') {
          window.loadRevenueCalculator();
        }
      }, 50);
    }

    if (tabName === 'livestock') {
      // Trigger livestock map resize if needed
      if (window.map) {
        setTimeout(() => {
          try { window.map.invalidateSize(); } catch(e) {}
        }, 150);
      }
    }
  }

  // Expose globally so other scripts can call it
  window.switchTab = switchTab;

  // Attach click listeners to all tab buttons
  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const tabName = btn.getAttribute('data-tab');
        if (tabName) switchTab(tabName);
      });
    });

    // Init drone canvas for default view
    if (typeof window.initDroneCanvas === 'function') {
      window.initDroneCanvas();
    }
  });
})();
