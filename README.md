# American Horse Racing VIP Picker — Django API + Scraper

Backend Django + DRF que alimenta la app **NANO BANANA 2 / American Horse Racing VIP Picker** con:

- Hipódromos y calendarios (entries / post times)
- Resultados oficiales (llegada 1-2-3)
- Dividendos (W/P/S, Exacta, Trifecta…)
- Tablero VIP (Mañana vs Última Hora)
- Consulta en **JSON** vía API REST

## Stack

- Django 6 + Django REST Framework
- BeautifulSoup / requests (Equibase HTML)
- Cliente opcional para [The Racing API](https://api.theracingapi.com/documentation) (add-on North America)
- `django-crontab` para jobs programados
- Modo `demo` para desarrollar sin depender de scraping en vivo

## Arranque rápido

```powershell
cd "C:\Users\acade\OneDrive\Documentos\american horse racing vip picker"
.\.venv\Scripts\Activate.ps1
copy .env.example .env
python manage.py migrate
python manage.py sync_tracks
python manage.py seed_demo --tracks GP,CD,SAR
python manage.py runserver
```

API base: `http://127.0.0.1:8000/api/`

### Panel de administración (español)

UI gráfica con **django-jazzmin** en español: `http://127.0.0.1:8000/admin/`

- Login: usuario `jhon` (superusuario local)
- Menú agrupado: Carreras, Integraciones, Referidos, Usuarios
- Dashboard con resumen (carreras hoy, scrapes, referidos, webhooks)

### Exponer en internet (prueba gratuita)

Con el `runserver` en marcha, un túnel Cloudflare (sin cuenta) publica la app:

```powershell
cloudflared tunnel --url http://127.0.0.1:8000
```

Copia la URL `https://….trycloudflare.com` que imprime el túnel y ponla en `.env`:

```env
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,.trycloudflare.com,TU-HOST.trycloudflare.com
CSRF_TRUSTED_ORIGINS=https://TU-HOST.trycloudflare.com
```

Reinicia `runserver`. Alternativa: [ngrok](https://ngrok.com) (`ngrok http 8000`) con hosts `.ngrok-free.app`.

### App Android (Expo)

Cliente móvil en [`mobile/`](mobile/) (React Native / Expo + TypeScript).

```powershell
cd mobile
npm install
npm start
# luego 'a' (Android) o 'w' (web)
```

Configura la URL del API en **Más → Ajustes** (`http://10.0.2.2:8000/api` en emulador). Detalle: [mobile/README.md](mobile/README.md).

Documentación completa:

- [docs/GUIA_DE_USO.md](docs/GUIA_DE_USO.md) — guía de uso (admin, picks, scraping, API, referidos)
- [docs/API_ENDPOINTS.md](docs/API_ENDPOINTS.md) — todos los endpoints JSON (racing, our-picks, referidos, webhooks)
- [docs/API_EXAMPLES.md](docs/API_EXAMPLES.md) — ejemplos de petición y respuesta por endpoint
- [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) — fuentes externas, failover y eventos del scraper

### Features de plataforma

| Área | Cómo usarlo |
|---|---|
| Webhooks outbound | `POST /api/integrations/webhooks/` + header `X-Admin-Token` |
| Telegram VIP | `TELEGRAM_ENABLED=true` + bot token + chat id |
| Near-post / 5 MTP | `python manage.py scrape_near_post` (cron `*/2`) |
| Referidos | `GET /api/referrals/me/?device_id=` · `POST /api/referrals/claim/` |
| Our Picks + odds | `GET /api/our-picks/?track=GP` |

## Endpoints JSON (alineados a la app)

| Endpoint | Uso en la app |
|---|---|
| `GET /api/health/` | Healthcheck |
| `GET /api/tracks/` | Select Track |
| `GET /api/schedule/today/?track=GP` | Lista de carreras del día |
| `GET /api/races/?race_day__track__code=GP&race_day__race_date=2026-08-02` | Filtro de carreras |
| `GET /api/races/{id}/` | Detalle: runners, result, payouts, VIP picks |
| `GET /api/vip-board/?track=GP` | Tabla Mañana vs Última Hora |
| `GET /api/results/?track=GP` | Llegada + Dividendos + replay |
| `GET /api/race-days/?track__code=GP&race_date=2026-08-02` | Card completa del meet |

Ejemplo de respuesta de resultados:

```json
{
  "date": "2026-08-02",
  "track": "GP",
  "results": [
    {
      "track_code": "GP",
      "race_number": 6,
      "distance": "1 1/16M T",
      "status": "official",
      "top_three": [
        {"position": 1, "program_number": "9"},
        {"position": 2, "program_number": "2"},
        {"position": 3, "program_number": "7"}
      ],
      "dividends": {
        "W": {"amount": 8.4, "combination": "9"},
        "P": {"amount": 4.2, "combination": "9"},
        "S": {"amount": 3.0, "combination": "9"},
        "EXA": {"amount": 42.6, "combination": "9-2"},
        "TRI": {"amount": 158.8, "combination": "9-2-7"}
      },
      "video_replay_url": "https://example.com/replay/GP/.../R6"
    }
  ]
}
```

## Fuentes de datos

| Source (`SCRAPER_SOURCE`) | Descripción |
|---|---|
| `equibase` | HTML público de Equibase (entries + summary charts). Puede bloquear bots (Imperva). |
| `racing_api` | API licenciada (The Racing API + add-on North America ~£49.99/mo). |
| `demo` | Datos sintéticos deterministas para desarrollo / UI. |

Fallback automático: si Equibase bloquea y no hay credenciales de Racing API → usa `demo` para no romper el pipeline.

### Hipódromos principales (cobertura VIP)

Gulfstream (GP), Churchill Downs (CD), Saratoga (SAR), Belmont/Aqueduct (BAQ/AQU/BEL), Santa Anita (SA), Del Mar (DMR), Keeneland (KEE), Oaklawn (OP), Pimlico/Laurel (PIM/LRL), Indianapolis (IND), Ellis (ELP), Fair Grounds (FG), Tampa (TAM), Turfway (TP), Woodbine (WO), Parx (PRX), Monmouth (MTH).

### Ventanas típicas de post (ET)

- Este (GP, CD, NYRA): primer post ~12:30–13:10
- Oeste (SA, DMR): tarde ET (tarde local PT)
- Intervalo entre carreras: ~25–35 min
- Charts oficiales Equibase: ~40 min después de official

## Comandos del scraper

```powershell
python manage.py sync_tracks
python manage.py scrape_entries --date 2026-08-02 --tracks GP,CD
python manage.py scrape_results --date 2026-08-02 --tracks GP
python manage.py scrape_live --tracks GP,CD,SAR
python manage.py seed_demo --tracks GP --days 2

# Forzar fuente
python manage.py scrape_results --source demo --tracks GP
python manage.py scrape_results --source equibase --tracks GP
```

## Plan de cron (America/New_York)

Definido en `config/settings.py` → `CRONJOBS`:

| Horario ET | Job | Objetivo |
|---|---|---|
| `06:15` diario | `scrape_entries_job` | Entries de hoy y mañana |
| `10:00` diario | `scrape_entries_job` | Scratches / cambios de programa |
| `*/5 11:00–23:55` | `scrape_live_job` | Resultados + status NEXT (countdown) |
| `23:30` diario | `scrape_results_job` | Catch-up de charts del día |
| `01:00` domingo | `sync_tracks_job` | Catálogo de tracks |

### Instalar cron (Linux / WSL / servidor)

```bash
python manage.py crontab add
python manage.py crontab show
```

> En Windows nativo usa **Task Scheduler** llamando a los management commands, o corre los jobs en WSL.

### Task Scheduler (Windows) — ejemplo

```powershell
# Cada 5 minutos en horario de carrera
schtasks /Create /SC MINUTE /MO 5 /TN "AHR_LiveScrape" /TR "C:\path\to\.venv\Scripts\python.exe C:\path\to\manage.py scrape_live"
```

## Notas legales / producción

- Equibase y BloodHorse aplican protección anti-bot; el scraping agresivo viola ToS.
- Para producción comercial, usa datos licenciados (Equibase/TrackMaster o The Racing API NA).
- Respeta delays (`SCRAPER_REQUEST_DELAY_SECONDS`) y no dispares scrapes masivos.
- Los VIP picks de la app (Mañana / Última Hora) son **contenido propio**; el scraper solo trae entries/results — el seeding demo genera picks de ejemplo.

## Estructura

```
config/          # settings, urls
racing/          # models, serializers, API views
scraper/
  clients/       # equibase + racing_api
  management/    # scrape_* / seed_demo / sync_tracks
  cron.py        # entrypoints django-crontab
  services.py    # orquestación + upsert
  demo_data.py   # fallback offline
```
