export type Track = {
  id: number;
  code: string;
  name: string;
  state: string;
  country: string;
  timezone: string;
  is_active: boolean;
  website: string;
};

export type Paginated<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export type HealthResponse = {
  status: string;
  service: string;
  time: string;
};

export type TipBlock = {
  label: string;
  horses: string[];
  top: string | null;
};

export type RaceTips = {
  selections?: TipBlock;
  max_speed?: TipBlock;
  first_class?: TipBlock;
  max_pace?: TipBlock;
};

export type OddsMovement = {
  program_number: string;
  morning_odds: string;
  mtp5_odds: string;
  delta: string | null;
  direction: "shortened" | "drifted" | "unchanged" | string;
};

export type FavoriteBoardItem = {
  program_number: string;
  horse_name?: string;
  odds: string;
};

export type ScheduleRace = {
  id: number;
  track_code: string;
  track_name: string;
  race_date: string;
  race_number: number;
  race_name: string;
  race_type: string;
  distance: string;
  surface: string;
  surface_label: string;
  purse: string | null;
  post_time: string | null;
  status: string;
  status_label: string;
  minutes_to_post: number | null;
  video_replay_url: string;
};

export type ScheduleMeet = {
  id: number;
  track: Track;
  race_date: string;
  first_post_time: string | null;
  source: string;
  races: ScheduleRace[];
};

export type ScheduleResponse = {
  date: string;
  timezone: string;
  meets: ScheduleMeet[];
};

export type OurPicksRace = {
  race_id: number;
  track_code: string;
  race_number: number;
  race_date: string;
  status: string;
  minutes_to_post: number | null;
  tips?: RaceTips | null;
  morning: string[];
  mtp5: string[];
  favorites?: FavoriteBoardItem[];
  odds_movement: OddsMovement[];
};

export type OurPicksResponse = {
  date: string;
  track: string | null;
  races: OurPicksRace[];
};

export type VipBoardRace = {
  race_id: number;
  track_code: string;
  race_number: number;
  race_date: string;
  status: string;
  minutes_to_post: number | null;
  tips?: RaceTips | null;
  morning: string[];
  mtp5: string[];
  last_hour: string[];
  favorites?: FavoriteBoardItem[];
  odds_movement: OddsMovement[];
};

export type VipBoardResponse = {
  date: string;
  track: string | null;
  races: VipBoardRace[];
};

export type Dividend = {
  amount: number;
  combination: string;
  base_wager?: number;
};

export type FinisherLite = {
  position: number;
  program_number: string;
  horse_name?: string;
};

export type ResultsRace = {
  id: number;
  track_code: string;
  track_name: string;
  race_date: string;
  race_number: number;
  distance: string;
  surface: string;
  post_time: string | null;
  status: string;
  minutes_to_post: number | null;
  video_replay_url: string;
  top_three: FinisherLite[];
  dividends: Record<string, Dividend>;
};

export type ResultsResponse = {
  date: string;
  track: string | null;
  results: ResultsRace[];
};

export type Runner = {
  program_number: string;
  horse_name: string;
  jockey: string;
  trainer: string;
  morning_line_odds: string;
  weight: number | null;
  scratched: boolean;
  post_position: number | null;
};

export type VipPick = {
  pick_window: string;
  pick_window_label: string;
  selections: string[];
  published_at: string;
  notes: string;
};

export type RaceDetail = {
  id: number;
  track_code: string;
  track_name?: string;
  race_number: number;
  race_name?: string;
  distance: string;
  surface?: string;
  status: string;
  status_label?: string;
  minutes_to_post: number | null;
  post_time?: string | null;
  conditions: string;
  runners: Runner[];
  result: unknown;
  payouts: unknown[];
  vip_picks: VipPick[];
  top_three: FinisherLite[];
  dividends: Record<string, Dividend>;
  video_replay_url: string;
};

export type ReferralProfile = {
  device_id: string;
  code: string;
  share_url: string;
  share_text: string;
  credits: number;
  vip_days: number;
  stats: {
    pending: number;
    qualified: number;
    rewarded: number;
    total: number;
  };
};

export type ClaimReferralResponse = {
  attribution_id: number;
  referrer: ReferralProfile;
  referee: ReferralProfile;
  rewards: {
    referrer_credits: number;
    referrer_vip_days: number;
    referee_credits: number;
  };
};
