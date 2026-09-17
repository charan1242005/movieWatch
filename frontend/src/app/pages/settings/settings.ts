import { Component, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar } from '@angular/material/snack-bar';
import { AuthService } from '../../core/services/auth.service';
import { NotificationService } from '../../core/services/notification.service';

const THEME_KEY = 'moviewatch_theme';
const DEFAULT_INTERVAL_KEY = 'moviewatch_default_interval';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [FormsModule, MatCardModule, MatFormFieldModule, MatInputModule, MatButtonModule, MatSelectModule],
  templateUrl: './settings.html',
  styleUrl: './settings.scss',
})
export class Settings implements OnInit {
  notifyEmail = '';
  telegramChatId = '';
  theme = localStorage.getItem(THEME_KEY) || 'dark';
  defaultInterval = Number(localStorage.getItem(DEFAULT_INTERVAL_KEY) || 5);
  intervals = [1, 2, 5, 10, 15];
  saving = signal(false);

  constructor(
    private auth: AuthService,
    private notificationService: NotificationService,
    private snackBar: MatSnackBar,
  ) {}

  ngOnInit(): void {
    this.auth.fetchMe().subscribe((u) => {
      this.notifyEmail = u.notify_email || u.email;
      this.telegramChatId = u.telegram_chat_id || '';
    });
  }

  saveNotifications(): void {
    this.saving.set(true);
    this.auth.updateSettings({ notify_email: this.notifyEmail, telegram_chat_id: this.telegramChatId }).subscribe({
      next: () => {
        this.saving.set(false);
        this.snackBar.open('Notification settings saved', 'Dismiss', { duration: 2500 });
      },
      error: () => this.saving.set(false),
    });
  }

  saveDefaults(): void {
    localStorage.setItem(THEME_KEY, this.theme);
    localStorage.setItem(DEFAULT_INTERVAL_KEY, String(this.defaultInterval));
    document.body.classList.toggle('dark-theme', this.theme === 'dark');
    document.body.classList.toggle('light-theme', this.theme === 'light');
    this.snackBar.open('Preferences saved', 'Dismiss', { duration: 2500 });
  }

  sendTestEmail(): void {
    this.notificationService.sendTest('email', 'This is a test notification from MovieWatch.').subscribe({
      next: () => this.snackBar.open('Test email queued', 'Dismiss', { duration: 2500 }),
      error: (err) => this.snackBar.open(err?.error?.detail || 'Failed to send test notification', 'Dismiss', { duration: 3000 }),
    });
  }

  sendTestTelegram(): void {
    this.notificationService.sendTest('telegram', 'This is a test notification from MovieWatch.').subscribe({
      next: () => this.snackBar.open('Test Telegram message queued', 'Dismiss', { duration: 2500 }),
      error: (err) => this.snackBar.open(err?.error?.detail || 'Failed to send test notification', 'Dismiss', { duration: 3000 }),
    });
  }
}
