# Guía de uso — American Horse Racing VIP Picker

Manual práctico para operar el backend: panel de administración, picks VIP, scraping, API de la app, referidos e integraciones.

| Recurso | URL / ruta |
|---|---|
| Panel admin (español) | http://127.0.0.1:8000/admin/ |
| API REST | http://127.0.0.1:8000/api/ |
| Health | http://127.0.0.1:8000/api/health/ |
| App Android (Expo) | [../mobile/README.md](../mobile/README.md) |
| Endpoints técnicos | [API_ENDPOINTS.md](API_ENDPOINTS.md) |
| Ejemplos JSON | [API_EXAMPLES.md](API_EXAMPLES.md) |
| Fuentes de datos | [DATA_SOURCES.md](DATA_SOURCES.md) |

---

## 1. Qué es la herramienta

Sistema Django que alimenta la app móvil **American Horse Racing VIP Picker** con:

1. **Carreras** — hipódromos, jornadas, participantes, resultados y dividendos  
2. **Picks VIP** — tip sheets (CONSEJOS) y tablero Mañana / 5 MTP / Última Hora  
3. **Cuotas** — snapshots y movimiento de odds  
4. **Scraping** — carga automática o demo de entries/results  
5. **Integraciones** — webhooks salientes y Telegram al canal VIP  
6. **Referidos** — códigos por dispositivo, créditos y días VIP  

La API pública de carreras no pide login. El panel `/admin/` sí (usuarios staff/superuser).

---

## 2. Arranque en local

En PowerShell, desde la carpeta del proyecto:

```powershell
cd "C:\Users\acade\OneDrive\Documentos\american horse racing vip picker"
.\.venv\Scripts\Activate.ps1
copy .env.example .env          # solo la primera vez
python manage.py migrate
python manage.py sync_tracks
python manage.py seed_demo --tracks GP,CD,SAR
python manage.py runserver
```

Luego abre:

- Admin → http://127.0.0.1:8000/admin/  
- API → http://127.0.0.1:8000/api/health/  

### Usuarios admin de ejemplo

| Usuario | Uso |
|---|---|
| `jhon` | Superusuario principal |
| `jose` | Superusuario adicional |

Si olvidaste la contraseña, se puede resetear con:

```powershell
python manage.py changepassword jose
```

---

## 3. Panel de administración

Interfaz **Jazzmin en español**. Tras el login verás el **Panel de control** con tarjetas:

| Tarjeta | Significado |
|---|---|
| Carreras hoy | Carreras con fecha de jornada = hoy (hora NY) |
| Jobs fallidos | Scrapes con error (útil para diagnóstico) |
| Perfiles de referido | Usuarios/dispositivos en el programa de referidos |
| Webhooks activos | Endpoints outbound habilitados |

### Menú lateral (módulos)

| Grupo | Qué gestionar |
|---|---|
| **Carreras** | Hipódromos, jornadas, carreras, resultados, hojas de consejos, picks VIP, cuotas, jobs de scrape |
| **Integraciones** | Endpoints webhook y entregas (auditoría) |
| **Referidos** | Perfiles, atribuciones y ledger de recompensas |
| **Autenticación** | Usuarios y grupos de Django |

---

## 4. Flujo diario recomendado (operador VIP)

### Paso A — Datos del día

1. Confirma hipódromos activos en **Carreras → Hipódromos**.  
2. Carga entries (automático o manual):

```powershell
python manage.py scrape_entries --tracks GP,CD,SAR
# o demo:
python manage.py seed_demo --tracks GP --days 1
# tip sheet estilo BetAmerica CNL:
python manage.py seed_betamerica_cnl
```

3. En admin, revisa **Jornadas** y **Carreras** del día.

### Paso B — Publicar Our Picks / CONSEJOS

Para cada carrera relevante:

1. Abre **Hojas de consejos** (o créala desde la carrera).  
2. Completa las 4 listas JSON de números de programa, por ejemplo:

| Campo | Etiqueta en app | Ejemplo |
|---|---|---|
| Selecciones | SELECCIONES | `["5","2","8"]` |
| Velocidad máxima | VELOCIDAD MAXIMA | `["1","4","3"]` |
| Primera clase | PRIMERA CLASE | `["5","7","2"]` |
| Ritmo máximo | RITMO MAXIMO | `["6","5","1"]` |

3. El pick de **Mañana / Our Picks** se arma con el **primero** de cada categoría → en el ejemplo: `["5","1","5","6"]`.  
4. Opcional: crea también un **Pick VIP** con ventana `Mañana / Our Picks` o `5 MTP` si quieres fijarlo a mano.

Comprueba en la API:

```
GET http://127.0.0.1:8000/api/our-picks/?track=CNL
GET http://127.0.0.1:8000/api/vip-board/?track=GP
```

### Paso C — Cerca del post (5 MTP)

Cuando la carrera se acerca:

```powershell
python manage.py scrape_near_post
```

Esto actualiza cuotas / picks de ventana corta según la configuración (`NEAR_POST_MTP_THRESHOLD`, por defecto 15 min).

### Paso D — Resultados

```powershell
python manage.py scrape_results --tracks GP
# o en vivo durante la tarde:
python manage.py scrape_live --tracks GP,CD,SAR
```

En admin: **Resultados** (llegada) + dividendos en la carrera.  
En la app: `GET /api/results/?track=GP`.

---

## 5. Cómo usar cada módulo del admin

### Hipódromos

- `code` corto (GP, CD, SAR, CNL…) — es el que usa la API (`?track=GP`).  
- Marca **Activo** solo los que quieres en producción.

### Jornadas y carreras

- Una **jornada** = un hipódromo + una fecha.  
- Cada **carrera** tiene número, distancia, superficie, post time y estado (Programada / Siguiente / En curso / Oficial…).  
- Dentro de la carrera puedes editar **Participantes**, **Dividendos** y **Picks VIP** (inlines).

### Hojas de consejos

Contenido editorial estilo BetAmerica. Es la fuente principal de “Our Picks” cuando existe tip sheet.

### Picks VIP

| Ventana | Uso |
|---|---|
| Mañana / Our Picks | Publicación matutina |
| 5 MTP | Actualización a ~5 minutos del post |
| Última Hora | Compatibilidad con clientes antiguos |

`selections` es una lista JSON de strings: `["4","2","9","7"]`.

### Jobs de scrape

Solo lectura. Sirve para ver si un scrape terminó en **Éxito**, **Parcial** o **Fallido**, y el mensaje de error.

### Webhooks

1. Crea un **Endpoint webhook** (nombre, URL, secreto HMAC, eventos).  
2. Deja `events` vacío para recibir todos, o lista JSON de tipos (`race.official`, `picks.morning_published`, etc.).  
3. Las **Entregas webhook** son auditoría (payload y respuesta HTTP, no se editan).

Token para crear/editar vía API (no vía formulario admin): cabecera `X-Admin-Token` = valor de `INTEGRATIONS_ADMIN_TOKEN` en `.env`.

### Referidos

1. La app pide perfil con `device_id` → se crea código tipo `AHRxxxxxx`.  
2. Otro dispositivo hace **claim** del código.  
3. En admin ves créditos, días VIP y el **Ledger**.

---

## 6. API para la app (resumen)

Base: `http://127.0.0.1:8000/api/`

| Pantalla app | Endpoint |
|---|---|
| Ping | `GET /health/` |
| Elegir pista | `GET /tracks/` |
| Carreras de hoy | `GET /schedule/today/?track=GP` |
| Tablero Mañana vs 5 MTP | `GET /vip-board/?track=GP` |
| Our Picks + tips + odds | `GET /our-picks/?track=GP` |
| Resultados | `GET /results/?track=GP` |
| Detalle carrera | `GET /races/{id}/` |
| Mi referido | `GET /referrals/me/?device_id=DEVICE123` |
| Canjear código | `POST /referrals/claim/` |

Detalle completo: [API_ENDPOINTS.md](API_ENDPOINTS.md) y [API_EXAMPLES.md](API_EXAMPLES.md).

Prueba rápida en el navegador o:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health/
Invoke-RestMethod "http://127.0.0.1:8000/api/our-picks/?track=GP"
```

---

## 7. Scraping y fuentes de datos

Configura en `.env` la variable `SCRAPER_SOURCE` (cadena con failover):

| Valor | Cuándo usarlo |
|---|---|
| `demo` | Desarrollo / demos sin internet de datos reales |
| `equibase,demo` | Intentar Equibase; si falla, demo |
| `equibase,racing_api,demo` | Cadena completa (recomendado si tienes Racing API) |

### Comandos útiles

```powershell
python manage.py sync_tracks
python manage.py scrape_entries --date 2026-08-02 --tracks GP,CD
python manage.py scrape_results --date 2026-08-02 --tracks GP
python manage.py scrape_live --tracks GP,CD,SAR
python manage.py scrape_near_post
python manage.py seed_demo --tracks GP,CD,SAR
python manage.py seed_betamerica_cnl
```

Forzar fuente en un comando:

```powershell
python manage.py scrape_results --source demo --tracks GP
```

### Cron / Task Scheduler

Los horarios están en `config/settings.py` (`CRONJOBS`, zona `America/New_York`):

- Mañana: entries  
- Cada ~5 min (tarde): live  
- Cerca del post: `scrape_near_post`  
- Noche: catch-up de resultados  

En Windows usa **Programador de tareas** apuntando al `python.exe` del `.venv` y `manage.py`.

---

## 8. Telegram (canal VIP)

En `.env`:

```env
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_VIP_CHAT_ID=-100xxxxxxxxxx
```

Cuando el scraper/dispatcher emite eventos (picks publicados, carrera oficial, etc.), se envía al chat configurado. No hay vinculación Telegram por usuario final.

---

## 9. Referidos (configuración)

| Variable `.env` | Efecto |
|---|---|
| `REFERRAL_SHARE_BASE_URL` | Plantilla del link (`{code}` se sustituye) |
| `REFERRAL_REWARD_REFERRER_CREDITS` | Créditos al que invita |
| `REFERRAL_REWARD_REFERRER_VIP_DAYS` | Días VIP al que invita |
| `REFERRAL_REWARD_REFEREE_CREDITS` | Créditos al invitado |
| `REFERRAL_MAX_REWARDS_PER_DAY` | Tope diario de recompensas |

Flujo app:

1. `GET /api/referrals/me/?device_id=...` → obtiene o crea perfil + código.  
2. `POST /api/referrals/claim/` con `device_id` + código → atribuye y premia según reglas.

---

## 10. Checklist de operación

**Al iniciar el día**

- [ ] Servidor en marcha (`runserver` o despliegue)  
- [ ] Entries cargadas (scrape o seed)  
- [ ] Tip sheets / picks de mañana publicados  
- [ ] Comprobar `our-picks` y `vip-board` en la API  

**Durante la jornada**

- [ ] `scrape_live` / cron activo  
- [ ] `scrape_near_post` cerca de cada carrera VIP  
- [ ] Revisar jobs fallidos en el dashboard  

**Al cierre**

- [ ] Resultados y dividendos cargados  
- [ ] Revisar entregas webhook / Telegram si aplica  

---

## 11. Problemas frecuentes

| Síntoma | Qué revisar |
|---|---|
| Admin en blanco / sin CSS | Servidor corriendo; Jazzmin instalado (`pip install -r requirements.txt`) |
| API vacía | Correr `seed_demo` o `scrape_entries`; filtrar con `?track=` correcto |
| Equibase no trae datos | Bloqueo anti-bot; usar `demo` o credenciales `racing_api` |
| Webhook no dispara | Endpoint **Activo**, eventos correctos, URL alcanzable; ver **Entregas** |
| Our Picks sin tips | Falta **Hoja de consejos** para esa carrera |
| Login admin falla | Usuario con `is_staff`; reset con `changepassword` |

---

## 12. Límites importantes

- Las respuestas JSON de la API **siguen en inglés** (claves de campos); el español es del panel admin.  
- Los picks VIP son **contenido editorial propio**; el scraper trae entries/results, no inventa el tip sheet en producción.  
- Respeta delays de scraping y términos de uso de las fuentes externas (ver [DATA_SOURCES.md](DATA_SOURCES.md)).

---

## 13. Documentación relacionada

| Documento | Contenido |
|---|---|
| [../README.md](../README.md) | Arranque rápido y overview |
| [API_ENDPOINTS.md](API_ENDPOINTS.md) | Contrato de cada endpoint |
| [API_EXAMPLES.md](API_EXAMPLES.md) | Peticiones/respuestas de ejemplo |
| [DATA_SOURCES.md](DATA_SOURCES.md) | Equibase, Racing API, demo, failover |
