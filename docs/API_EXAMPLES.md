# API Examples — American Horse Racing VIP Picker

Base URL local: `http://127.0.0.1:8000`

- Formato: **JSON**
- Auth racing/referrals: pública (`AllowAny`)
- Auth escritura webhooks: header `X-Admin-Token`
- Paginación DRF en listados: `{ "count", "next", "previous", "results": [...] }`
- Timezone servidor: `America/New_York`

---

## Índice

1. [Health](#1-health)
2. [Tracks](#2-tracks)
3. [Schedule today](#3-schedule-today)
4. [VIP Board](#4-vip-board)
5. [Our Picks](#5-our-picks)
6. [Results](#6-results)
7. [Race days](#7-race-days)
8. [Races](#8-races)
9. [Referrals](#9-referrals)
10. [Integrations / Webhooks](#10-integrations--webhooks)
11. [Admin](#11-admin)

---

## 1. Health

### `GET /api/health/`

**Request**

```bash
curl -X GET "http://127.0.0.1:8000/api/health/"
```

**Response `200`**

```json
{
  "status": "ok",
  "service": "american-horse-racing-vip-picker",
  "time": "2026-08-02T16:38:10.699657+00:00"
}
```

---

## 2. Tracks

### `GET /api/tracks/`

Lista hipódromos activos.

| Query | Ejemplo | Descripción |
|---|---|---|
| `search` | `Gulf` | Busca code/name/state |
| `ordering` | `name` / `-code` | Orden |

**Request**

```bash
curl -X GET "http://127.0.0.1:8000/api/tracks/"
curl -X GET "http://127.0.0.1:8000/api/tracks/?search=Gulf&ordering=name"
```

**Response `200`**

```json
{
  "count": 20,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 5,
      "code": "AQU",
      "name": "Aqueduct",
      "state": "NY",
      "country": "USA",
      "timezone": "America/New_York",
      "is_active": true,
      "website": ""
    },
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
  ]
}
```

### `GET /api/tracks/{code}/`

**Request**

```bash
curl -X GET "http://127.0.0.1:8000/api/tracks/GP/"
```

**Response `200`**

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

---

## 3. Schedule today

### `GET /api/schedule/today/`

| Query | Ejemplo | Default |
|---|---|---|
| `date` | `2026-08-02` | hoy ET |
| `track` | `GP` | todos |

**Request**

```bash
curl -X GET "http://127.0.0.1:8000/api/schedule/today/?track=GP"
curl -X GET "http://127.0.0.1:8000/api/schedule/today/?track=GP&date=2026-08-02"
```

**Response `200`**

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
      "first_post_time": "2026-08-02T09:34:00-04:00",
      "source": "demo",
      "scraped_at": "2026-08-02T12:34:15.927785-04:00",
      "races": [
        {
          "id": 1,
          "track_code": "GP",
          "track_name": "Gulfstream Park",
          "race_date": "2026-08-02",
          "race_number": 1,
          "race_name": "GP Race 1",
          "race_type": "Allowance",
          "distance": "1 1/16M T",
          "distance_furlongs": "8.50",
          "surface": "T",
          "surface_label": "Turf",
          "purse": "50000.00",
          "post_time": "2026-08-02T09:34:00-04:00",
          "status": "official",
          "status_label": "Official",
          "minutes_to_post": -185,
          "video_replay_url": "https://example.com/replay/GP/2026-08-02/R1",
          "top_three": [
            { "position": 1, "program_number": "4", "horse_name": "Winner" },
            { "position": 2, "program_number": "2", "horse_name": "Place" },
            { "position": 3, "program_number": "7", "horse_name": "Show" }
          ],
          "dividends": {
            "W": { "amount": 8.4, "combination": "4", "base_wager": 2.0 },
            "P": { "amount": 4.2, "combination": "4", "base_wager": 2.0 },
            "S": { "amount": 3.0, "combination": "4", "base_wager": 2.0 },
            "EXA": { "amount": 42.6, "combination": "4-2", "base_wager": 2.0 },
            "TRI": { "amount": 158.8, "combination": "4-2-7", "base_wager": 2.0 }
          }
        }
      ]
    }
  ]
}
```

---

## 4. VIP Board

### `GET /api/vip-board/`

Mañana vs 5 MTP + odds movement.

| Query | Ejemplo |
|---|---|
| `track` | `GP` |
| `date` | `2026-08-02` |

**Request**

```bash
curl -X GET "http://127.0.0.1:8000/api/vip-board/?track=GP"
curl -X GET "http://127.0.0.1:8000/api/vip-board/?track=GP&date=2026-08-02"
```

**Response `200`**

```json
{
  "date": "2026-08-02",
  "track": "GP",
  "races": [
    {
      "race_id": 1,
      "track_code": "GP",
      "race_number": 1,
      "race_date": "2026-08-02",
      "status": "official",
      "minutes_to_post": -185,
      "morning": ["4", "2", "9", "7"],
      "mtp5": ["2", "4", "7", "9"],
      "last_hour": ["2", "4", "7", "9"],
      "odds_movement": [
        {
          "program_number": "4",
          "morning_odds": "5/1",
          "mtp5_odds": "4.40",
          "morning_decimal": "6.0000",
          "mtp5_decimal": "4.4000",
          "delta": "-1.6000",
          "direction": "shortened",
          "direction_label": "Shortened",
          "computed_at": "2026-08-02T12:34:16.167000-04:00"
        },
        {
          "program_number": "2",
          "morning_odds": "3/1",
          "mtp5_odds": "2.70",
          "delta": "-0.3000",
          "direction": "shortened",
          "direction_label": "Shortened",
          "computed_at": "2026-08-02T12:34:16.167000-04:00"
        }
      ]
    }
  ]
}
```

> `last_hour` es alias de compatibilidad de `mtp5`.

---

## 5. Our Picks

### `GET /api/our-picks/`

Alineado al layout BetAmerica ([betamerica.com](https://www.betamerica.com/)):

| Campo API | UI BetAmerica |
|---|---|
| `tips.*` | CONSEJOS verdes (SELECCIONES, VELOCIDAD, PRIMERA CLASE, RITMO) |
| `morning` | Primer caballo de cada tip (= Mañana / Our Picks) |
| `favorites` | Pizarra roja columna **O** (favoritos por odds más cortas) |
| `odds_movement` | Movimiento morning → 5 MTP |

| Query | Ejemplo |
|---|---|
| `track` | `CNL` (Colonial Downs) / `GP` |
| `date` | `2026-08-02` |

**Request (ejemplo Colonial Downs = screenshot)**

```bash
curl -X GET "http://127.0.0.1:8000/api/our-picks/?track=CNL"
python manage.py seed_betamerica_cnl   # carga el ejemplo BetAmerica
```

**Response `200` (mapeo del ejemplo BetAmerica)**

```json
{
  "date": "2026-08-02",
  "track": "CNL",
  "races": [
    {
      "race_id": 25,
      "track_code": "CNL",
      "race_number": 1,
      "status": "next",
      "minutes_to_post": 8,
      "tips": {
        "selections": { "label": "SELECCIONES", "horses": ["5", "3", "4"], "top": "5" },
        "max_speed": { "label": "VELOCIDAD MAXIMA", "horses": ["1", "2", "5"], "top": "1" },
        "first_class": { "label": "PRIMERA CLASE", "horses": ["5", "2", "6"], "top": "5" },
        "max_pace": { "label": "RITMO MAXIMO", "horses": ["6", "3", "7"], "top": "6" }
      },
      "morning": ["5", "1", "5", "6"],
      "mtp5": ["5", "4", "3", "2"],
      "favorites": [
        { "rank": 1, "program_number": "4", "odds": "2", "odds_decimal": "3.0000" },
        { "rank": 2, "program_number": "5", "odds": "5/2", "odds_decimal": "3.5000" },
        { "rank": 3, "program_number": "3", "odds": "3", "odds_decimal": "4.0000" },
        { "rank": 4, "program_number": "2", "odds": "9/2", "odds_decimal": "5.5000" }
      ],
      "odds_movement": [
        {
          "program_number": "5",
          "morning_odds": "5/2",
          "mtp5_odds": "5/2",
          "direction": "unchanged"
        }
      ]
    }
  ]
}
```

> Verde → `morning` = tops `[5,1,5,6]`. Rojo → `favorites` con odds `5/2`, `2`, `3`, `9/2` ordenados por favoritismo real (2-1 < 5/2 < 3-1 < 9/2).

---

## 6. Results

### `GET /api/results/`

Solo carreras `status=official` (Llegada + Dividendos + replay).

| Query | Ejemplo |
|---|---|
| `track` | `GP` |
| `date` | `2026-08-02` |

**Request**

```bash
curl -X GET "http://127.0.0.1:8000/api/results/?track=GP"
curl -X GET "http://127.0.0.1:8000/api/results/?track=GP&date=2026-08-02"
```

**Response `200`**

```json
{
  "date": "2026-08-02",
  "track": "GP",
  "results": [
    {
      "id": 1,
      "track_code": "GP",
      "track_name": "Gulfstream Park",
      "race_date": "2026-08-02",
      "race_number": 1,
      "race_name": "GP Race 1",
      "distance": "1 1/16M T",
      "surface": "T",
      "surface_label": "Turf",
      "post_time": "2026-08-02T09:34:00-04:00",
      "status": "official",
      "status_label": "Official",
      "minutes_to_post": -185,
      "video_replay_url": "https://example.com/replay/GP/2026-08-02/R1",
      "top_three": [
        { "position": 1, "program_number": "4", "horse_name": "Winner" },
        { "position": 2, "program_number": "2", "horse_name": "Place" },
        { "position": 3, "program_number": "7", "horse_name": "Show" }
      ],
      "dividends": {
        "W": { "amount": 8.4, "combination": "4", "base_wager": 2.0 },
        "P": { "amount": 4.2, "combination": "4", "base_wager": 2.0 },
        "S": { "amount": 3.0, "combination": "4", "base_wager": 2.0 },
        "EXA": { "amount": 42.6, "combination": "4-2", "base_wager": 2.0 },
        "TRI": { "amount": 158.8, "combination": "4-2-7", "base_wager": 2.0 }
      }
    }
  ]
}
```

**Claves dividendos:** `W` Ganador · `P` Place · `S` Show · `EXA` Exacta · `TRI` Trifecta · `SUPER` Superfecta

---

## 7. Race days

### `GET /api/race-days/`

| Query | Ejemplo |
|---|---|
| `track__code` | `GP` |
| `race_date` | `2026-08-02` |
| `ordering` | `-race_date` |

**Request**

```bash
curl -X GET "http://127.0.0.1:8000/api/race-days/?track__code=GP&race_date=2026-08-02"
```

**Response `200`**

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
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
      "first_post_time": "2026-08-02T09:34:00-04:00",
      "source": "demo",
      "scraped_at": "2026-08-02T12:34:15.927785-04:00",
      "races": [
        {
          "id": 1,
          "track_code": "GP",
          "race_number": 1,
          "status": "official",
          "distance": "1 1/16M T",
          "top_three": [
            { "position": 1, "program_number": "4", "horse_name": "Winner" }
          ],
          "dividends": {
            "W": { "amount": 8.4, "combination": "4", "base_wager": 2.0 }
          }
        }
      ]
    }
  ]
}
```

### `GET /api/race-days/{id}/`

**Request**

```bash
curl -X GET "http://127.0.0.1:8000/api/race-days/1/"
```

**Response `200`:** mismo shape que un item de `results` arriba.

---

## 8. Races

### `GET /api/races/`

| Query | Ejemplo |
|---|---|
| `race_day__track__code` | `GP` |
| `race_day__race_date` | `2026-08-02` |
| `race_day__race_date__gte` | `2026-08-01` |
| `race_day__race_date__lte` | `2026-08-31` |
| `status` | `next` |
| `status__in` | `next,scheduled` |
| `surface` | `T` |
| `race_number` | `5` |
| `search` | `Allowance` |
| `ordering` | `post_time` |

**Request**

```bash
curl -X GET "http://127.0.0.1:8000/api/races/?race_day__track__code=GP"
curl -X GET "http://127.0.0.1:8000/api/races/?race_day__track__code=GP&status=official&ordering=race_number"
```

**Response `200`**

```json
{
  "count": 8,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "track_code": "GP",
      "track_name": "Gulfstream Park",
      "race_date": "2026-08-02",
      "race_number": 1,
      "race_name": "GP Race 1",
      "race_type": "Allowance",
      "distance": "1 1/16M T",
      "distance_furlongs": "8.50",
      "surface": "T",
      "surface_label": "Turf",
      "purse": "50000.00",
      "post_time": "2026-08-02T09:34:00-04:00",
      "status": "official",
      "status_label": "Official",
      "minutes_to_post": -185,
      "video_replay_url": "https://example.com/replay/GP/2026-08-02/R1",
      "top_three": [
        { "position": 1, "program_number": "4", "horse_name": "Winner" },
        { "position": 2, "program_number": "2", "horse_name": "Place" },
        { "position": 3, "program_number": "7", "horse_name": "Show" }
      ],
      "dividends": {
        "W": { "amount": 8.4, "combination": "4", "base_wager": 2.0 },
        "EXA": { "amount": 42.6, "combination": "4-2", "base_wager": 2.0 },
        "TRI": { "amount": 158.8, "combination": "4-2-7", "base_wager": 2.0 }
      }
    }
  ]
}
```

### `GET /api/races/{id}/`

Detalle completo.

**Request**

```bash
curl -X GET "http://127.0.0.1:8000/api/races/1/"
```

**Response `200`**

```json
{
  "id": 1,
  "track_code": "GP",
  "track_name": "Gulfstream Park",
  "race_date": "2026-08-02",
  "race_number": 1,
  "race_name": "GP Race 1",
  "race_type": "Allowance",
  "distance": "1 1/16M T",
  "distance_furlongs": "8.50",
  "surface": "T",
  "surface_label": "Turf",
  "purse": "50000.00",
  "post_time": "2026-08-02T09:34:00-04:00",
  "status": "official",
  "status_label": "Official",
  "minutes_to_post": -185,
  "video_replay_url": "https://example.com/replay/GP/2026-08-02/R1",
  "top_three": [
    { "position": 1, "program_number": "4", "horse_name": "Winner" },
    { "position": 2, "program_number": "2", "horse_name": "Place" },
    { "position": 3, "program_number": "7", "horse_name": "Show" }
  ],
  "dividends": {
    "W": { "amount": 8.4, "combination": "4", "base_wager": 2.0 },
    "P": { "amount": 4.2, "combination": "4", "base_wager": 2.0 },
    "S": { "amount": 3.0, "combination": "4", "base_wager": 2.0 },
    "EXA": { "amount": 42.6, "combination": "4-2", "base_wager": 2.0 },
    "TRI": { "amount": 158.8, "combination": "4-2-7", "base_wager": 2.0 }
  },
  "conditions": "",
  "runners": [
    {
      "program_number": "1",
      "horse_name": "Demo Horse GP-1-1",
      "jockey": "Jockey 1",
      "trainer": "Trainer 1",
      "morning_line_odds": "2/1",
      "weight": null,
      "scratched": false,
      "post_position": 1
    },
    {
      "program_number": "4",
      "horse_name": "Demo Horse GP-1-4",
      "jockey": "Jockey 4",
      "trainer": "Trainer 4",
      "morning_line_odds": "5/1",
      "weight": null,
      "scratched": false,
      "post_position": 4
    }
  ],
  "result": {
    "winning_time": "1:42.35",
    "official_at": "2026-08-02T12:34:15.950000-04:00",
    "source": "demo",
    "finishers": [
      {
        "position": 1,
        "program_number": "4",
        "horse_name": "Winner",
        "jockey": "",
        "trainer": "",
        "win_payoff": null,
        "place_payoff": null,
        "show_payoff": null
      },
      {
        "position": 2,
        "program_number": "2",
        "horse_name": "Place",
        "jockey": "",
        "trainer": "",
        "win_payoff": null,
        "place_payoff": null,
        "show_payoff": null
      },
      {
        "position": 3,
        "program_number": "7",
        "horse_name": "Show",
        "jockey": "",
        "trainer": "",
        "win_payoff": null,
        "place_payoff": null,
        "show_payoff": null
      }
    ]
  },
  "payouts": [
    {
      "bet_type": "W",
      "bet_type_label": "Win / Ganador",
      "combination": "4",
      "amount": "8.40",
      "base_wager": "2.00"
    },
    {
      "bet_type": "EXA",
      "bet_type_label": "Exacta",
      "combination": "4-2",
      "amount": "42.60",
      "base_wager": "2.00"
    },
    {
      "bet_type": "TRI",
      "bet_type_label": "Trifecta",
      "combination": "4-2-7",
      "amount": "158.80",
      "base_wager": "2.00"
    }
  ],
  "vip_picks": [
    {
      "pick_window": "morning",
      "pick_window_label": "Mañana / Our Picks",
      "selections": ["4", "2", "9", "7"],
      "published_at": "2026-08-02T12:34:16.000000-04:00",
      "notes": "demo"
    },
    {
      "pick_window": "mtp5",
      "pick_window_label": "5 MTP",
      "selections": ["2", "4", "7", "9"],
      "published_at": "2026-08-02T12:34:16.000000-04:00",
      "notes": "demo"
    },
    {
      "pick_window": "last_hour",
      "pick_window_label": "Última Hora",
      "selections": ["2", "4", "7", "9"],
      "published_at": "2026-08-02T12:34:16.000000-04:00",
      "notes": "demo"
    }
  ]
}
```

### `GET /api/races/{id}/picks/`

**Request**

```bash
curl -X GET "http://127.0.0.1:8000/api/races/1/picks/"
```

**Response `200`**

```json
[
  {
    "pick_window": "morning",
    "pick_window_label": "Mañana / Our Picks",
    "selections": ["4", "2", "9", "7"],
    "published_at": "2026-08-02T12:34:16.000000-04:00",
    "notes": "demo"
  },
  {
    "pick_window": "mtp5",
    "pick_window_label": "5 MTP",
    "selections": ["2", "4", "7", "9"],
    "published_at": "2026-08-02T12:34:16.000000-04:00",
    "notes": "demo"
  }
]
```

### `GET /api/races/{id}/results/`

Alias del detalle (incluye result + payouts).

**Request**

```bash
curl -X GET "http://127.0.0.1:8000/api/races/1/results/"
```

**Response `200`:** mismo shape que `GET /api/races/{id}/`.

### `GET /api/races/{id}/odds-movement/`

**Request**

```bash
curl -X GET "http://127.0.0.1:8000/api/races/1/odds-movement/"
```

**Response `200`**

```json
{
  "race_id": 1,
  "track_code": "GP",
  "race_number": 1,
  "movements": [
    {
      "program_number": "4",
      "morning_odds": "5/1",
      "mtp5_odds": "4.40",
      "morning_decimal": "6.0000",
      "mtp5_decimal": "4.4000",
      "delta": "-1.6000",
      "direction": "shortened",
      "direction_label": "Shortened",
      "computed_at": "2026-08-02T12:34:16.167000-04:00"
    },
    {
      "program_number": "2",
      "morning_odds": "3/1",
      "mtp5_odds": "2.70",
      "delta": "-0.3000",
      "direction": "shortened",
      "direction_label": "Shortened",
      "computed_at": "2026-08-02T12:34:16.167000-04:00"
    }
  ]
}
```

`direction`: `shortened` | `drifted` | `unchanged`

---

## 9. Referrals

Identidad por `device_id` (sin JWT).

### `GET /api/referrals/me/`

Crea el perfil si no existe.

**Request**

```bash
curl -X GET "http://127.0.0.1:8000/api/referrals/me/?device_id=DEVICE123"
curl -X GET "http://127.0.0.1:8000/api/referrals/me/?device_id=DEVICE123&email=user@example.com"
```

**Response `200`**

```json
{
  "device_id": "DEVICE123",
  "email": "",
  "code": "AHR7BVASK",
  "share_url": "https://vip.example.com/r/AHR7BVASK",
  "share_text": "Usa mi código AHR7BVASK en American Horse Racing VIP Picker y gana créditos VIP: https://vip.example.com/r/AHR7BVASK",
  "credits": 0,
  "vip_days": 0,
  "stats": {
    "pending": 0,
    "qualified": 0,
    "rewarded": 0,
    "total": 0
  }
}
```

### `POST /api/referrals/me/`

**Request**

```bash
curl -X POST "http://127.0.0.1:8000/api/referrals/me/" \
  -H "Content-Type: application/json" \
  -d "{\"device_id\":\"DEVICE456\",\"email\":\"r2@example.com\"}"
```

**Response `201` (nuevo) / `200` (existente)**

```json
{
  "device_id": "DEVICE456",
  "email": "r2@example.com",
  "code": "AHRTX9Q89",
  "share_url": "https://vip.example.com/r/AHRTX9Q89",
  "share_text": "Usa mi código AHRTX9Q89 en American Horse Racing VIP Picker y gana créditos VIP: https://vip.example.com/r/AHRTX9Q89",
  "credits": 0,
  "vip_days": 0,
  "stats": {
    "pending": 0,
    "qualified": 0,
    "rewarded": 0,
    "total": 0
  }
}
```

### `POST /api/referrals/claim/`

**Request**

```bash
curl -X POST "http://127.0.0.1:8000/api/referrals/claim/" \
  -H "Content-Type: application/json" \
  -d "{\"device_id\":\"NEW_DEVICE\",\"referral_code\":\"AHR7BVASK\"}"
```

**Response `201`**

```json
{
  "attribution_id": 1,
  "referrer": {
    "device_id": "DEVICE123",
    "email": "",
    "code": "AHR7BVASK",
    "share_url": "https://vip.example.com/r/AHR7BVASK",
    "share_text": "Usa mi código AHR7BVASK...",
    "credits": 10,
    "vip_days": 1,
    "stats": {
      "pending": 0,
      "qualified": 0,
      "rewarded": 1,
      "total": 1
    }
  },
  "referee": {
    "device_id": "NEW_DEVICE",
    "code": "AHRXXXXXX",
    "credits": 5,
    "vip_days": 0,
    "stats": { "pending": 0, "qualified": 0, "rewarded": 0, "total": 0 }
  },
  "rewards": {
    "referrer_credits": 10,
    "referrer_vip_days": 1,
    "referee_credits": 5
  }
}
```

**Response `400` (ya reclamado / código inválido / self-referral)**

```json
{
  "code": "already_claimed",
  "detail": "This device already claimed a referral"
}
```

Otros `code`: `missing_device` · `missing_code` · `invalid_code` · `self_referral` · `daily_cap`

---

## 10. Integrations / Webhooks

Escritura requiere:

```http
X-Admin-Token: dev-admin-token
```

(Valor de `INTEGRATIONS_ADMIN_TOKEN` en `.env`)

### Eventos disponibles

| Event | Descripción |
|---|---|
| `race.next` | Carrera marcada NEXT |
| `race.official` | Resultados + dividendos |
| `picks.morning_published` | Our Picks mañana |
| `picks.mtp5_published` | Update 5 MTP |
| `odds.moved` | Movimiento de odds VIP |
| `replay.ready` | Replay disponible |

Envelope outbound:

```json
{
  "event": "race.official",
  "occurred_at": "2026-08-02T15:00:00-04:00",
  "data": {
    "track_code": "GP",
    "race_number": 6,
    "top_three": [],
    "dividends": {}
  }
}
```

Header de firma en el POST al partner: `X-Signature: <HMAC-SHA256 hex del body>`

### `GET /api/integrations/events/`

**Request**

```bash
curl -X GET "http://127.0.0.1:8000/api/integrations/events/"
```

**Response `200`**

```json
{
  "events": [
    { "type": "race.next", "label": "Race Next" },
    { "type": "race.official", "label": "Race Official" },
    { "type": "picks.morning_published", "label": "Morning Picks Published" },
    { "type": "picks.mtp5_published", "label": "5 MTP Picks Published" },
    { "type": "odds.moved", "label": "Odds Moved" },
    { "type": "replay.ready", "label": "Replay Ready" }
  ]
}
```

### `GET /api/integrations/webhooks/`

**Request**

```bash
curl -X GET "http://127.0.0.1:8000/api/integrations/webhooks/"
```

**Response `200`**

```json
{
  "count": 0,
  "next": null,
  "previous": null,
  "results": []
}
```

### `POST /api/integrations/webhooks/`

**Request**

```bash
curl -X POST "http://127.0.0.1:8000/api/integrations/webhooks/" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: dev-admin-token" \
  -d "{
    \"name\": \"Partner Hook\",
    \"url\": \"https://partner.example.com/hooks/racing\",
    \"secret\": \"shared-secret\",
    \"events\": [\"race.official\", \"picks.mtp5_published\"],
    \"is_active\": true
  }"
```

`events: []` = suscrito a **todos** los eventos.

**Response `201`**

```json
{
  "id": 1,
  "name": "Partner Hook",
  "url": "https://partner.example.com/hooks/racing",
  "events": ["race.official", "picks.mtp5_published"],
  "is_active": true,
  "created_at": "2026-08-02T12:36:00.000000-04:00",
  "updated_at": "2026-08-02T12:36:00.000000-04:00"
}
```

> `secret` es write-only: no se devuelve en respuestas posteriores.

**Response `403` (sin token)**

```json
{
  "detail": "You do not have permission to perform this action."
}
```

### `GET /api/integrations/webhooks/{id}/`

**Request**

```bash
curl -X GET "http://127.0.0.1:8000/api/integrations/webhooks/1/"
```

### `PUT/PATCH /api/integrations/webhooks/{id}/`

**Request**

```bash
curl -X PATCH "http://127.0.0.1:8000/api/integrations/webhooks/1/" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: dev-admin-token" \
  -d "{\"is_active\": false}"
```

### `DELETE /api/integrations/webhooks/{id}/`

**Request**

```bash
curl -X DELETE "http://127.0.0.1:8000/api/integrations/webhooks/1/" \
  -H "X-Admin-Token: dev-admin-token"
```

**Response `204`** (sin body)

### `GET /api/integrations/deliveries/`

Auditoría de entregas.

| Query | Ejemplo |
|---|---|
| `event_type` | `race.official` |
| `status` | `success` / `failed` / `pending` |
| `endpoint` | `1` |

**Request**

```bash
curl -X GET "http://127.0.0.1:8000/api/integrations/deliveries/"
curl -X GET "http://127.0.0.1:8000/api/integrations/deliveries/?event_type=race.next&status=success"
```

**Response `200`**

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "endpoint": 1,
      "endpoint_name": "Partner Hook",
      "event_type": "race.next",
      "payload": {
        "event": "race.next",
        "occurred_at": "2026-08-02T12:36:10.000000-04:00",
        "data": {
          "track_code": "GP",
          "race_number": 5,
          "minutes_to_post": 5
        }
      },
      "status": "success",
      "status_code": 200,
      "attempts": 1,
      "next_retry_at": null,
      "error_message": "",
      "created_at": "2026-08-02T12:36:10.000000-04:00",
      "delivered_at": "2026-08-02T12:36:10.200000-04:00"
    }
  ]
}
```

### `POST /api/integrations/test-emit/`

Dispara un evento de prueba (webhooks + Telegram si está enabled).

**Request**

```bash
curl -X POST "http://127.0.0.1:8000/api/integrations/test-emit/" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: dev-admin-token" \
  -d "{
    \"event_type\": \"race.next\",
    \"payload\": {
      \"track_code\": \"GP\",
      \"race_number\": 5,
      \"race_date\": \"2026-08-02\",
      \"minutes_to_post\": 5
    }
  }"
```

**Response `200`**

```json
{
  "event": "race.next",
  "webhooks": [
    {
      "endpoint_id": 1,
      "status": "success",
      "status_code": 200
    }
  ],
  "telegram": false
}
```

---

## 11. Admin

### `GET /admin/login/`

**Request**

```bash
curl -X GET "http://127.0.0.1:8000/admin/login/"
```

**Browser**

1. Abrir http://127.0.0.1:8000/admin/
2. Usuario: `jhon`
3. Contraseña: la configurada en el despliegue

---

## Errores comunes

| HTTP | Cuándo |
|---|---|
| `400` | Body inválido / referral claim inválido |
| `403` | Falta o es incorrecto `X-Admin-Token` |
| `404` | Track/race/webhook no existe |
| `500` | Error interno |

Ejemplo genérico DRF:

```json
{
  "detail": "Not found."
}
```

---

## Quick copy — colección mínima móvil

```bash
# Home / select track
curl "http://127.0.0.1:8000/api/tracks/"
curl "http://127.0.0.1:8000/api/schedule/today/?track=GP"

# VIP + odds 5 MTP
curl "http://127.0.0.1:8000/api/vip-board/?track=GP"
curl "http://127.0.0.1:8000/api/our-picks/?track=GP"

# Resultados
curl "http://127.0.0.1:8000/api/results/?track=GP"
curl "http://127.0.0.1:8000/api/races/1/"

# Referidos
curl "http://127.0.0.1:8000/api/referrals/me/?device_id=DEVICE1"
curl -X POST "http://127.0.0.1:8000/api/referrals/claim/" \
  -H "Content-Type: application/json" \
  -d "{\"device_id\":\"DEVICE2\",\"referral_code\":\"AHRXXXXXX\"}"
```

Ver también:

- [API_ENDPOINTS.md](./API_ENDPOINTS.md) — referencia funcional
- [DATA_SOURCES.md](./DATA_SOURCES.md) — fuentes y eventos del scraper
