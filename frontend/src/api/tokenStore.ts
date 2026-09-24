const STORAGE_KEY = "smart_attendance_token";

let inMemoryToken: string | null = null;

export function getToken(): string | null {
  if (inMemoryToken) return inMemoryToken;
  try {
    inMemoryToken = localStorage.getItem(STORAGE_KEY);
  } catch {
    inMemoryToken = null;
  }
  return inMemoryToken;
}

export function setToken(token: string): void {
  inMemoryToken = token;
  try {
    localStorage.setItem(STORAGE_KEY, token);
  } catch {
    // Storage unavailable (private window, blocked, etc.) -- the in-memory
    // copy still works for the rest of this page load.
  }
}

export function clearToken(): void {
  inMemoryToken = null;
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // ignore
  }
}
