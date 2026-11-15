"""Exploratory weather suitability rules, not a validated disease forecast.
Daily RH2M is not leaf wetness; field scouting is required.
"""
from datetime import datetime, date
import math


def valid(value, low, high):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and low <= value <= high


def crop_health(raw, crop='', lang='tr'):
    en = lang == 'en'
    param = (raw or {}).get('properties', {}).get('parameter', {})
    temps, humidity, rain = (param.get(k, {}) for k in ('T2M', 'RH2M', 'PRECTOTCORR'))
    dates = []
    for key in sorted(temps):
        try:
            day = datetime.strptime(key, '%Y%m%d').date()
        except (ValueError, TypeError):
            continue
        dates.append((key, day))
    # Only the last seven calendar days, never seven scattered observations.
    latest = dates[-1][1] if dates else None
    window = [(key, day) for key, day in dates if latest and 0 <= (latest - day).days < 7]
    rows = [(day, temps[key], humidity.get(key), rain.get(key)) for key, day in window
            if valid(temps[key], -60, 60) and valid(humidity.get(key), 0, 100) and valid(rain.get(key), 0, 1000)]
    rules = [
        ('fungal', 'Fungal disease conditions', 'Mantar hastalıklarına elverişli koşullar',
         lambda t,h,p: 10 <= t <= 28 and h >= 85 and p >= 1, 2,
         'T 10–28 °C · RH ≥85% · rain ≥1 mm/day',
         'Inspect leaves and canopy; avoid prolonged leaf wetness.', 'Yaprakları ve bitki örtüsünü kontrol edin; uzun süreli yaprak ıslaklığını azaltın.')]
    normalized = crop.casefold()
    if normalized in ('buğday', 'bugday', 'arpa'):
        rules.append(('rust', 'Cereal yellow rust conditions', 'Tahıllarda sarı pasa elverişli koşullar',
            lambda t,h,p: 7 <= t <= 15 and h >= 85 and p >= .5, 2,
            'T 7–15 °C · RH ≥85% · rain ≥0.5 mm/day',
            'Scout for yellow stripe-like pustules; consult a local agronomist.', 'Yapraklarda sarı çizgili püstülleri kontrol edin; yerel ziraat mühendisine danışın.'))
    if normalized in ('patates', 'domates'):
        rules.append(('blight', 'Late blight conditions', 'Geç yanıklığa elverişli koşullar',
            lambda t,h,p: 10 <= t <= 25 and h >= 90 and p >= .5, 2,
            'T 10–25 °C · RH ≥90% · rain ≥0.5 mm/day',
            'Inspect leaf undersides and lesions; seek local diagnosis.', 'Yaprak altlarını ve lekeleri kontrol edin; yerel teşhis desteği alın.'))
    rules.append(('aphids', 'Aphid monitoring conditions', 'Yaprak biti gözlem koşulları',
        lambda t,h,p: 15 <= t <= 28 and h < 75 and p < 1, 3,
        'T 15–28 °C · RH <75% · rain <1 mm/day',
        'Check new shoots and leaf undersides; weather alone cannot confirm pests.', 'Taze sürgünleri ve yaprak altlarını kontrol edin; hava koşulları tek başına zararlıyı doğrulamaz.'))
    cards = []
    for key, title_en, title_tr, match, threshold, criteria, action_en, action_tr in rules:
        hits = sum(match(t,h,p) for _,t,h,p in rows)
        status = 'insufficient' if len(rows) < 4 else 'favorable' if hits >= threshold else 'watch' if hits else 'low'
        cards.append(dict(id=key, title=title_en if en else title_tr, status=status,
                          matching_days=hits, valid_days=len(rows), trigger_days=threshold,
                          criteria=criteria, action=action_en if en else action_tr))
    return dict(crop=crop, latest_date=latest.isoformat() if latest else None,
                start_date=window[0][1].isoformat() if window else None,
                age_days=(date.today()-latest).days if latest else None,
                valid_days=len(rows), window_days=7, cards=cards,
                method='SAGE exploratory daily weather screening v1; unvalidated thresholds, not infection probabilities',
                source='NASA POWER Daily: T2M, RH2M, PRECTOTCORR',
                limitation=('Daily grid estimates are not field sensors, leaf wetness, diagnosis or a forecast. Crop stage, variety and scouting are not included. No automatic pesticide recommendation.' if en else
                'Günlük ızgara tahminleri tarla sensörü, yaprak ıslaklığı, teşhis veya hava tahmini değildir. Çeşit, gelişim evresi ve saha gözlemi hesaba katılmaz. Otomatik ilaç önerilmez.'))
