import { Component, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar } from '@angular/material/snack-bar';
import { TrackerService } from '../../core/services/tracker.service';
import { Tracker } from '../../core/models/models';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [RouterLink, MatButtonModule, MatIconModule, MatCardModule, MatChipsModule, MatProgressSpinnerModule],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss',
})
export class Dashboard implements OnInit {
  trackers = signal<Tracker[]>([]);
  loading = signal(true);
  actingOn = signal<number | null>(null);

  constructor(private trackerService: TrackerService, private snackBar: MatSnackBar) {}

  ngOnInit(): void {
    this.refresh();
  }

  refresh(): void {
    this.loading.set(true);
    this.trackerService.list().subscribe({
      next: (trackers) => {
        this.trackers.set(trackers);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  lastCheckedLabel(t: Tracker): string {
    if (!t.last_checked_at) return 'Never';
    const diffMs = Date.now() - new Date(t.last_checked_at).getTime();
    const mins = Math.floor(diffMs / 60000);
    if (mins < 1) return 'Just now';
    if (mins === 1) return '1 minute ago';
    if (mins < 60) return `${mins} minutes ago`;
    const hours = Math.floor(mins / 60);
    return `${hours} hour${hours === 1 ? '' : 's'} ago`;
  }

  start(t: Tracker): void {
    this.actingOn.set(t.id);
    this.trackerService.start(t.id).subscribe({
      next: () => {
        this.snackBar.open(`Monitoring started for ${t.movie_title}`, 'Dismiss', { duration: 3000 });
        this.refresh();
        this.actingOn.set(null);
      },
      error: () => this.actingOn.set(null),
    });
  }

  stop(t: Tracker): void {
    this.actingOn.set(t.id);
    this.trackerService.stop(t.id).subscribe({
      next: () => {
        this.refresh();
        this.actingOn.set(null);
      },
      error: () => this.actingOn.set(null),
    });
  }

  remove(t: Tracker): void {
    if (!confirm(`Delete tracker for ${t.movie_title}?`)) return;
    this.trackerService.delete(t.id).subscribe(() => this.refresh());
  }
}
