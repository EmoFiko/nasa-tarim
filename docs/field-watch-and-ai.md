# SAGE Field Watch and AI advisor

## What is implemented

- NASA POWER Daily queries now include `RH2M` (relative humidity at 2m).
- Field Watch screens the last **seven calendar days of the selected historical analysis period**, using temperature, relative humidity and precipitation on matching dates. At least four complete daily observations are required. Missing or fill values produce an insufficient-data state, not a low-risk assessment.
- Crop-specific cards cover cereal yellow rust for wheat/barley and late blight for potato/tomato, plus broad fungal conditions and an aphid scouting indicator. Cards show thresholds, matching-day counts, period and limitations.
- These are exploratory weather-suitability rules, **not validated infection models, probabilities, diagnosis, forecasts or real-time field alerts**. Daily relative humidity does not measure leaf wetness. There is no scheduled monitoring or SMS service.
- A contextual chat drawer connects server-side to NVIDIA NIM (`nvidia/nemotron-3.5-super-vl-120b-a12b`). It receives the last successfully analyzed field/date range, observed climate, monthly data, multi-year climate summary, crop history, priorities, scenario, constraints, full rotation/strategy results and Field Watch results. Raw daily series are summarized rather than duplicated in every prompt.
- Each send explains that the message, field location and analysis summary are sent to NVIDIA. Conversation stays in browser memory, is reset on a changed analysis, and is not persisted by SAGE. NVIDIA's own service/data policy still applies.
- The assistant explains uncertainty, distinguishes observed climate from scenario changes, and asks for field scouting/local agronomic review. It is instructed against disease diagnosis, pesticide prescriptions and irrigation quantities without sufficient measurements.

## Rule definitions (prototype, not locally calibrated)

| Screening card | Daily conditions | Trigger in 7 calendar days |
| --- | --- | --- |
| General fungal conditions | 10–28 °C, RH ≥85%, rain ≥1 mm/day | 2 matching days |
| Cereal yellow rust | 7–15 °C, RH ≥85%, rain ≥0.5 mm/day | 2 matching days |
| Potato/tomato late blight | 10–25 °C, RH ≥90%, rain ≥0.5 mm/day | 2 matching days |
| Aphid scouting | 15–28 °C, RH <75%, rain <1 mm/day | 3 matching days |

The numeric rules are SAGE prototype screening choices. They are **not** Smith periods, a validated regional forecast, or a field trial result. Wetness duration, cultivar susceptibility, pathogen presence, phenology and scouting need to be added and validated before operational disease forecasting. The no-match state explicitly says it does not imply absence of risk. Scenarios do not alter these observational cards.

Data documentation: https://power.larc.nasa.gov/docs/services/api/temporal/daily/

## Local configuration

Copy `.env.example` to `.env` and set `NVIDIA_API_KEY`. The stdlib server reads only the known NVIDIA configuration keys; existing environment variables take priority. `.env` is ignored by Git. Deployments must supply their own environment secret. No key belongs in JavaScript, HTML or Git.

Run `python3 server.py`, then open `/platform`. The model can be overridden by `NVIDIA_MODEL`. `POST /api/chat` accepts `message`, `history`, `context`, and `lang`. Provider calls have a 75-second timeout, 2 simultaneous request slots and an in-memory per-IP limit of 6 attempts/minute. This is appropriate for a local demo; an unrestricted public production deployment would need authenticated usage and shared quotas. Static-file paths are confined to `static/`, body sizes are bounded and cross-origin POSTs are rejected.

Provider failures return readable error codes without provider response bodies or credentials. Failed questions remain editable for retry. All chat output renders as text rather than HTML.

## Deliberately not claimed

SMAP, real-time root-zone moisture sensing, precise automatic irrigation, carbon-credit verification, regenerative certification, buyer matching, SMS and offline operation are not implemented. SMAP is a coarse satellite/reanalysis product, not millimeter-level field sensing. Certification needs measured baselines, verification and an accredited scheme; it cannot be generated from a rotation suggestion.

## Verification

`python3 -m unittest discover -s tests -v`

Browser checks cover TR/EN, theme changes, narrow viewports, context transfer, conversation reset, failure/retry and actual model responses. The demonstration uses a cached, genuine NASA POWER response for Konya, 1–31 May 2024; dates remain visible and historical. Chat in the recording is a live NVIDIA response. No synthetic weather is presented as current observations.
