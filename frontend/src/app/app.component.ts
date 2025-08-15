import { Component, ElementRef, ViewChild, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { AuthService } from './auth.service';
import { User } from 'firebase/auth';
import { environment } from '../environments/environment';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule    
  ],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  @ViewChild('resultsContainer') resultsContainer!: ElementRef;

  titleSearching: string = '';
  results: any[] = [];
  loading: boolean = false;
  error: string | null = null;
  comparison: string | null = null;
  suggestions: string[] = [];
  showSuggestions: boolean = false;
  isDeepDiveButtonDisabled: boolean = true;

  currentUser: User | null = null;
  loggedIn: boolean = false;

  constructor(private http: HttpClient, private authService: AuthService) {}

  ngOnInit(): void {
    this.authService.getCurrentUser().subscribe(user => {
      this.currentUser = user;
      this.loggedIn = !!user;
    });
  }

  async signInWithGoogle(): Promise<void> {
    try {
      const user = await this.authService.signInWithGoogle().toPromise();
      this.currentUser = user || null;
      this.loggedIn = !!user;
      console.log('User signed in:', this.currentUser?.email);
    } catch (error) {
      console.error('Google sign-in error:', error);
      this.error = 'Error al iniciar sesión con Google.';
    }
  }

  async signOut(): Promise<void> {
    try {
      await this.authService.signOut().toPromise();
      this.currentUser = null;
      this.loggedIn = false;
      console.log('User signed out.');
    } catch (error) {
      console.error('Sign-out error:', error);
      this.error = 'Error al cerrar sesión.';
    }
  }

  private async getAuthHeaders(): Promise<HttpHeaders> {
    if (!this.loggedIn || !this.currentUser) {
      throw new Error("User not logged in.");
    }
    const token = await this.currentUser.getIdToken();
    return new HttpHeaders({
      'Authorization': `Bearer ${token}`
    });
  }

  async searchRecommendations(): Promise<void> {
    if (!this.titleSearching.trim()) {
      return;
    }

    this.loading = true;
    this.error = null;
    this.results = [];
    this.showSuggestions = false; // Hide suggestions when searching
    this.isDeepDiveButtonDisabled = true; // Disable deep dive button on new search

    try {
      const headers = await this.getAuthHeaders();
            this.http.post<any[]>(`${environment.apiUrl}/api/recomend`, { titolo: this.titleSearching }, { headers }).subscribe({
        next: (data) => {
          this.results = data;
          this.loading = false;
          this.isDeepDiveButtonDisabled = this.results.length !== 5;
        },
        error: (err) => {
          this.error = 'Getting recommendations error, please try again';
          console.error(err);
          this.loading = false;
          this.isDeepDiveButtonDisabled = true;
        }
      });
    } catch (e: any) {
      this.error = e.message;
      this.loading = false;
    }
  }

  onTitleInputChange(): void {
    this.isDeepDiveButtonDisabled = true; // Disable deep dive button when input changes
    if (this.titleSearching.trim().length > 1) {
      // No authentication needed for suggestions, as it's a public endpoint (for now)
            this.http.get<string[]>(`${environment.apiUrl}/api/suggest_titles?query=${this.titleSearching.trim()}`).subscribe({
        next: (data) => {
          this.suggestions = data;
          this.showSuggestions = true;
        },
        error: (err) => {
          console.error('Error fetching suggestions:', err);
          this.suggestions = [];
          this.showSuggestions = false;
        }
      });
    } else {
      this.suggestions = [];
      this.showSuggestions = false;
    }
  }

  selectSuggestion(suggestion: string): void {
    this.titleSearching = suggestion;
    this.showSuggestions = false;
    this.searchRecommendations(); // Immediately search for recommendations after selecting
  }

  async deepDive(): Promise<void> {
    this.loading = true;
    this.error = null;

    try {
      const headers = await this.getAuthHeaders();
            this.http.post<any>(`${environment.apiUrl}/api/deep_dive`, { titolo: this.titleSearching, recommendations: this.results }, { headers }).subscribe({
        next: (data) => {
          console.log("Datos recibidos de deepDive:", data);
          this.results.forEach(book => {
            console.log(`Searching analisis for: '{book.titolo}'`);
            if (data.analysis && data.analysis[book.titolo]) {
              book.analysis = data.analysis[book.titolo];
              console.log(`Analisis found for '{book.titolo}: {book.analysis}`);
            } else {
              console.warn(`not found analisis for: '{book.titolo}'`);
            }
          });
          this.loading = false;
          
          setTimeout(() => {
            this.resultsContainer.nativeElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }, 100);
        },
        error: (err) => {
          this.error = 'Error getting deep dive, please try again';
          console.error(err);
          this.loading = false;
        }
      });
    } catch (e: any) {
      this.error = e.message;
      this.loading = false;
    }
  }
}
