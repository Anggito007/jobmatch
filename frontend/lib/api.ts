// Klien API untuk backend JobMatch (FastAPI).
// URL backend diambil dari NEXT_PUBLIC_API_URL (default: localhost:8000).

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const TOKEN_KEY = "jobmatch_token";

// --- Token (disimpan di localStorage) ---
export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}
export function setToken(t: string | null) {
  if (typeof window === "undefined") return;
  if (t) localStorage.setItem(TOKEN_KEY, t);
  else localStorage.removeItem(TOKEN_KEY);
}

// --- Tipe ---
export interface Job {
  id: string;
  source: string;
  title: string;
  company: string;
  location: string;
  salary_min: number | null;
  salary_max: number | null;
  currency: string;
  job_type: string;
  work_arrangement: string;
  description: string;
  skills: string[];
  url: string;
  posted_at: string;
}

export interface Match {
  id: string;
  source: string;
  title: string;
  company: string;
  location: string;
  salary_min: number | null;
  salary_max: number | null;
  currency: string;
  job_type: string;
  work_arrangement: string;
  description: string;
  url: string;
  posted_at: string;
  score: number;
  matched_skills: string[];
}

export interface CVProfile {
  skills: string[];
  years_experience: number | null;
  education: string;
  target_role: string;
}

export interface MatchResponse {
  profile: CVProfile;
  count: number;
  pool_size: number;
  keywords: string;
  matches: Match[];
}

export interface SavedJob {
  id: string;
  source: string;
  external_id: string;
  status: string;
  created_at: string;
}

function fmtSalary(j: { salary_min: number | null; salary_max: number | null; currency: string }): string {
  if (j.salary_min == null && j.salary_max == null) return "";
  const cur = j.currency === "IDR" ? "Rp" : j.currency + " ";
  const nf = (n: number) => n.toLocaleString("id-ID", { maximumFractionDigits: 0 });
  if (j.salary_min != null && j.salary_max != null) {
    return `${cur}${nf(j.salary_min)} – ${nf(j.salary_max)}`;
  }
  const v = j.salary_min ?? j.salary_max!;
  return `${cur}${nf(v)}`;
}

export { fmtSalary };

// --- Helper fetch (sertakan token bila ada) ---
async function api(path: string, options: RequestInit = {}): Promise<Response> {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> | undefined),
  };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return fetch(`${API_URL}${path}`, { ...options, headers });
}

async function apiJson<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await api(path, options);
  if (!res.ok) {
    let detail = "";
    try {
      const j = await res.json();
      detail = j.detail || JSON.stringify(j);
    } catch {
      detail = await res.text();
    }
    throw new Error(detail.slice(0, 200));
  }
  return res.json();
}

// --- Matching ---
export async function matchCv(file: File, keywords: string, location: string, topN: number): Promise<MatchResponse> {
  const form = new FormData();
  form.append("file", file);
  form.append("keywords", keywords);
  form.append("location", location);
  form.append("top_n", String(topN));
  return apiJson<MatchResponse>("/api/match", { method: "POST", body: form });
}

export async function refreshJobs(): Promise<{ fetched: number; added: number; updated: number }> {
  return apiJson("/api/jobs/refresh", { method: "POST" });
}

// --- Auth ---
export async function register(email: string, password: string): Promise<{ token: string; email: string }> {
  return apiJson("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
}

export async function login(email: string, password: string): Promise<{ token: string; email: string }> {
  return apiJson("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
}

export async function me(): Promise<{ id: number; email: string }> {
  return apiJson("/api/auth/me");
}

export function logout() {
  setToken(null);
}

// --- Feedback ---
export async function sendFeedback(jobId: string, isRelevant: boolean): Promise<{ action: string }> {
  return apiJson("/api/feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_id: jobId, is_relevant: isRelevant }),
  });
}

// --- Saved jobs ---
export async function saveJob(jobId: string, status: string): Promise<{ action: string }> {
  return apiJson("/api/saved", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_id: jobId, status }),
  });
}

export async function listSaved(): Promise<{ saved: SavedJob[] }> {
  return apiJson("/api/saved");
}

export async function deleteSaved(jobId: string): Promise<{ deleted: boolean }> {
  return apiJson(`/api/saved?job_id=${encodeURIComponent(jobId)}`, { method: "DELETE" });
}
