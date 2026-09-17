import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_BASE } from './api-base';
import { Tracker, TrackerCreateRequest, Show, MovieResult } from '../models/models';

@Injectable({ providedIn: 'root' })
export class TrackerService {
  constructor(private http: HttpClient) {}

  list(): Observable<Tracker[]> {
    return this.http.get<Tracker[]>(`${API_BASE}/api/trackers`);
  }

  get(id: number): Observable<Tracker> {
    return this.http.get<Tracker>(`${API_BASE}/api/trackers/${id}`);
  }

  create(payload: TrackerCreateRequest): Observable<Tracker> {
    return this.http.post<Tracker>(`${API_BASE}/api/trackers`, payload);
  }

  update(id: number, payload: Partial<TrackerCreateRequest>): Observable<Tracker> {
    return this.http.put<Tracker>(`${API_BASE}/api/trackers/${id}`, payload);
  }

  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${API_BASE}/api/trackers/${id}`);
  }

  start(id: number): Observable<Tracker> {
    return this.http.post<Tracker>(`${API_BASE}/api/trackers/${id}/start`, {});
  }

  stop(id: number): Observable<Tracker> {
    return this.http.post<Tracker>(`${API_BASE}/api/trackers/${id}/stop`, {});
  }

  shows(id: number): Observable<Show[]> {
    return this.http.get<Show[]>(`${API_BASE}/api/trackers/${id}/shows`);
  }

  searchMovies(q: string, city: string): Observable<MovieResult[]> {
    return this.http.get<MovieResult[]>(`${API_BASE}/api/movies/search`, { params: { q, city } });
  }
}
