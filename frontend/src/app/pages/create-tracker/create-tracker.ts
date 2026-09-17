import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatSnackBar } from '@angular/material/snack-bar';
import { TrackerService } from '../../core/services/tracker.service';
import { Platform, TrackerCreateRequest } from '../../core/models/models';

@Component({
  selector: 'app-create-tracker',
  standalone: true,
  imports: [
    FormsModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    MatCheckboxModule,
  ],
  templateUrl: './create-tracker.html',
  styleUrl: './create-tracker.scss',
})
export class CreateTracker {
  form: TrackerCreateRequest = {
    movie_title: '',
    city: '',
    date: '',
    platform: 'mock',
    cinema: 'Any Cinema',
    language: '',
    format: '',
    start_time: '',
    end_time: '',
    seats_required: 2,
    adjacent_seats: false,
    check_interval: 5,
  };

  platforms: { value: Platform; label: string }[] = [
    { value: 'mock', label: 'Demo / Mock Provider' },
    { value: 'bookmyshow', label: 'BookMyShow' },
    { value: 'district', label: 'District' },
    { value: 'both', label: 'BookMyShow + District' },
  ];

  intervals = [1, 2, 5, 10, 15];
  submitting = signal(false);

  constructor(private trackerService: TrackerService, private router: Router, private snackBar: MatSnackBar) {}

  submit(): void {
    this.submitting.set(true);
    this.trackerService.create(this.form).subscribe({
      next: () => {
        this.snackBar.open('Tracker created', 'Dismiss', { duration: 2500 });
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.submitting.set(false);
        this.snackBar.open(err?.error?.detail || 'Failed to create tracker', 'Dismiss', { duration: 3000 });
      },
    });
  }
}
