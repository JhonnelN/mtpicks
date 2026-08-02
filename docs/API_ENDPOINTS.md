# API Endpoints — American Horse Racing VIP Picker

Base URL (local): `http://127.0.0.1:8000/api/`

Formato de respuesta: **JSON**  
Paginación (listados DRF): `{ "count", "next", "previous", "results": [...] }`  
Timezone del servidor: `America/New_York`

---

## Mapa rápido (pantallas de la app)

| Pantalla app | Endpoint |
|---|---|
| Health / ping | `GET /api/health/` |
| Select Track | `GET /api/tracks/` |
| Lista de carreras del día | `GET /api/schedule/today/?track=GP` |
| VIP Picks (Mañana vs 5 MTP) | `GET /api/vip-board/?track=GP` |
| Our Picks + Odds Movement | `GET /api/our-picks/?track=GP` |
| Resultados (Llegada + Dividendos) | `GET /api/results/?track=GP` |
| Detalle de carrera | `GET /api/races/{id}/` |
| Odds movement por carrera | `GET /api/races/{id}/odds-movement/` |
| Referidos / share | `GET /api/referrals/me/?device_id=` |
| Claim código referido | `POST /api/referrals/claim/` |
| Webhooks (integraciones) | `GET/POST /api/integrations/webhooks/` |

---

## 1. Health

### `GET /api/health/`

Comprueba que el servicio está arriba.

**Response 200**

```json
{
  "status": "ok",
  "service": "american-horse-racing-vip-picker",
  "time": "2026-08-02T15:42:09.736713+00:00"
}
```

---

## 2. Tracks (Select Track)

### `GET /api/tracks/`

Lista hipódromos activos.

| Query | Tipo | Descripción |
|---|---|---|
| `search` | string | Filtra por code, name o state |
| `ordering` | string | `name` \| `code` (prefijo `-` = desc) |

**Response item**

```json
{
  "id": 1,
  "code": "GP",
  "name": "Gulfstream Park",
  "state": "FL",
  "country": "USA",
  "timezone": "America/New_York",
  "is_active": true,
  "website": ""
}
```

### `GET /api/tracks/{code}/`

Detalle de un track. Ejemplo: `/api/tracks/GP/`

---

## 3. Schedule / Home feed

### `GET /api/schedule/today/`

Cards del día (todas las meets o filtradas por track).

| Query | Tipo | Default | Descripción |
|---|---|---|---|
| `date` | `YYYY-MM-DD` | hoy (ET) | Fecha del card |
| `track` | string | — | Código track (`GP`, `CD`, `SAR`…) |

**Response**

```json
{
  "date": "2026-08-02",
  "timezone": "America/New_York",
  "meets": [
    {
      "id": 1,
      "track": {
        "id": 1,
        "code": "GP",
        "name": "Gulfstream Park",
        "state": "FL",
        "country": "USA",
        "timezone": "America/New_York",
        "is_active": true,
        "website": ""
      },
      "race_date": "2026-08-02",
      "first_post_time": "2026-08-02T12:50:00-04:00",
      "source": "demo",
      "scraped_at": "2026-08-02T11:40:00-04:00",
      "races": [
        {
          "id": 5,
          "track_code": "GP",
          "track_name": "Gulfstream Park",
          "race_date": "2026-08-02",
          "race_number": 5,
          "race_name": "GP Race 5",
          "race_type": "Allowance",
          "distance": "1 1/16M T",
          "distance_furlongs": "8.50",
          "surface": "T",
          "surface_label": "Turf",
          "purse": "70000.00",
          "post_time": "2026-08-02T14:50:00-04:00",
          "status": "next",
          "status_label": "Next",
          "minutes_to_post": 5,
          "video_replay_url": "",
          "top_three": [],
          "dividends": {}
        }
      ]
    }
  ]
}
```

**Status posibles:** `scheduled` | `next` | `running` | `official` | `cancelled` | `scratched`  
**Surface:** `D` Dirt | `T` Turf | `S` Synthetic | `U` Unknown

---

## 4. VIP Board (Mañana / Última Hora)

### `GET /api/vip-board/`

Tabla de comparación de picks VIP.

| Query | Tipo | Default | Descripción |
|---|---|---|---|
| `date` | `YYYY-MM-DD` | hoy (ET) | Fecha |
| `track` | string | — | Código track |

**Response**

```json
{
  "date": "2026-08-02",
  "track": "GP",
  "races": [
    {
      "race_id": 5,
      "track_code": "GP",
      "race_number": 5,
      "race_date": "2026-08-02",
      "status": "next",
      "minutes_to_post": 5,
      "morning": ["4", "2", "9", "7"],
      "last_hour": ["2", "4", "7", "9"]
    }
  ]
}
```

- `morning` → columna **Mañana**
- `last_hour` → columna **Última Hora**
- Cada array = program numbers ordenados (ej. top 4)

---

## 5. Results feed (Llegada + Dividendos)

### `GET /api/results/`

Solo carreras con `status=official`.

| Query | Tipo | Default | Descripción |
|---|---|---|---|
| `date` | `YYYY-MM-DD` | hoy (ET) | Fecha |
| `track` | string | — | Código track |

**Response**

```json
{
  "date": "2026-08-02",
  "track": "GP",
  "results": [
    {
      "id": 6,
      "track_code": "GP",
      "track_name": "Gulfstream Park",
      "race_date": "2026-08-02",
      "race_number": 6,
      "distance": "1 1/16M T",
      "surface": "T",
      "post_time": "2026-08-02T15:20:00-04:00",
      "status": "official",
      "minutes_to_post": -40,
      "video_replay_url": "https://example.com/replay/GP/2026-08-02/R6",
      "top_three": [
        { "position": 1, "program_number": "9", "horse_name": "Winner" },
        { "position": 2, "program_number": "2", "horse_name": "Place" },
        { "position": 3, "program_number": "7", "horse_name": "Show" }
      ],
      "dividends": {
        "W":   { "amount": 8.4,  "combination": "9",     "base_wager": 2.0 },
        "P":   { "amount": 4.2,  "combination": "9",     "base_wager": 2.0 },
        "S":   { "amount": 3.0,  "combination": "9",     "base_wager": 2.0 },
        "EXA": { "amount": 42.6, "combination": "9-2",   "base_wager": 2.0 },
        "TRI": { "amount": 158.8,"combination": "9-2-7", "base_wager": 2.0 }
      }
    }
  ]
}
```

**Claves de dividendos**

| Key | App label |
|---|---|
| `W` | G / Ganador / Win |
| `P` | P / Place |
| `S` | S / Show |
| `EXA` | Exacta |
| `TRI` | Trifecta |
| `SUPER` | Superfecta |
| `DD` | Daily Double |
| `P3` / `P4` / `P5` / `P6` | Pick 3–6 |

---

## 6. Races

### `GET /api/races/`

Listado filtrable.

| Query | Ejemplo | Descripción |
|---|---|---|
| `race_day__track__code` | `GP` | Track |
| `race_day__race_date` | `2026-08-02` | Fecha exacta |
| `race_day__race_date__gte` | `2026-08-01` | Desde |
| `race_day__race_date__lte` | `2026-08-31` | Hasta |
| `status` | `next` | Status exacto |
| `status__in` | `next,scheduled` | Varios status |
| `surface` | `T` | Superficie |
| `race_number` | `5` | Número de carrera |
| `search` | `Allowance` | Busca en name/type/track |
| `ordering` | `post_time` | Orden |

### `GET /api/races/{id}/`

Detalle completo: runners, result, payouts, VIP picks.

```json
{
  "id": 5,
  "track_code": "GP",
  "race_number": 5,
  "distance": "1 1/16M T",
  "status": "next",
  "minutes_to_post": 5,
  "conditions": "",
  "runners": [
    {
      "program_number": "4",
      "horse_name": "Demo Horse GP-5-4",
      "jockey": "Jockey 4",
      "trainer": "Trainer 4",
      "morning_line_odds": "5/1",
      "weight": null,
      "scratched": false,
      "post_position": 4
    }
  ],
  "result": null,
  "payouts": [],
  "vip_picks": [
    {
      "pick_window": "morning",
      "pick_window_label": "Mañana",
      "selections": ["4", "2", "9", "7"],
      "published_at": "2026-08-02T08:00:00-04:00",
      "notes": "demo"
    },
    {
      "pick_window": "last_hour",
      "pick_window_label": "Última Hora",
      "selections": ["2", "4", "7", "9"],
      "published_at": "2026-08-02T14:00:00-04:00",
      "notes": "demo"
    }
  ],
  "top_three": [],
  "dividends": {},
  "video_replay_url": ""
}
```

### `GET /api/races/{id}/picks/`

Solo VIP picks de esa carrera.

### `GET /api/races/{id}/results/`

Alias de detalle (incluye result + payouts).

---

## 7. Race days (meet / card)

### `GET /api/race-days/`

| Query | Ejemplo |
|---|---|
| `track__code` | `GP` |
| `race_date` | `2026-08-02` |
| `ordering` | `-race_date` |

### `GET /api/race-days/{id}/`

Un meet con todas sus carreras embebidas.

---

## 8. Our Picks + Odds Movement (5 MTP)

### `GET /api/our-picks/`

| Query | Tipo | Default |
|---|---|---|
| `date` | `YYYY-MM-DD` | hoy ET |
| `track` | string | — |

```json
{
  "date": "2026-08-02",
  "track": "GP",
  "races": [
    {
      "race_id": 5,
      "track_code": "GP",
      "race_number": 5,
      "status": "next",
      "minutes_to_post": 5,
      "morning": ["4", "2", "9", "7"],
      "mtp5": ["2", "4", "7", "9"],
      "odds_movement": [
        {
          "program_number": "4",
          "morning_odds": "5/1",
          "mtp5_odds": "4.25",
          "delta": "-0.75",
          "direction": "shortened"
        }
      ]
    }
  ]
}
```

### `GET /api/vip-board/`

Además de `morning`, ahora incluye:

- `mtp5` — selecciones a ~5 MTP
- `last_hour` — alias de compatibilidad (= `mtp5`)
- `odds_movement[]`

### `GET /api/races/{id}/odds-movement/`

Movimiento morning → 5 MTP para esa carrera.

---

## 9. Referidos / Share

Identidad por `device_id` (sin JWT).

### `GET /api/referrals/me/?device_id=DEVICE123`

Crea el perfil si no existe. Response:

```json
{
  "device_id": "DEVICE123",
  "code": "AHRAB12CD",
  "share_url": "https://vip.example.com/r/AHRAB12CD",
  "share_text": "Usa mi código AHRAB12CD...",
  "credits": 0,
  "vip_days": 0,
  "stats": { "pending": 0, "qualified": 0, "rewarded": 0, "total": 0 }
}
```

### `POST /api/referrals/me/`

Body: `{ "device_id": "...", "email": "opcional@mail.com" }`

### `POST /api/referrals/claim/`

Body: `{ "device_id": "NEW_DEVICE", "referral_code": "AHRAB12CD" }`

Rewards por defecto (settings): referrer **+10 credits + 1 VIP day**, referee **+5 credits**.

---

## 10. Integrations — Webhooks + Telegram

### Eventos outbound

| Event | Cuándo |
|---|---|
| `race.next` | Carrera marcada NEXT |
| `race.official` | Resultados + dividendos |
| `picks.morning_published` | Our Picks mañana |
| `picks.mtp5_published` | Update 5 MTP |
| `odds.moved` | Movimiento en selecciones VIP |
| `replay.ready` | `video_replay_url` disponible |

Payload envelope:

```json
{
  "event": "race.official",
  "occurred_at": "2026-08-02T15:00:00-04:00",
  "data": { "track_code": "GP", "race_number": 6, "...": "..." }
}
```

Header de firma: `X-Signature: <HMAC-SHA256 hex del body con el secret del endpoint>`

### `GET /api/integrations/events/`

Catálogo de event types.

### `GET/POST /api/integrations/webhooks/`

- **GET** público (lista)
- **POST/PUT/PATCH/DELETE** requieren header `X-Admin-Token: <INTEGRATIONS_ADMIN_TOKEN>`

Body create:

```json
{
  "name": "Partner Hook",
  "url": "https://partner.example.com/hooks/racing",
  "secret": "shared-secret",
  "events": ["race.official", "picks.mtp5_published"],
  "is_active": true
}
```

`events: []` = suscrito a todos.

### `GET /api/integrations/deliveries/`

Auditoría de entregas.

### `POST /api/integrations/test-emit/`

Requiere `X-Admin-Token`. Dispara un evento de prueba (también envía a Telegram si `TELEGRAM_ENABLED=true`).

Telegram: mensajes al canal/grupo `TELEGRAM_VIP_CHAT_ID` (sin usuarios individuales).

---

## Ejemplos cURL

```bash
# Tracks
curl http://127.0.0.1:8000/api/tracks/

# Schedule Gulfstream hoy
curl "http://127.0.0.1:8000/api/schedule/today/?track=GP"

# VIP board + odds movement
curl "http://127.0.0.1:8000/api/vip-board/?track=GP"

# Our Picks
curl "http://127.0.0.1:8000/api/our-picks/?track=GP"

# Resultados
curl "http://127.0.0.1:8000/api/results/?track=GP"

# Referidos
curl "http://127.0.0.1:8000/api/referrals/me/?device_id=DEVICE1"
curl -X POST http://127.0.0.1:8000/api/referrals/claim/ \
  -H "Content-Type: application/json" \
  -d '{"device_id":"DEVICE2","referral_code":"AHRAB12CD"}'

# Registrar webhook
curl -X POST http://127.0.0.1:8000/api/integrations/webhooks/ \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: dev-admin-token" \
  -d '{"name":"Hook","url":"https://example.com/h","secret":"s","events":[]}'
```

---

## Admin

| URL | Descripción |
|---|---|
| `/admin/` | Django Admin (tracks, races, scrape jobs, picks, webhooks, referrals) |

---

## Notas para el cliente móvil

1. Usa `minutes_to_post` para el countdown (“5 MINUTE COUNTDOWN TILL POST”).
2. La carrera con `status=next` es la activa en el header.
3. `top_three` + `dividends` alimentan el panel **Llegada / Dividendos**.
4. `video_replay_url` alimenta el botón **VIDEO REPLAY**.
5. `morning` / `mtp5` (o `last_hour`) alimentan la tabla VIP Picks; `odds_movement` el panel 5 MTP.
6. Referidos: guarda `device_id` localmente y usa `/api/referrals/me/` + share_text.
7. Códigos de track alineados a Equibase: `GP`, `CD`, `SAR`, `BAQ`, `SA`, `DMR`, etc.

Ver también: [DATA_SOURCES.md](./DATA_SOURCES.md) — fuentes externas y estrategia multi-source.
