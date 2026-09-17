import { Component, OnInit, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { NotificationService } from '../../core/services/notification.service';
import { AppNotification } from '../../core/models/models';

@Component({
  selector: 'app-notifications',
  standalone: true,
  imports: [DatePipe, MatCardModule, MatIconModule],
  templateUrl: './notifications.html',
  styleUrl: './notifications.scss',
})
export class Notifications implements OnInit {
  notifications = signal<AppNotification[]>([]);
  loading = signal(true);

  constructor(private notificationService: NotificationService) {}

  ngOnInit(): void {
    this.notificationService.list().subscribe({
      next: (n) => {
        this.notifications.set(n);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  iconFor(type: string): string {
    switch (type) {
      case 'email': return 'mail';
      case 'telegram': return 'send';
      default: return 'notifications';
    }
  }
}
