import { Injectable } from '@angular/core';
import { getAuth, GoogleAuthProvider, signInWithRedirect, User, getRedirectResult } from 'firebase/auth';
import { from, Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private auth = getAuth();

  constructor() { }

  signInWithGoogle(): Observable<void> {
    const provider = new GoogleAuthProvider();
    return from(signInWithRedirect(this.auth, provider));
  }

  getRedirectResult(): Observable<User | null> {
    return from(getRedirectResult(this.auth).then(result => result?.user || null));
  }

  signOut(): Observable<void> {
    return from(this.auth.signOut());
  }

  getCurrentUser(): Observable<User | null> {
    return new Observable(observer => {
      this.auth.onAuthStateChanged(user => {
        observer.next(user);
        observer.complete();
      });
    });
  }

  getIdToken(): Observable<string | null> {
    return new Observable(observer => {
      this.auth.onIdTokenChanged(user => {
        if (user) {
          from(user.getIdToken()).subscribe(token => {
            observer.next(token);
            observer.complete();
          });
        } else {
          observer.next(null);
          observer.complete();
        }
      });
    });
  }
}
