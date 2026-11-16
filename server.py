#!/usr/bin/env python3
"""NASA Space Apps 2026 - SAGE (Satellite Agro-climatology & Growth Engine) sunucu.
HTTP: GET /, GET /static/*, POST /api/analiz, POST /api/rotasyon"""
import json
import os
import urllib.request
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import time
import math
from collections import defaultdict, deque
from logic.advisor import answer_chat, AdvisorError
from logic.crop_health import crop_health

POWER = "https://power.larc.nasa.gov/api/temporal/daily/point"
POWER_MONTHLY = "https://power.larc.nasa.gov/api/temporal/monthly/point"

BASE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(BASE, "static")

# Tiny stdlib .env reader: only allow known config keys; environment wins.
try:
    with open(os.path.join(BASE, '.env'), encoding='utf-8') as env_file:
        for line in env_file:
            name, sep, value = line.strip().partition('=')
            if sep and name in ('NVIDIA_API_KEY', 'NVIDIA_MODEL'):
                os.environ.setdefault(name, value.strip())
except FileNotFoundError:
    pass

CHAT_LOCK = threading.Lock()
CHAT_SLOTS = threading.BoundedSemaphore(2)
CHAT_LIMITS = defaultdict(deque)



def power_veri(lat, lon, start, end, params="T2M,PRECTOTCORR,ALLSKY_SFC_SW_DWN,WS2M,RH2M"):
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


def ortalama(veri_dict, minimum=0):
    vals = [v for v in veri_dict.values() if isinstance(v, (int, float)) and math.isfinite(v) and v >= minimum]
    return round(sum(vals) / len(vals), 2) if vals else 0


def analiz_et(veri):
    p = veri["properties"]["parameter"]
    ort = {
        "sıcaklık_C": ortalama(p.get("T2M", {}), minimum=-90),
        "yağış_mm_gun": ortalama(p.get("PRECTOTCORR", {})),
        "güneş_MJ_m2_gun": ortalama(p.get("ALLSKY_SFC_SW_DWN", {})),
        "rüzgar_m_s": ortalama(p.get("WS2M", {})),
        "nem_yuzde": ortalama(p.get("RH2M", {})),
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
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(b)

    def _json(self, data, code=200):
        self._send(json.dumps(data, ensure_ascii=False), code, "application/json")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Origin", "*")
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
        elif urllib.parse.urlsplit(self.path).path in ("/platform", "/platform/"):
            self._dosya(os.path.join(STATIC, "platform.html"), "text/html")
        elif self.path.startswith("/static/"):
            dosya = os.path.realpath(os.path.join(STATIC, urllib.parse.unquote(urllib.parse.urlsplit(self.path).path[len("/static/"):])))
            if not dosya.startswith(STATIC + os.sep):
                self._json({"error":"forbidden"}, 403)
                return
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
        # Cross-origin is allowed (github.io frontend <- vercel backend).
        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            self._json({'error':'invalid_length'}, 400)
            return
        if not 0 < length <= 250000:
            self._json({'error':'request_too_large'}, 413)
            return
        raw = self.rfile.read(length)
        try:
            body = json.loads(raw.decode("utf-8"))
        except Exception:
            self._json({"error": "geçersiz json"}, 400)
            return

        if not isinstance(body, dict):
            self._json({'error':'invalid_body'}, 400)
            return

        if self.path == '/api/chat':
            now = time.monotonic()
            with CHAT_LOCK:
                # Bound retained IP entries on a public preview server.
                if len(CHAT_LIMITS) > 2000:
                    CHAT_LIMITS.clear()
                calls = CHAT_LIMITS[self.client_address[0]]
                while calls and calls[0] < now - 60:
                    calls.popleft()
                limited = len(calls) >= 6
                if not limited:
                    calls.append(now)
            if limited or not CHAT_SLOTS.acquire(blocking=False):
                self._json({'error':'rate_limited'}, 429)
                return
            try:
                self._json(answer_chat(body))
            except AdvisorError as exc:
                self._json({'error':exc.code}, exc.status)
            except Exception:
                self._json({'error':'invalid_context'}, 400)
            finally:
                CHAT_SLOTS.release()
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
                self._json({"ortalama": ort, "raw": veri, "aylik": aylik, "cok_yillik": cok_yillik, "bitki_sagligi": crop_health(veri, body.get("crop", ""), body.get("lang", "tr"))})
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
                sonuc["bitki_sagligi"] = crop_health(body.get("health_raw"), mevcut or "", lang)
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
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()
