import { Component, OnInit, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { DatePipe } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { TrackerService } from '../../core/services/tracker.service';
import { Tracker, Show } from '../../core/models/models';

@Component({
  selector: 'app-tracker-details',
  standalone: true,
  imports: [RouterLink, DatePipe, MatCardModule, MatButtonModule, MatIconModule, MatProgressSpinnerModule],
  templateUrl: './tracker-details.html',
  styleUrl: './tracker-details.scss',
})
export class TrackerDetails implements OnInit {
  tracker = signal<Tracker | null>(null);
  shows = signal<Show[]>([]);
  loading = signal(true);
  id!: number;

  constructor(private route: ActivatedRoute, private trackerService: TrackerService) {}

  ngOnInit(): void {
    this.id = Number(this.route.snapshot.paramMap.get('id'));
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.trackerService.get(this.id).subscribe((t) => this.tracker.set(t));
    this.trackerService.shows(this.id).subscribe({
      next: (shows) => {
        this.shows.set(shows);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  isMatch(s: Show, t: Tracker): boolean {
    return s.available_seats >= t.seats_required && (!t.adjacent_seats || !!s.adjacent_available);
  }

  start(): void {
    this.trackerService.start(this.id).subscribe(() => this.load());
  }

  stop(): void {
    this.trackerService.stop(this.id).subscribe(() => this.load());
  }
}
