"""Smoke-test all public API endpoints against a running local server."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"
ADMIN_TOKEN = "dev-admin-token"
results: list[tuple] = []


def req(method, path, data=None, headers=None, expect=200):
    url = BASE + path
    body = None
    hdrs = {"Accept": "application/json"}
    if headers:
        hdrs.update(headers)
    if data is not None:
        body = json.dumps(data).encode()
        hdrs["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as resp:
            raw = resp.read().decode()
            code = resp.status
            try:
                payload = json.loads(raw) if raw else None
            except json.JSONDecodeError:
                payload = raw[:200]
            ok = code == expect or (
                isinstance(expect, (list, tuple)) and code in expect
            )
            results.append((ok, method, path, code, expect, _summary(payload)))
            return code, payload
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            payload = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            payload = raw[:200]
        ok = e.code == expect or (
            isinstance(expect, (list, tuple)) and e.code in expect
        )
        results.append((ok, method, path, e.code, expect, _summary(payload)))
        return e.code, payload
    except Exception as e:  # noqa: BLE001
        results.append((False, method, path, "ERR", expect, str(e)[:120]))
        return None, None


def _summary(payload):
    if payload is None:
        return "-"
    if isinstance(payload, list):
        return f"list[{len(payload)}]"
    if isinstance(payload, dict):
        if "results" in payload and isinstance(payload["results"], list):
            return (
                f"page count={payload.get('count')} "
                f"results={len(payload['results'])}"
            )
        if "races" in payload:
            return f"races={len(payload['races'])}"
        if "meets" in payload:
            return f"meets={len(payload['meets'])}"
        if "events" in payload:
            return f"events={len(payload['events'])}"
        if "code" in payload and "credits" in payload:
            return f"code={payload['code']} credits={payload['credits']}"
        if "movements" in payload:
            return f"movements={len(payload['movements'])}"
        if "status" in payload and "service" in payload:
            return f"status={payload.get('status')}"
        if "rewards" in payload:
            return f"rewards={payload.get('rewards')}"
        keys = ",".join(list(payload.keys())[:6])
        return f"keys={keys}"
    return str(payload)[:80]


def main() -> int:
    # Racing
    req("GET", "/api/health/")
    req("GET", "/api/tracks/")
    req("GET", "/api/tracks/GP/")
    req("GET", "/api/schedule/today/?track=GP")
    req("GET", "/api/vip-board/?track=GP")
    req("GET", "/api/our-picks/?track=GP")
    req("GET", "/api/results/?track=GP")
    req("GET", "/api/race-days/?track__code=GP")
    _code, races = req("GET", "/api/races/?race_day__track__code=GP")
    race_id = None
    if isinstance(races, dict) and races.get("results"):
        race_id = races["results"][0]["id"]
    if race_id:
        req("GET", f"/api/races/{race_id}/")
        req("GET", f"/api/races/{race_id}/picks/")
        req("GET", f"/api/races/{race_id}/results/")
        req("GET", f"/api/races/{race_id}/odds-movement/")
    else:
        results.append((False, "GET", "/api/races/{id}/...", "SKIP", 200, "no race_id"))

    # Referrals
    _code, me = req("GET", "/api/referrals/me/?device_id=e2e-referrer")
    ref_code = me.get("code") if isinstance(me, dict) else None
    req(
        "POST",
        "/api/referrals/me/",
        {"device_id": "e2e-referrer2", "email": "r2@example.com"},
        expect=(200, 201),
    )
    if ref_code:
        req(
            "POST",
            "/api/referrals/claim/",
            {"device_id": "e2e-referee-new", "referral_code": ref_code},
            expect=(200, 201),
        )
        req(
            "POST",
            "/api/referrals/claim/",
            {"device_id": "e2e-referee-new", "referral_code": ref_code},
            expect=400,
        )

    # Integrations
    req("GET", "/api/integrations/events/")
    req("GET", "/api/integrations/webhooks/")
    req("GET", "/api/integrations/deliveries/")
    req(
        "POST",
        "/api/integrations/webhooks/",
        {
            "name": "E2E Hook",
            "url": "https://httpbin.org/post",
            "secret": "e2e-secret",
            "events": ["race.next"],
            "is_active": True,
        },
        expect=403,
    )
    _code, wh = req(
        "POST",
        "/api/integrations/webhooks/",
        {
            "name": "E2E Hook",
            "url": "https://httpbin.org/post",
            "secret": "e2e-secret",
            "events": ["race.next"],
            "is_active": True,
        },
        headers={"X-Admin-Token": ADMIN_TOKEN},
        expect=201,
    )
    wh_id = wh.get("id") if isinstance(wh, dict) else None
    req(
        "POST",
        "/api/integrations/test-emit/",
        {
            "event_type": "race.next",
            "payload": {
                "track_code": "GP",
                "race_number": 5,
                "race_date": "2026-08-02",
                "minutes_to_post": 5,
            },
        },
        headers={"X-Admin-Token": ADMIN_TOKEN},
    )
    if wh_id:
        req(
            "DELETE",
            f"/api/integrations/webhooks/{wh_id}/",
            headers={"X-Admin-Token": ADMIN_TOKEN},
            expect=(200, 204),
        )

    # Admin login page (HTML)
    req("GET", "/admin/login/", expect=200)

    print("\n=== ENDPOINT TEST REPORT ===")
    ok_n = sum(1 for r in results if r[0])
    fail_n = sum(1 for r in results if not r[0])
    for ok, method, path, code, expect, summary in results:
        mark = "PASS" if ok else "FAIL"
        print(f"{mark:4} {method:6} {code!s:>4}  {path}  | {summary}")
    print(f"\nTOTAL: {ok_n} passed, {fail_n} failed, {len(results)} tested")
    print(f"SERVER: {BASE}")
    print("ADMIN:  http://127.0.0.1:8000/admin/  user=jhon")
    return 1 if fail_n else 0


if __name__ == "__main__":
    sys.exit(main())
