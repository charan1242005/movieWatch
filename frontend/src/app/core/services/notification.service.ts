import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_BASE } from './api-base';
import { AppNotification } from '../models/models';

@Injectable({ providedIn: 'root' })
export class NotificationService {
  constructor(private http: HttpClient) {}

  list(): Observable<AppNotification[]> {
    return this.http.get<AppNotification[]>(`${API_BASE}/api/notifications`);
  }

  sendTest(channel: string, message: string): Observable<AppNotification> {
    return this.http.post<AppNotification>(`${API_BASE}/api/notifications/test`, { channel, message });
  }
}
