# VIP Picker — App Android (Expo)

App móvil en **React Native / Expo (TypeScript)** que consume el API Django de American Horse Racing VIP Picker.

## Pantallas

| Tab / ruta | Contenido |
|---|---|
| Hoy | Schedule del día + detalle de carrera |
| Picks | Our Picks, tip sheet CONSEJOS, favoritos, odds movement |
| VIP | Tablero Mañana vs 5 MTP / Última Hora |
| Resultados | Llegada + dividendos + replay |
| Más → Referidos | Código, share, claim |
| Más → Ajustes API | URL del backend + health check |

## Requisitos

- Node.js 20+ (o el portable en `%LOCALAPPDATA%\nodejs-portable`)
- Backend Django en marcha (`python manage.py runserver 0.0.0.0:8000`)
- Emulador Android / dispositivo con Expo Go, **o** `npm run web` para smoke en navegador

## Arranque

```powershell
cd "C:\Users\acade\OneDrive\Documentos\american horse racing vip picker\mobile"
$env:Path = "$env:LOCALAPPDATA\nodejs-portable;$env:Path"   # si usas Node portable
npm install
npm start
```

Luego:

- `a` → Android emulator  
- `w` → Web  
- Escanea QR con Expo Go en el teléfono

## URL del API

Por defecto: `http://10.0.2.2:8000/api` (emulador Android → localhost del PC).

En la app: **Más → Ajustes API**

| Escenario | URL ejemplo |
|---|---|
| Emulador Android | `http://10.0.2.2:8000/api` |
| Web / simulador | `http://127.0.0.1:8000/api` |
| Teléfono en la misma Wi‑Fi | `http://IP-DE-TU-PC:8000/api` |
| Túnel Cloudflare/ngrok | `https://xxxx.trycloudflare.com/api` |

`usesCleartextTraffic` está habilitado en `app.json` para HTTP de desarrollo.

## Estructura

```
mobile/
  app/                 # Expo Router (tabs + stacks)
  src/api/             # cliente tipado
  src/context/         # Settings (URL, track, device_id)
  src/components/      # UI compartida
  src/theme/           # colores / tipografías
```

## Datos de prueba en el backend

```powershell
cd ..
.\.venv\Scripts\Activate.ps1
python manage.py seed_demo --tracks GP,CD,SAR
python manage.py seed_betamerica_cnl
python manage.py runserver 0.0.0.0:8000
```
