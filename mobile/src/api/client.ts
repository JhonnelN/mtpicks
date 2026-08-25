import type {
  ClaimReferralResponse,
  HealthResponse,
  OurPicksResponse,
  Paginated,
  RaceDetail,
  ReferralProfile,
  ResultsResponse,
  ScheduleResponse,
  Track,
  VipBoardResponse,
} from "./types";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function normalizeBase(url: string): string {
  return url.replace(/\/+$/, "");
}

async function request<T>(
  baseUrl: string,
  path: string,
  init?: RequestInit
): Promise<T> {
  const url = `${normalizeBase(baseUrl)}${path.startsWith("/") ? path : `/${path}`}`;
  let response: Response;
  try {
    response = await fetch(url, {
      ...init,
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        ...(init?.headers || {}),
      },
    });
  } catch {
    throw new ApiError(
      "Sin conexión con el API. Revisa la URL en Ajustes.",
      0
    );
  }

  if (!response.ok) {
    const body = await response.text().catch(() => "");
    let message = body || `Error HTTP ${response.status}`;
    try {
      const parsed = JSON.parse(body) as { detail?: string; code?: string };
      if (parsed.detail) message = parsed.detail;
    } catch {
      // keep raw body
    }
    throw new ApiError(message, response.status);
  }

  return (await response.json()) as T;
}

function withTrack(path: string, track?: string | null): string {
  if (!track) return path;
  const join = path.includes("?") ? "&" : "?";
  return `${path}${join}track=${encodeURIComponent(track)}`;
}

export const api = {
  health: (baseUrl: string) => request<HealthResponse>(baseUrl, "/health/"),

  tracks: (baseUrl: string) =>
    request<Paginated<Track> | Track[]>(baseUrl, "/tracks/").then((data) =>
      Array.isArray(data) ? data : data.results
    ),

  scheduleToday: (baseUrl: string, track?: string | null) =>
    request<ScheduleResponse>(baseUrl, withTrack("/schedule/today/", track)),

  ourPicks: (baseUrl: string, track?: string | null) =>
    request<OurPicksResponse>(baseUrl, withTrack("/our-picks/", track)),

  vipBoard: (baseUrl: string, track?: string | null) =>
    request<VipBoardResponse>(baseUrl, withTrack("/vip-board/", track)),

  results: (baseUrl: string, track?: string | null) =>
    request<ResultsResponse>(baseUrl, withTrack("/results/", track)),

  raceDetail: (baseUrl: string, id: number | string) =>
    request<RaceDetail>(baseUrl, `/races/${id}/`),

  referralMe: (baseUrl: string, deviceId: string) =>
    request<ReferralProfile>(
      baseUrl,
      `/referrals/me/?device_id=${encodeURIComponent(deviceId)}`
    ),

  claimReferral: (
    baseUrl: string,
    deviceId: string,
    referralCode: string
  ) =>
    request<ClaimReferralResponse>(baseUrl, "/referrals/claim/", {
      method: "POST",
      body: JSON.stringify({
        device_id: deviceId,
        referral_code: referralCode.trim().toUpperCase(),
      }),
    }),
};

/** Default for Android emulator → host machine localhost */
export const DEFAULT_API_BASE = "http://10.0.2.2:8000/api";
