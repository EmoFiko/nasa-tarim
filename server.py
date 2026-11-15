#!/usr/bin/env python3
"""NASA Space Apps 2026 - Field Shift proje sunucu.
HTTP: GET /, GET /static/*, POST /api/analiz, POST /api/rotasyon"""
import json
import os
import urllib.request
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

POWER = "https://power.larc.nasa.gov/api/temporal/daily/point"
POWER_MONTHLY = "https://power.larc.nasa.gov/api/temporal/monthly/point"

BASE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(BASE, "static")


def power_veri(lat, lon, start, end, params="T2M,PRECTOTCORR,ALLSKY_SFC_SW_DWN,WS2M"):
    qs = urllib.parse.urlencode({
        "parameters": params,
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": start,
        "end": end,
        "format": "JSON",
    })
    url = f"{POWER}?{qs}"
    # Retry logic: 3 deneme, exponential backoff
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as ex:
            if attempt == 2:
                raise Exception(f"NASA POWER API hatası (3 deneme sonrası): {ex}")
            import time
            time.sleep(2 ** attempt)  # 1s, 2s
    return None


def power_aylik(lat, lon, year="2023", params="T2M,PRECTOTCORR"):
    """NASA POWER Monthly point endpoint - 12 aylık gerçek veriyi çeker."""
    qs = urllib.parse.urlencode({
        "parameters": params,
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": year,
        "end": year,
        "format": "JSON",
    })
    url = f"{POWER_MONTHLY}?{qs}"
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def power_cok_yillik(lat, lon, bitis_yili=2023, yil_sayisi=5, params="T2M,PRECTOTCORR"):
    """
    SI Trend Analizi için son N yılın yıllık ortalama değerlerini çeker.
    NASA POWER Monthly API kullanılır, tek çağrıda tüm aralık sorgulanır.
    Döndürür: {'yillar': [...], 'sicaklik': [...], 'yagis': [...]}
    """
    baslangic_yili = bitis_yili - yil_sayisi + 1
    qs = urllib.parse.urlencode({
        "parameters": params,
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": str(baslangic_yili),
        "end": str(bitis_yili),
        "format": "JSON",
    })
    url = f"{POWER_MONTHLY}?{qs}"
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            veri = json.loads(r.read().decode("utf-8"))
        if not veri or "properties" not in veri or "parameter" not in veri["properties"]:
            return None
        p = veri["properties"]["parameter"]
        t2m_dict = p.get("T2M", {})
        prec_dict = p.get("PRECTOTCORR", {})

        gecerli_yillar = []
        sicaklik_listesi = []
        yagis_listesi = []

        for y in range(baslangic_yili, bitis_yili + 1):
            ann_key = f"{y}13"
            t_val = t2m_dict.get(ann_key)
            p_val = prec_dict.get(ann_key)
            if t_val is not None and p_val is not None and t_val > -90 and p_val >= 0:
                gecerli_yillar.append(y)
                sicaklik_listesi.append(round(float(t_val), 2))
                yagis_listesi.append(round(float(p_val), 3))

        if len(sicaklik_listesi) < 2:
            return None

        return {
            "yillar": gecerli_yillar,
            "sicaklik": sicaklik_listesi,
            "yagis": yagis_listesi,
        }
    except Exception as ex:
        print(f"power_cok_yillik hata: {ex}")
        return None


def ortalama(veri_dict):
    vals = [v for v in veri_dict.values() if isinstance(v, (int, float)) and v >= 0]
    return round(sum(vals) / len(vals), 2) if vals else 0


def analiz_et(veri):
    p = veri["properties"]["parameter"]
    ort = {
        "sıcaklık_C": ortalama(p.get("T2M", {})),
        "yağış_mm_gun": ortalama(p.get("PRECTOTCORR", {})),
        "güneş_MJ_m2_gun": ortalama(p.get("ALLSKY_SFC_SW_DWN", {})),
        "rüzgar_m_s": ortalama(p.get("WS2M", {})),
    }
    return ort


class Handler(BaseHTTPRequestHandler):
    def _send(self, body, code=200, content_type="application/json"):
        if isinstance(body, str):
            b = body.encode("utf-8")
        else:
            b = body
        self.send_response(code)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(b)

    def _json(self, data, code=200):
        self._send(json.dumps(data, ensure_ascii=False), code, "application/json")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _dosya(self, path, content_type):
        try:
            with open(path, "rb") as f:
                self._send(f.read(), 200, content_type)
        except FileNotFoundError:
            self._json({"error": "dosya bulunamadı"}, 404)

    def do_GET(self):
        if self.path == "/":
            self._dosya(os.path.join(STATIC, "index.html"), "text/html")
        elif self.path.startswith("/static/"):
            dosya = os.path.join(STATIC, self.path[len("/static/"):])
            ct = "text/css" if dosya.endswith(".css") else "application/javascript" if dosya.endswith(".js") else "text/plain"
            self._dosya(dosya, ct)
        elif self.path == "/api/bitkiler":
            import sys
            sys.path.insert(0, BASE)
            from logic.rotation import load_crops
            self._json(load_crops())
        else:
            self._json({"error": "bulunamadı"}, 404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        try:
            body = json.loads(raw.decode("utf-8"))
        except Exception:
            self._json({"error": "geçersiz json"}, 400)
            return

        if self.path == "/api/analiz":
            try:
                lat = body["lat"]; lon = body["lon"]; start = body["start"]; end = body["end"]
                veri = power_veri(lat, lon, start, end)
                ort = analiz_et(veri)
                # 12 aylık gerçek NASA verisi al
                yil = start[:4] if len(str(start)) >= 4 else "2023"
                aylik = power_aylik(lat, lon, year=yil)
                # SI: Son 5 yıllık trend verisi (paralel değil, arka planda hafif çekiliyor)
                bitis_yili = int(yil) if yil.isdigit() else 2023
                # 2026 ise 2023'e cap (henüz POWER'da mevcut olmayabilir)
                bitis_yili = min(bitis_yili, 2023)
                cok_yillik = power_cok_yillik(lat, lon, bitis_yili=bitis_yili, yil_sayisi=5)
                self._json({"ortalama": ort, "raw": veri, "aylik": aylik, "cok_yillik": cok_yillik})
            except Exception as ex:
                self._json({"error": str(ex)}, 500)

        elif self.path == "/api/rotasyon":
            try:
                import sys
                sys.path.insert(0, BASE)
                from logic.rotation import rotasyon_oneri
                ort = body["ortalama"]
                oncelikler = body.get("oncelikler", {})
                mevcut = body.get("mevcut")
                onceki = body.get("onceki")
                gecmis_bitkiler = body.get("gecmis_bitkiler", [])
                aylik = body.get("aylik")
                cok_yillik = body.get("cok_yillik")
                scenario = body.get("scenario")
                constraints = body.get("constraints")
                lang = body.get("lang", "en")
                sonuc = rotasyon_oneri(
                    ort, oncelikler, mevcut, onceki=onceki,
                    gecmis_bitkiler=gecmis_bitkiler, aylik=aylik,
                    scenario=scenario, constraints=constraints, lang=lang,
                    cok_yillik=cok_yillik
                )
                self._json(sonuc)
            except Exception as ex:
                self._json({"error": str(ex)}, 500)
        else:
            self._json({"error": "bulunamadı"}, 404)


if __name__ == "__main__":
    import os, socket
    port = int(os.environ.get("PORT", 5000))
    # Try port with SO_REUSEADDR
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(("0.0.0.0", port))
        s.close()
    except OSError:
        port = 5001
    print(f"Sunucu başlatılıyor: http://localhost:{port}")
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()
