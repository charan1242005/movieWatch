import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';
import { API_BASE } from './api-base';
import { User } from '../models/models';

const TOKEN_KEY = 'moviewatch_token';

@Injectable({ providedIn: 'root' })
export class AuthService {
  currentUser = signal<User | null>(null);

  constructor(private http: HttpClient, private router: Router) {}

  get token(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  isLoggedIn(): boolean {
    return !!this.token;
  }

  register(name: string, email: string, password: string): Observable<User> {
    return this.http.post<User>(`${API_BASE}/api/auth/register`, { name, email, password });
  }

  login(email: string, password: string): Observable<{ access_token: string; token_type: string }> {
    const body = new URLSearchParams();
    body.set('username', email);
    body.set('password', password);
    return this.http
      .post<{ access_token: string; token_type: string }>(`${API_BASE}/api/auth/login`, body.toString(), {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })
      .pipe(tap((res) => localStorage.setItem(TOKEN_KEY, res.access_token)));
  }

  fetchMe(): Observable<User> {
    return this.http.get<User>(`${API_BASE}/api/auth/me`).pipe(tap((u) => this.currentUser.set(u)));
  }

  updateSettings(payload: { telegram_chat_id?: string; notify_email?: string }): Observable<User> {
    return this.http
      .put<User>(`${API_BASE}/api/auth/me/settings`, payload)
      .pipe(tap((u) => this.currentUser.set(u)));
  }

  logout(): void {
    localStorage.removeItem(TOKEN_KEY);
    this.currentUser.set(null);
    this.router.navigate(['/login']);
  }
}
