import { Component, signal } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { AuthService } from '../../core/services/auth.service';

const THEME_KEY = 'moviewatch_theme';

@Component({
  selector: 'app-nav',
  standalone: true,
  imports: [RouterLink, RouterLinkActive, MatToolbarModule, MatIconModule, MatButtonModule],
  templateUrl: './nav.html',
  styleUrl: './nav.scss',
})
export class Nav {
  isDark = signal(true);

  constructor(public auth: AuthService) {
    const saved = localStorage.getItem(THEME_KEY);
    const dark = saved ? saved === 'dark' : true;
    this.isDark.set(dark);
    this.applyTheme(dark);
  }

  toggleTheme(): void {
    const dark = !this.isDark();
    this.isDark.set(dark);
    localStorage.setItem(THEME_KEY, dark ? 'dark' : 'light');
    this.applyTheme(dark);
  }

  private applyTheme(dark: boolean): void {
    document.body.classList.toggle('dark-theme', dark);
    document.body.classList.toggle('light-theme', !dark);
  }

  logout(): void {
    this.auth.logout();
  }
}
