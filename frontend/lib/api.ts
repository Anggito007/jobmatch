// Klien API untuk backend JobMatch (FastAPI).
// URL backend diambil dari NEXT_PUBLIC_API_URL (default: localhost:8000).

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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

export interface MatchResponse {
  cv_skills: string[];
  count: number;
  pool_size: number;
  keywords: string;
  matches: Match[];
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

export async function matchCv(
  file: File,
  keywords: string,
  location: string,
  topN: number,
): Promise<MatchResponse> {
  const form = new FormData();
  form.append("file", file);
  form.append("keywords", keywords);
  form.append("location", location);
  form.append("top_n", String(topN));

  const res = await fetch(`${API_URL}/api/match`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Match gagal (${res.status}): ${detail.slice(0, 200)}`);
  }
  return res.json();
}

export async function refreshJobs(): Promise<{ fetched: number; added: number; updated: number }> {
  const res = await fetch(`${API_URL}/api/jobs/refresh`, { method: "POST" });
  if (!res.ok) throw new Error(`Refresh gagal (${res.status})`);
  return res.json();
}
