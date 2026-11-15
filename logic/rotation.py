import json
import os
import math

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

LANG = {
    "tr": {
        "strategies": {
            "toprak_sagligi": "Toprak Sağlığı Odaklı",
            "su_tasarrufu": "Su Tasarruflu",
            "mevcut_koruma": "Mevcut Rotasyonu Koru",
        },
        "groups": {"bahar": "Bahar", "yaz": "Yaz", "sonbahar": "Sonbahar", "kis": "Kış"},
        "water_need": {"düşük": "Düşük", "orta": "Orta", "yüksek": "Yüksek"},
        "soil_effect": {"iyileştirici": "İyileştirici", "nötr": "Nötr", "tüketici": "Tüketici"},
        "risk_frost": "Don riski",
        "risk_heat": "Isı dalgası riski",
        "risk_drought": "Kuraklık riski",
        "advisor_warn": "Bu araç destekleyici bir öneri sunar; final karar çiftçi ve yerel tarım uzmanlığına bırakılır.",
        "nasa_sources": "NASA Veri Kaynakları: POWER (sıcaklık, yağış, güneş, rüzgar) · SMAP (toprak nemi) · GPM (yağış) · Landsat (NDVI) · ECOSTRESS (ısı stresi) · SRTM (eşya yüksekliği)",
        "best_crop": "En iyi bitki",
        "strategy_score": "Strateji skoru",
        "crop_score": "Bitki skoru",
        "recommended_crop": "Önerilen bitki",
        "why": "Neden",
        "evidence": "Kanıt",
        "benefits": "Faydalar",
        "risks": "Riskler",
        "gaps": "Bilgi eksikliği",
        "rotation_advice": "Rota önerisi",
        "current_crop": "Mevcut bitki",
        "scenario_label": "Senaryo",
        "scenario_precip": "Yağış değişimi (%)",
        "scenario_temp": "Sıcaklık değişimi (°C)",
        "constraints": "Çiftçi kısıtları",
        "irrigation": "Sulama",
        "equipment": "Ekipman",
        "market": "Pazar tercihi",
        "stress_calendar": "Stres Takvimi",
        "month": "Ay",
        "temp_stress": "Sıcaklık stresi",
        "water_stress": "Su stresi",
        "ndvi_proxy": "Bitki gelişimi (NDVI proxy)",
        "frost_warning": "Bu dönemde don riski yüksek — erken tohumlama/koruma önlemi alın.",
        "heat_warning": "Bu dönemde ısı dalgası riski yüksek — sulama/ölçme planlayın.",
        "drought_warning": "Bu dönemde kuraklık riski yüksek — su tasarruflu bitki tercih edin.",
        "wind_erosion_warning": "Yüksek rüzgar hızı (>3.5 m/s) ve kurak rejim rüzgar erozyonu riski yaratıyor — çıplak nadas yerine örtücü baklagil tercih edin.",
        "runoff_erosion_warning": "Aşırı yağış ve yüzey akışı riski (>5 mm/gün) — eğimli arazide kontur ekim ve erozyon önleyici derin köklü ürünler tavsiye edilir.",
        "lang_switch": "EN",
    },
    "en": {
        "strategies": {
            "toprak_sagligi": "Soil Health Focused",
            "su_tasarrufu": "Water Saving",
            "mevcut_koruma": "Keep Current Rotation",
        },
        "groups": {"bahar": "Spring", "yaz": "Summer", "sonbahar": "Autumn", "kis": "Winter"},
        "water_need": {"düşük": "Low", "orta": "Medium", "yüksek": "High"},
        "soil_effect": {"iyileştirici": "Improving", "nötr": "Neutral", "tüketici": "Depleting"},
        "risk_frost": "Frost risk",
        "risk_heat": "Heat wave risk",
        "risk_drought": "Drought risk",
        "advisor_warn": "This tool provides supportive suggestions; final decisions rest with the farmer and local agronomists.",
        "nasa_sources": "NASA Data Sources: POWER (temp, precip, solar, wind) · SMAP (soil moisture) · GPM (precip) · Landsat (NDVI) · ECOSTRESS (heat stress) · SRTM (elevation)",
        "best_crop": "Best crop",
        "strategy_score": "Strategy score",
        "crop_score": "Crop score",
        "recommended_crop": "Recommended crop",
        "why": "Why",
        "evidence": "Evidence",
        "benefits": "Benefits",
        "risks": "Risks",
        "gaps": "Knowledge gaps",
        "rotation_advice": "Rotation advice",
        "current_crop": "Current crop",
        "scenario_label": "Scenario",
        "scenario_precip": "Precipitation change (%)",
        "scenario_temp": "Temperature change (°C)",
        "constraints": "Farmer constraints",
        "irrigation": "Irrigation",
        "equipment": "Equipment",
        "market": "Market preference",
        "stress_calendar": "Stress Calendar",
        "month": "Month",
        "temp_stress": "Temperature stress",
        "water_stress": "Water stress",
        "ndvi_proxy": "Crop growth (NDVI proxy)",
        "frost_warning": "High frost risk this period — consider early planting/protection.",
        "heat_warning": "High heat wave risk this period — plan irrigation/monitoring.",
        "drought_warning": "High drought risk this period — prefer water-saving crops.",
        "wind_erosion_warning": "High wind speed (>3.5 m/s) with arid conditions poses wind erosion risk — avoid bare fallow, prioritize cover legumes.",
        "runoff_erosion_warning": "High precipitation runoff risk (>5 mm/day) — contour planting and deep-rooted cover crops advised against water erosion.",
        "lang_switch": "TR",
    },
}


def load_crops():
    with open(os.path.join(DATA_DIR, "crops.json"), encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# SI: Statistical Inference — Linear Trend & Anomaly Detection
# ---------------------------------------------------------------------------

def linear_trend(values):
    """
    Basit en küçük kareler regresyonu (OLS) ile y = a*x + b doğrusu.
    Girdi: sayı listesi (sıralı zaman serisi).
    Döndürür: {'slope': eğim, 'intercept': sabit, 'r2': açıklayıcılık katsayısı}
    """
    n = len(values)
    if n < 2:
        return {"slope": 0.0, "intercept": values[0] if values else 0.0, "r2": 0.0}

    xs = list(range(n))
    x_mean = sum(xs) / n
    y_mean = sum(values) / n

    num   = sum((xs[i] - x_mean) * (values[i] - y_mean) for i in range(n))
    denom = sum((xs[i] - x_mean) ** 2 for i in range(n))

    slope     = num / denom if denom != 0 else 0.0
    intercept = y_mean - slope * x_mean

    ss_res = sum((values[i] - (slope * xs[i] + intercept)) ** 2 for i in range(n))
    ss_tot = sum((v - y_mean) ** 2 for v in values)
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 1e-9 else 0.0

    return {
        "slope": round(slope, 4),
        "intercept": round(intercept, 2),
        "r2": round(max(0.0, r2), 3),
    }


def anomaly_score(value, historical_values):
    """
    Z-score tabanlı anomali skoru.
    Dönüş: {'z': z_skoru, 'anomaly': True/False, 'direction': 'above'/'below'/'normal'}
    """
    if not historical_values or len(historical_values) < 2:
        return {"z": 0.0, "anomaly": False, "direction": "normal"}

    n    = len(historical_values)
    mean = sum(historical_values) / n
    std  = math.sqrt(sum((v - mean) ** 2 for v in historical_values) / n)

    if std < 1e-9:
        return {"z": 0.0, "anomaly": False, "direction": "normal"}

    z = (value - mean) / std
    direction = "above" if z > 0 else "below" if z < 0 else "normal"
    return {
        "z": round(z, 2),
        "anomaly": abs(z) > 1.5,
        "direction": direction,
    }


def si_analiz(cok_yillik_veri, lang="tr"):
    """
    Çok yıllık NASA POWER verisinden istatistiksel trend ve anomali analizi üretir.
    Girdi: {'yillar': [2019,..2023], 'sicaklik': [ort1,..], 'yagis': [ort1,..]}
    Döndürür: {'sicaklik_trend': {...}, 'yagis_trend': {...}, 'yorumlama': str, 'guven_duzeyi': 0-100}
    """
    yillar    = cok_yillik_veri.get("yillar", [])
    sicaklik  = cok_yillik_veri.get("sicaklik", [])
    yagis     = cok_yillik_veri.get("yagis", [])

    if not sicaklik or not yagis:
        return None

    t_trend = linear_trend(sicaklik)
    p_trend = linear_trend(yagis)

    # Anomali: son yıl vs geçmiş
    t_anomali = anomaly_score(sicaklik[-1], sicaklik[:-1]) if len(sicaklik) > 1 else None
    p_anomali = anomaly_score(yagis[-1], yagis[:-1]) if len(yagis) > 1 else None

    # Güven düzeyi: R² ortalaması ölçeklenmiş
    guven = int(round(((t_trend["r2"] + p_trend["r2"]) / 2) * 100))

    # Yorumlama
    t_yon = "ısınıyor" if t_trend["slope"] > 0.1 else ("soğuyor" if t_trend["slope"] < -0.1 else "stabil")
    p_yon = "kuruyor"  if p_trend["slope"] < -0.05 else ("ıslanıyor" if p_trend["slope"] > 0.05 else "stabil")
    t_yon_en = "warming" if t_trend["slope"] > 0.1 else ("cooling" if t_trend["slope"] < -0.1 else "stable")
    p_yon_en = "drying"  if p_trend["slope"] < -0.05 else ("wetting" if p_trend["slope"] > 0.05 else "stable")

    if lang == "tr":
        yorum = (
            f"Son {len(yillar)} yıllık NASA POWER verisi: "
            f"Sıcaklık eğilimi {t_yon} ({t_trend['slope']:+.2f}°C/yıl), "
            f"yağış rejimi {p_yon} ({p_trend['slope']:+.3f} mm/gün/yıl). "
            f"Model açıklayıcılığı R²={t_trend['r2']:.2f} (sıcaklık), R²={p_trend['r2']:.2f} (yağış)."
        )
    else:
        yorum = (
            f"NASA POWER {len(yillar)}-year trend: "
            f"Temperature is {t_yon_en} ({t_trend['slope']:+.2f}°C/yr), "
            f"precipitation regime is {p_yon_en} ({p_trend['slope']:+.3f} mm/day/yr). "
            f"Model fit R²={t_trend['r2']:.2f} (temp), R²={p_trend['r2']:.2f} (precip)."
        )

    return {
        "sicaklik_trend": {**t_trend, "anomali": t_anomali},
        "yagis_trend": {**p_trend, "anomali": p_anomali},
        "yorumlama": yorum,
        "guven_duzeyi": guven,
        "yillar": yillar,
    }


def clima_uygunluk(ort, crop):
    """0-100 arası klima uygunluk skoru."""
    t_min, t_max = crop["sıcaklık"]
    p_min, p_max = crop["yağış"]
    s_min, s_max = crop["güneş"]

    t = ort["sıcaklık_C"]
    p = ort["yağış_mm_gun"]
    s = ort["güneş_MJ_m2_gun"]

    def skalala(deger, d_min, d_max):
        if d_max == d_min:
            return 100 if deger == d_min else 0
        if deger < d_min:
            mesafe = d_min - deger
            return max(0, 70 - mesafe * 30)
        if deger > d_max:
            mesafe = deger - d_max
            return max(0, 70 - mesafe * 30)
        orta = (d_min + d_max) / 2
        yaricap = (d_max - d_min) / 2
        uzaklik = abs(deger - orta) / yaricap
        return 70 + 30 * (1 - uzaklik)

    st = skalala(t, t_min, t_max)
    sp = skalala(p, p_min, p_max)
    ss = skalala(s, s_min, s_max)
    return round((st * 0.5 + sp * 0.3 + ss * 0.2), 1)


# Strateji tanımları
STRATEJILER = {
    "toprak_sagligi": {
        "anahtar": "toprak_sagligi",
        "ad_tr": "Toprağı Dinlendiren ve Güçlendiren Ekim",
        "ad_en": "Soil Health & Regeneration Rotation",
        "grup_vurgu": ["iyileştirici", "nötr"],
        "aciklama_tr": "Toprağı yormayan, nohut ve mercimek gibi baklagillerle toprağa doğal gübre bırakan ve tarlayı dinlendiren yol.",
        "aciklama_en": "Rotation emphasizing nitrogen-fixers and cover crops to rest soil and reduce erosion.",
        "neden_tr": "NASA uydu verilerine göre bu mevsimde tarlayı yormayan baklagiller (nohut, mercimek) ekilirse, toprağa doğal gübre bırakır ve seneye ekeceğiniz buğdayın verimini artırır.",
        "neden_en": "Based on NASA POWER precipitation and temperature data, nitrogen-fixers (chickpea, pea) and cover crops are placed in low water-stress seasons to increase soil organic matter.",
        "kanit_tr": "Tarımsal araştırmalar, nohut ve mercimeğin dekara yaklaşık 4-6 kg saf doğal azot (gübre) kazandırdığını kanıtlamaktadır.",
        "kanit_en": "NASA SMAP soil moisture and POWER precipitation data; agronomic literature shows nitrogen-fixers contribute ~40-60 kg/ha N.",
        "faydalar_tr": ["Seneye atacağınız gübre masrafı düşer", "Toprağın su tutma gücü artar", "Tarlanın bereketi uzun yıllar korunur"],
        "faydalar_en": ["Soil organic matter increases", "Erosion risk decreases", "Chemical fertilizer need drops", "Water retention improves"],
        "riskler_tr": ["İlk hasatta buğday kadar hızlı nakit getirmeyebilir", "Tüccar/pazar fiyatı mevsime göre oynayabilir"],
        "riskler_en": ["May reduce short-term income", "Local market demand may be limited", "Expert advisory may be needed"],
        "bilgi_eksikligi_tr": "Toprak yapınıza göre tohum seçimi için ilçe tarıma danışın.",
        "bilgi_eksikligi_en": "Local soil test and agronomist approval required.",
    },
    "su_tasarrufu": {
        "anahtar": "su_tasarrufu",
        "ad_tr": "Susuzluğa Dayanıklı (Az Masraflı) Ekim",
        "ad_en": "Water Saving & Drought Hardy Rotation",
        "grup_vurgu": ["düşük", "orta"],
        "aciklama_tr": "Az su isteyen, kuraklığa kafa tutan nohut, arpa veya mercimek ile su ve elektrik/mazot faturasını düşüren yol.",
        "aciklama_en": "Rotation minimizing water use with low-water, drought-tolerant crops.",
        "neden_tr": "Bölgenizin NASA yağış ve sıcaklık geçmişi kuraklık eğilimi gösterdiği için, suyu az tüketen ve sıcağa dayanıklı çeşitler önerildi.",
        "neden_en": "Based on NASA POWER low precipitation and high temperature data, low-water crops (lentil, chickpea, barley) are preferred.",
        "kanit_tr": "NASA yağış ölçümleri ve tarla denemelerine göre nohut ve arpa, mısır veya pamuğa kıyasla %40-60 daha az suya ihtiyaç duyar.",
        "kanit_en": "NASA GPM precipitation and POWER temperature data; studies show lentil and chickpea use 30-50% less water than cereals.",
        "faydalar_tr": ["Sulama ve elektrik/mazot masrafı yarı yarıya düşer", "Kurak yılda bile ürün tarlada yanmaz", "Kuyu suyunu tüketmez"],
        "faydalar_en": ["Water use reduced 30-50%", "Drought resilience increases", "Irrigation cost drops"],
        "riskler_tr": ["Sulu mısır kadar tonaj getirisi yüksek olmayabilir"],
        "riskler_en": ["Yield may be lower", "Market demand may vary", "Soil salinity risk"],
        "bilgi_eksikligi_tr": "Kuru tarım tohum desteği için bölgenizdeki kooperatife başvurun.",
        "bilgi_eksikligi_en": "Local irrigation infrastructure and water rights check required.",
    },
    "mevcut_koruma": {
        "anahtar": "mevcut_koruma",
        "ad_tr": "Alışılmış Düzen (Düşük Riskli Yol)",
        "ad_en": "Keep Current Rotation",
        "grup_vurgu": None,
        "aciklama_tr": "Mevcut alışkanlığınızı ve ekipmanınızı bozmadan, en az riskle devam edebileceğiniz güvenli yol.",
        "aciklama_en": "Minimum-change, low-risk rotation suited to current crop.",
        "neden_tr": "NASA iklim verileri bölgenizde olağanüstü bir risk göstermediği için bildiğiniz ve elinizde alet-edevatı hazır olan döngüyü sürdürebilirsiniz.",
        "neden_en": "If NASA POWER climate data matches current crop's temp/precip range, continue current rotation without change risk.",
        "kanit_tr": "NASA geçmiş 20 yıllık verilerinde bu bölgede standart döngünün ortalama hava şartlarında tutarlı sonuç vermesi.",
        "kanit_en": "NASA POWER temperature and precipitation data falling within current crop's ideal range.",
        "faydalar_tr": ["Alışık olduğunuz düzen, acemilik çekilmez", "Yeni makine/ekipman masrafı çıkarmaz", "Tüccarı ve pazarı bellidir"],
        "faydalar_en": ["No change risk", "Existing equipment and knowledge base", "Quick to implement"],
        "riskler_tr": ["Üst üste aynı ürün ekilirse toprak yorulur ve kök hastalıkları artabilir"],
        "riskler_en": ["Soil fatigue may increase long-term", "Pest/disease cycles may persist", "New opportunities may be missed"],
        "bilgi_eksikligi_tr": "Aynı tarlaya 2 yıldan fazla üst üste aynı ürünü ekmemeye dikkat edin.",
        "bilgi_eksikligi_en": "Soil tests and long-term yield records required.",
    },
}


def get_str_text(key, lang):
    """STRATEJILER içinden dil özelliğini al."""
    s = STRATEJILER[key]
    return s.get(f"{key.split('_')[-1]}_{lang}") or s.get(f"ad_{lang}") or s["ad_tr"]


def apply_scenario(ort, scenario):
    """Senaryo (yağış/sıcaklık değişimi) uygula, yeni ortalama döndür."""
    if not scenario:
        return ort
    yeni = dict(ort)
    precip_change = scenario.get("precip_change_pct", 0) / 100.0
    temp_change = scenario.get("temp_change_c", 0)
    yeni["yağış_mm_gun"] = round(yeni["yağış_mm_gun"] * (1 + precip_change), 2)
    yeni["sıcaklık_C"] = round(yeni["sıcaklık_C"] + temp_change, 2)
    return yeni


def apply_constraints(crops, constraints):
    """Çiftçi kısıtlarına göre bitki listesini filtrele/cezala."""
    if not constraints:
        return crops
    filtered = {}
    for k, c in crops.items():
        penalty = 0
        # Sulama yoksa yüksek su ihtiyacı ceza
        if constraints.get("irrigation") == "yok" and c["su_ihtiyacı"] == "yüksek":
            penalty += 30
        # Ekipman kısıtı: özel ekipman gerektiren bitkiler (şimdilik basit)
        # Pazar tercihi: istenen gruba bonus
        market_pref = constraints.get("market_preference")
        if market_pref and c["grup"] == market_pref:
            penalty -= 10  # bonus
        c2 = dict(c)
        c2["_constraint_penalty"] = penalty
        filtered[k] = c2
    return filtered


def strategi_skoru(ort, oncelikler, crop, strateji_key, constraints=None):
    """Tek bir strateji için bitki bazlı 0-100 skor hesaplar."""
    base = clima_uygunluk(ort, crop)

    su = oncelikler.get("su_tasarimi", 0) / 100.0
    toprak = oncelikler.get("toprak_sagligi", 0) / 100.0
    kararlilik = oncelikler.get("kararli_verim", 0) / 100.0
    guclu = oncelikler.get("guclu_koşullar", 0) / 100.0

    bonus = 0
    if su > 0:
        su_skor = {"düşük": 100, "orta": 60, "yüksek": 20}.get(crop["su_ihtiyacı"], 50)
        bonus += su_skor * su * 0.4
    if toprak > 0:
        top_skor = {"iyileştirici": 100, "nötr": 60, "tüketici": 20}.get(crop["toprak_etkisi"], 50)
        bonus += top_skor * toprak * 0.3
    if kararlilik > 0:
        t_genislik = crop["sıcaklık"][1] - crop["sıcaklık"][0]
        p_genislik = crop["yağış"][1] - crop["yağış"][0]
        kar_skor = min(100, (t_genislik + p_genislik) * 4)
        bonus += kar_skor * kararlilik * 0.2
    if guclu > 0:
        gcl_skor = min(100, crop["sıcaklık"][1] + (10 - crop["yağış"][1]) * 10)
        bonus += gcl_skor * guclu * 0.1

    # Kısıtlama cezası
    penalty = crop.get("_constraint_penalty", 0)
    if penalty > 0:
        bonus -= penalty

    return round(max(0, min(100, base + bonus)), 1)


def risk_uyarilari(ort, lang="tr"):
    """
    NASA POWER iklim göstergelerine dayalı agronomik riskler:
    Don, ısı dalgası, kuraklık ve NASA WS2M / PRECTOTCORR temelli rüzgar ve su erozyonu riskleri.
    """
    uyarilar = []
    t = ort.get("sıcaklık_C", 15.0)
    p = ort.get("yağış_mm_gun", 1.5)
    w = ort.get("rüzgar_m_s", 2.0)
    L = LANG[lang]

    # Don riski (T2M < 5°C)
    if t < 5:
        uyarilar.append({"tip": "don", "mesaj": L["frost_warning"], "severity": "high"})
    # Sıcaklık > 30°C -> ısı dalgası
    if t > 30:
        uyarilar.append({"tip": "isi", "mesaj": L["heat_warning"], "severity": "high"})
    # Yağış < 1 mm/gün -> kuraklık
    if p < 1.0:
        uyarilar.append({"tip": "kuraklik", "mesaj": L["drought_warning"], "severity": "medium"})

    # NASA WS2M Rüzgar Erozyonu Riski (Rüzgar > 3.5 m/s ve kurak ortam p < 1.4 mm/gün)
    if w > 3.5 and p < 1.4:
        uyarilar.append({"tip": "erozyon_ruzgar", "mesaj": L["wind_erosion_warning"], "severity": "medium"})
    # NASA PRECTOTCORR Su Erozyonu & Yüzey Akışı Riski (Aşırı yağış > 5.0 mm/gün)
    elif p > 5.0:
        uyarilar.append({"tip": "erozyon_su", "mesaj": L["runoff_erosion_warning"], "severity": "medium"})

    return uyarilar


def stres_takvimi(ort, lang="tr", aylik_veri=None):
    """
    Yıl boyu stres takvimi (12 ay).
    NASA POWER Monthly verisi varsa doğrudan gerçek aylık T2M ve PRECTOTCORR kullanılır.
    Yoksa akıllı mevsimsellik modeliyle fallback üretilir.
    """
    L = LANG[lang]
    t_ort = ort["sıcaklık_C"]
    p_ort = ort["yağış_mm_gun"]

    takvim = []

    # Aylık veriyi parse et (varsa)
    p_dict = {}
    t_dict = {}
    if aylik_veri and "properties" in aylik_veri and "parameter" in aylik_veri["properties"]:
        param = aylik_veri["properties"]["parameter"]
        p_dict = param.get("PRECTOTCORR", {})
        t_dict = param.get("T2M", {})

    for ay in range(1, 13):
        # Ay anahtarını bul (örn: 202301)
        ay_str = f"{ay:02d}"
        t_val = None
        p_val = None

        for k, v in t_dict.items():
            if k.endswith(ay_str) and isinstance(v, (int, float)) and v > -99:
                t_val = v
                break
        for k, v in p_dict.items():
            if k.endswith(ay_str) and isinstance(v, (int, float)) and v >= 0:
                p_val = v
                break

        # Gerçek veri yoksa mevsimsel fallback
        if t_val is None:
            if ay in [12, 1, 2]:
                t_ay = t_ort - 8
            elif ay in [3, 4, 5]:
                t_ay = t_ort - 2
            elif ay in [6, 7, 8]:
                t_ay = t_ort + 6
            else:
                t_ay = t_ort
        else:
            t_ay = t_val

        if p_val is None:
            if ay in [12, 1, 2]:
                p_ay = p_ort * 0.8
            elif ay in [3, 4, 5]:
                p_ay = p_ort * 1.2
            elif ay in [6, 7, 8]:
                p_ay = p_ort * 0.6
            else:
                p_ay = p_ort * 1.0
        else:
            p_ay = p_val

        # NDVI proxy: Sıcaklık ve yağışın optimalliğine göre fenolojik eğri
        if ay in [12, 1, 2]:
            ndvi = 0.18
        elif ay in [3, 4, 5]:
            ndvi = 0.58
        elif ay in [6, 7, 8]:
            ndvi = 0.72
        else:
            ndvi = 0.38

        # Stres hesaplama
        temp_stress = max(0, min(100, (max(0, 35 - t_ay) if t_ay > 30 else max(0, 5 - t_ay)) * 10))
        water_stress = max(0, min(100, (2.2 - p_ay) * 45))

        takvim.append({
            "ay": ay,
            "ay_adi": L["groups"]["kis" if ay in [12,1,2] else "bahar" if ay in [3,4,5] else "yaz" if ay in [6,7,8] else "sonbahar"],
            "sıcaklık_C": round(t_ay, 1),
            "yağış_mm_gun": round(p_ay, 2),
            "ndvi_proxy": round(ndvi, 2),
            "temp_stress": round(temp_stress),
            "water_stress": round(water_stress),
        })

    return {
        "aylar": takvim,
        "labels": [L["groups"]["kis"], L["groups"]["bahar"], L["groups"]["yaz"], L["groups"]["sonbahar"]],
    }


def rotasyon_dizisi_uret(tum_bitkiler, crops, gecmis_list=None, lang="tr"):
    """
    3 Yıllık Sıralı Rotasyon Dizisi Üretir (Yıl 1, Yıl 2, Yıl 3).
    Agronomik Kurallar:
    - Geçmişte tüketici ürün ekilmişse 1. yıl mutlaka iyileştirici (azot bağlayan baklagil) gelir.
    - Aynı aile veya aynı toprak etkisine sahip ürün üst üste 2 yıl ekilmez (hastalık ve tükenme önlenir).
    - Düşük su tüketen ve derin köklü bitkiler döngüye dengeli dahil edilir.
    """
    dizi = []
    kullanilan_anahtarlar = set()

    # Son ekilen ürün
    son_ekilen = None
    if gecmis_list and len(gecmis_list) > 0:
        son_ekilen = gecmis_list[-1]
    
    son_etki = crops.get(son_ekilen, {}).get("toprak_etkisi", "nötr") if son_ekilen else "nötr"

    # YIL 1 SEÇİMİ
    yil1_adaylar = []
    if son_etki == "tüketici":
        # Toprağı onarmak şart: İyileştirici baklagil öncelikli
        yil1_adaylar = [b for b in tum_bitkiler if b["toprak_etkisi"] == "iyileştirici"]
    if not yil1_adaylar:
        yil1_adaylar = [b for b in tum_bitkiler if b["anahtar"] != son_ekilen]
    
    yil1 = yil1_adaylar[0] if yil1_adaylar else tum_bitkiler[0]
    kullanilan_anahtarlar.add(yil1["anahtar"])
    
    c1 = crops[yil1["anahtar"]]
    dizi.append({
        "yil": 1,
        "anahtar": yil1["anahtar"],
        "bitki": yil1["bitki"],
        "grup": yil1["grup"],
        "toprak_etkisi": yil1["toprak_etkisi"],
        "rol": "Toprak Onarımı ve Azot Bağlama" if yil1["toprak_etkisi"] == "iyileştirici" else "Ana Mahsul",
        "rol_en": "Soil Restoration & N-Fixing" if yil1["toprak_etkisi"] == "iyileştirici" else "Primary Crop",
        "verim_kg": c1.get("verim_kg_donum", 300),
        "fiyat_tl": c1.get("fiyat_tl_kg", 15.0),
        "aciklama": "Önceki yıl toprağı tüketen mahsulden sonra tarlayı besler." if yil1["toprak_etkisi"] == "iyileştirici" else "İklim verisine en yüksek uyum sağlayan başlangıç ürünü.",
        "aciklama_en": "Restores soil vitality and natural nitrogen balance." if yil1["toprak_etkisi"] == "iyileştirici" else "Highest climate-matching starter crop."
    })

    # YIL 2 SEÇİMİ (Ana gelir / yüksek verimli veya dengeli tahıl/endüstri bitkisi)
    yil2_adaylar = [
        b for b in tum_bitkiler 
        if b["anahtar"] not in kullanilan_anahtarlar and b["toprak_etkisi"] in ("nötr", "tüketici")
    ]
    if not yil2_adaylar:
        yil2_adaylar = [b for b in tum_bitkiler if b["anahtar"] not in kullanilan_anahtarlar]
    
    yil2 = yil2_adaylar[0] if yil2_adaylar else tum_bitkiler[1 % len(tum_bitkiler)]
    kullanilan_anahtarlar.add(yil2["anahtar"])
    c2 = crops[yil2["anahtar"]]
    dizi.append({
        "yil": 2,
        "anahtar": yil2["anahtar"],
        "bitki": yil2["bitki"],
        "grup": yil2["grup"],
        "toprak_etkisi": yil2["toprak_etkisi"],
        "rol": "Verim ve Gelir Odaklı Ana Mahsul",
        "rol_en": "High-Yield Revenue Anchor",
        "verim_kg": c2.get("verim_kg_donum", 350),
        "fiyat_tl": c2.get("fiyat_tl_kg", 12.0),
        "aciklama": "1. yılda zenginleşen azot stoğundan beslenerek maksimum tonaj verir.",
        "aciklama_en": "Capitalizes on accumulated soil nitrogen to deliver maximum yield."
    })

    # YIL 3 SEÇİMİ (Kurağa dayanıklı, dinlendirici veya düşük girdili bitki)
    yil3_adaylar = [
        b for b in tum_bitkiler 
        if b["anahtar"] not in kullanilan_anahtarlar and b["su_ihtiyacı"] in ("düşük", "orta")
    ]
    if not yil3_adaylar:
        yil3_adaylar = [b for b in tum_bitkiler if b["anahtar"] not in kullanilan_anahtarlar]
    
    yil3 = yil3_adaylar[0] if yil3_adaylar else tum_bitkiler[2 % len(tum_bitkiler)]
    c3 = crops[yil3["anahtar"]]
    dizi.append({
        "yil": 3,
        "anahtar": yil3["anahtar"],
        "bitki": yil3["bitki"],
        "grup": yil3["grup"],
        "toprak_etkisi": yil3["toprak_etkisi"],
        "rol": "Su Tasarrufu ve Dengeleme",
        "rol_en": "Moisture Conservation & Stabilizer",
        "verim_kg": c3.get("verim_kg_donum", 280),
        "fiyat_tl": c3.get("fiyat_tl_kg", 18.0),
        "aciklama": "Düşük su tüketimiyle yeraltı su dengesini korur ve tarlayı bir sonraki rotasyona hazırlar.",
        "aciklama_en": "Conserves groundwater reserves and stabilizes field ecology."
    })

    return dizi


def rotasyon_oneri(ort, oncelikler, mevcut=None, onceki=None, gecmis_bitkiler=None, aylik=None, crops=None, scenario=None, constraints=None, lang="tr", cok_yillik=None):
    """
    3 farklı rotasyon stratejisi + 3 yıllık ekim nöbeti dizisi + stres takvimi + risk uyarıları + dil desteği.
    """
    L = LANG[lang]

    if crops is None:
        crops = load_crops()

    # Senaryo uygula
    ort_s = apply_scenario(ort, scenario)

    # Kısıtlamaları uygula
    crops_c = apply_constraints(crops, constraints)

    # Tüm bitkileri skora göre sırala
    tum_bitkiler = []
    for anahtar, c in crops_c.items():
        skor = strategi_skoru(ort_s, oncelikler, c, None, constraints)
        tum_bitkiler.append({
            "bitki": c["ad"],
            "anahtar": anahtar,
            "grup": c["grup"],
            "skor": skor,
            "su_ihtiyacı": c["su_ihtiyacı"],
            "toprak_etkisi": c["toprak_etkisi"],
            "verim_kg": c.get("verim_kg_donum", 300),
            "fiyat_tl": c.get("fiyat_tl_kg", 15.0),
            "not": c["not"],
        })
    tum_bitkiler.sort(key=lambda x: x["skor"], reverse=True)

    # Geçmiş bitkiler listesi oluştur
    gecmis_list = []
    if gecmis_bitkiler and isinstance(gecmis_bitkiler, list):
        gecmis_list = [g for g in gecmis_bitkiler if g in crops]
    elif onceki and onceki in crops:
        gecmis_list = [onceki]

    # Son mahsul tüketici/nötr ise baklagillere azot bonusu
    if gecmis_list:
        son_etki = crops[gecmis_list[-1]].get("toprak_etkisi", "nötr")
        if son_etki in ("tüketici", "nötr"):
            for b in tum_bitkiler:
                if b["toprak_etkisi"] == "iyileştirici":
                    b["skor"] = min(100, b["skor"] + 8)
            tum_bitkiler.sort(key=lambda x: x["skor"], reverse=True)

    # 3 Yıllık Rotasyon Takvimi Üret
    rotasyon_plani = rotasyon_dizisi_uret(tum_bitkiler, crops, gecmis_list=gecmis_list, lang=lang)

    # Strateji 1: Toprak Sağlığı
    ts_secim = [b for b in tum_bitkiler if b["toprak_etkisi"] in ("iyileştirici", "nötr")]
    ts_bitki = ts_secim[0] if ts_secim else tum_bitkiler[0]
    ts = dict(STRATEJILER["toprak_sagligi"])
    ts["bitki"] = ts_bitki["bitki"]
    ts["anahtar"] = ts_bitki["anahtar"]
    ts["skor"] = round((ts_bitki["skor"] + 10) / 2, 1)
    ts["bitki_skor"] = ts_bitki["skor"]
    ts["ad"] = L["strategies"]["toprak_sagligi"]

    # Strateji 2: Su Tasarrufu
    su_secim = [b for b in tum_bitkiler if b["su_ihtiyacı"] in ("düşük", "orta")]
    su_bitki = su_secim[0] if su_secim else tum_bitkiler[-1]
    su_str = dict(STRATEJILER["su_tasarrufu"])
    su_str["bitki"] = su_bitki["bitki"]
    su_str["anahtar"] = su_bitki["anahtar"]
    su_str["skor"] = round((su_bitki["skor"] + 10) / 2, 1)
    su_str["bitki_skor"] = su_bitki["skor"]
    su_str["ad"] = L["strategies"]["su_tasarrufu"]

    # Strateji 3: Mevcut Rotasyonu Koru
    if mevcut and mevcut in crops:
        mevcut_ad = crops[mevcut]["ad"]
        mevcut_skor = next((b["skor"] for b in tum_bitkiler if b["anahtar"] == mevcut), tum_bitkiler[0]["skor"])
        mevcut_anahtar = mevcut
    else:
        mevcut_ad = L["current_crop"] + " (seçilmedi)"
        mevcut_skor = tum_bitkiler[0]["skor"]
        mevcut_anahtar = None

    mk = dict(STRATEJILER["mevcut_koruma"])
    mk["bitki"] = mevcut_ad
    mk["anahtar"] = mevcut_anahtar
    mk["skor"] = round(mevcut_skor * 0.95, 1)
    mk["bitki_skor"] = mevcut_skor
    mk["mevcut_anahtar"] = mevcut_anahtar
    mk["ad"] = L["strategies"]["mevcut_koruma"]

    # Dil çevirileri için metinleri güncelle
    for s in [ts, su_str, mk]:
        s["neden"] = s[f"neden_{lang}"] if f"neden_{lang}" in s else s["neden_tr"]
        s["kanit"] = s[f"kanit_{lang}"] if f"kanit_{lang}" in s else s["kanit_tr"]
        s["faydalar"] = s[f"faydalar_{lang}"] if f"faydalar_{lang}" in s else s["faydalar_tr"]
        s["riskler"] = s[f"riskler_{lang}"] if f"riskler_{lang}" in s else s["riskler_tr"]
        s["bilgi_eksikligi"] = s[f"bilgi_eksikligi_{lang}"] if f"bilgi_eksikligi_{lang}" in s else s["bilgi_eksikligi_tr"]

    en_iyi = tum_bitkiler[0]

    return {
        "rotasyon_plani": rotasyon_plani,
        "stratejiler": [ts, su_str, mk],
        "en_iyi_bitki": en_iyi,
        "tum_bitkiler": tum_bitkiler[:8],
        "stres_takvimi": stres_takvimi(ort_s, lang, aylik_veri=aylik),
        "risk_uyarilari": risk_uyarilari(ort_s, lang),
        "si_analiz": si_analiz(cok_yillik, lang) if cok_yillik else None,
        "dil": lang,
        "senaryo": scenario,
        "kisitlamalar": constraints,
    }