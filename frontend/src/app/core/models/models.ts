export interface User {
  id: number;
  name: string;
  email: string;
  telegram_chat_id?: string | null;
  notify_email?: string | null;
  created_at: string;
}

export type Platform = 'bookmyshow' | 'district' | 'both' | 'mock';
export type TrackerStatus = 'active' | 'stopped' | 'fulfilled';

export interface Tracker {
  id: number;
  user_id: number;
  movie_id: number;
  movie_title?: string;
  city: string;
  date: string;
  platform: Platform;
  cinema: string;
  language?: string | null;
  format?: string | null;
  start_time?: string | null;
  end_time?: string | null;
  seats_required: number;
  adjacent_seats: boolean;
  status: TrackerStatus;
  check_interval: number;
  last_checked_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface TrackerCreateRequest {
  movie_title: string;
  city: string;
  date: string;
  platform: Platform;
  cinema: string;
  language?: string;
  format?: string;
  start_time?: string;
  end_time?: string;
  seats_required: number;
  adjacent_seats: boolean;
  check_interval: number;
}

export interface Show {
  id: number;
  tracker_id: number;
  provider: string;
  cinema: string;
  screen?: string | null;
  show_time: string;
  available_seats: number;
  adjacent_available?: boolean | null;
  booking_url?: string | null;
  last_seen_at: string;
}

export interface AppNotification {
  id: number;
  tracker_id: number;
  notification_type: string;
  message: string;
  sent_at: string;
  status: string;
}

export interface MovieResult {
  id: number;
  title: string;
  external_id?: string;
  language?: string;
  poster_url?: string;
}
