# Data Sources — Multi-source persistence

Usar **varias fuentes en cadena** mejora la persistencia del scraper: si Equibase bloquea o una API cae, la siguiente cubre entries/results.

Configuración (`.env`):

```env
# Failover chain (orden = prioridad)
SCRAPER_SOURCE=equibase,racing_api,demo
```

El servicio intenta cada fuente hasta obtener carreras; si todas fallan, cae a `demo`.

---

## Fuentes recomendadas

### 1. Equibase (HTML público) — ya integrado

| | |
|---|---|
| **Tipo** | Scrape HTML |
| **Cobertura** | USA + Canadá thoroughbred |
| **Datos** | Entries, charts, WPS, exotics, distancia, surface |
| **Código** | `scraper/clients/equibase.py` |
| **Riesgo** | Alto: Imperva/bot challenge |

URLs típicas:

```
Entries:  https://www.equibase.com/static/entry/{TRACK}{MMDDYY}USA-EQB.html
Results:  https://www.equibase.com/static/chart/summary/{TRACK}{MMDDYY}USA-EQB.html
Chart:    https://www.equibase.com/premium/chartEmb.cfm?track=GP&raceDate=MM/DD/YYYY&cy=USA&rn=1
```

---

### 2. The Racing API (North America) — ya integrado

| | |
|---|---|
| **Tipo** | API REST licenciada |
| **Docs** | https://api.theracingapi.com/documentation |
| **Cobertura** | USA/CAN con add-on North America (~£49.99/mo) |
| **Datos** | Meets, entries, results |
| **Código** | `scraper/clients/racing_api.py` |
| **Env** | `RACING_API_USERNAME`, `RACING_API_PASSWORD` |

Endpoints útiles:

```
GET /v1/north-america/meets?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
GET /v1/north-america/meets/{meet_id}/entries
GET /v1/north-america/meets/{meet_id}/results
GET /v1/results/today/free   # free tier limitado (no USA completo)
```

---

### 3. Goalserve Horse Racing Feed — recomendada como 2ª/3ª API

| | |
|---|---|
| **Tipo** | API comercial XML/JSON |
| **Docs** | https://www.goalserve.com/en/sport-data-feeds/horse-racing-api/description |
| **Cobertura** | UK, **USA**, FR, ZA, SE |
| **Datos** | Entries, results, odds, form/history |
| **Env** | `GOALSERVE_API_KEY`, `GOALSERVE_BASE_URL` |
| **Estado en repo** | Config lista; cliente pendiente |

Buen candidato a implementar en `scraper/clients/goalserve.py` para failover sin scrape HTML.

---

### 4. Horse Racing Nation (HRN) — scrape / Apify

| | |
|---|---|
| **Tipo** | HTML / scrapers Apify |
| **Site** | https://www.horseracingnation.com |
| **Datos** | Entries, results, stakes tracker, picks |
| **Pros** | Buena cobertura USA, menos “oficial” que Equibase |
| **Contras** | HTML frágil; ToS / rate limits |

Útil como fuente de **entries + post times** cuando Equibase falla.

---

### 5. Apify Equibase Actor — proxy anti-bot

| | |
|---|---|
| **Tipo** | SaaS scraper |
| **Actor** | `jungle_synthesizer/equibase-us-horse-racing-scraper` |
| **Datos** | Entries + results + payouts JSON |
| **Pros** | Resuelve Imperva por ti |
| **Contras** | Costo por run; dependencia externa |

Ejemplo:

```http
POST https://api.apify.com/v2/acts/jungle_synthesizer~equibase-us-horse-racing-scraper/run-sync-get-dataset-items
{
  "raceDate": "2026-08-02",
  "trackCodes": ["GP", "CD", "SAR"],
  "dataMode": "both",
  "maxItems": 500
}
```

---

### 6. Parse.bot Equibase / BloodHorse wrappers

| | |
|---|---|
| **Tipo** | API wrapper sobre scrape |
| **Equibase** | https://parse.bot/marketplace (equibase-com-api) |
| **BloodHorse** | race results list + detail |
| **Free tier** | ~100 req/mes |
| **Uso** | Backup ligero / prototipo |

Endpoints típicos wrapper Equibase:

- `get_track_entries(date, track)`
- `get_race_results(date, track, race_num)`
- `get_horse_profile(refNo)`

---

### 7. Sitios oficiales de tracks (replay + post times)

Fuentes complementarias por hipódromo (buenas para **video replay** y horarios):

| Track | Site | Uso |
|---|---|---|
| Gulfstream | https://www.gulfstreampark.com | Post times, replays |
| Churchill Downs | https://www.churchilldowns.com | Cards / twilight schedules |
| NYRA (SAR/AQU/BEL) | https://www.nyra.com | Entries, replays, first post |
| Santa Anita | https://www.santaanita.com | Cards CA |
| Del Mar | https://www.dmtc.com/racing/results/{date} | Results + replays |
| TwinSpires / Brisnet | https://www.twinspires.com | Results UI (cuenta wagering) |

No son un feed unificado, pero sirven para enriquecer `video_replay_url` y validar post times.

---

### 8. TrackMaster / Equibase Chart Downloads (licencia)

| | |
|---|---|
| **Tipo** | CSV/XML charts licenciados |
| **Datos** | Charts oficiales machine-readable (~45 días) |
| **Uso** | Producción seria / histórico |
| **Nota** | Equibase no ofrece API pública partner-free |

---

### 9. Demo (offline) — ya integrado

| | |
|---|---|
| **Código** | `scraper/demo_data.py` |
| **Uso** | UI/dev sin red; último eslabón del failover |
| **Comando** | `python manage.py seed_demo --tracks GP,CD,SAR` |

---

## Cadena recomendada por entorno

| Entorno | `SCRAPER_SOURCE` |
|---|---|
| Desarrollo local | `demo` |
| Staging | `equibase,demo` |
| Producción low-cost | `equibase,racing_api,demo` |
| Producción robusta | `racing_api,goalserve,equibase,demo` |
| Producción anti-bot | `apify_equibase,racing_api,demo` *(Apify client TBD)* |

---

## Qué fuente cubre qué campo de la app

| Campo app | Equibase | Racing API | Goalserve | HRN | Track sites | Demo |
|---|---|---|---|---|---|---|
| Track / date | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Distance / surface | ✅ | ✅ | ✅ | ✅ | parcial | ✅ |
| Post time | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Runners / ML odds | ✅ | ✅ | ✅ | ✅ | parcial | ✅ |
| Finish 1-2-3 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| W/P/S + EXA/TRI | ✅ | ✅ | ✅ | parcial | parcial | ✅ |
| Video replay | link chart | — | — | parcial | ✅ | fake URL |
| VIP picks | — (propios) | — | — | — | — | ✅ seed |

Los **VIP picks** (Mañana / Última Hora) son contenido de producto, no de Equibase.

---

## Próximos clientes a implementar

Orden sugerido para maximizar persistencia:

1. `scraper/clients/goalserve.py` — API estable USA
2. `scraper/clients/apify_equibase.py` — bypass Imperva
3. `scraper/clients/hrn.py` — backup entries/results HTML
4. Enricher de replays desde NYRA / Gulfstream / Del Mar

Comandos actuales:

```powershell
python manage.py scrape_entries --tracks GP,CD --source equibase,racing_api,demo
python manage.py scrape_results --tracks GP --source racing_api,demo
python manage.py scrape_live --source equibase,demo
python manage.py scrape_near_post --tracks GP   # odds @ 5 MTP + emits
```

## Eventos emitidos por el scraper

Tras upsert / near-post, `integrations.dispatcher.emit` dispara:

| Evento | Trigger |
|---|---|
| `race.next` | Cambio de carrera NEXT |
| `race.official` | Finishers + payouts nuevos |
| `replay.ready` | `video_replay_url` asignada/enriquecida |
| `picks.mtp5_published` | VipPick window `mtp5` |
| `odds.moved` | Delta morning → 5 MTP en selecciones VIP |

Telegram VIP channel y webhooks outbound consumen el mismo bus.
