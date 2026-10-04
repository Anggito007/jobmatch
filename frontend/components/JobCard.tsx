"use client";

import type { Match } from "@/lib/api";
import { fmtSalary } from "@/lib/api";

function scoreClass(score: number): string {
  if (score >= 0.4) return "high";
  if (score >= 0.25) return "mid";
  return "low";
}

interface Props {
  m: Match;
  loggedIn: boolean;
  saved: boolean;
  onFeedback: (jobId: string, relevant: boolean) => void;
  onSave: (jobId: string) => void;
}

export default function JobCard({ m, loggedIn, saved, onFeedback, onSave }: Props) {
  const pct = Math.round(m.score * 100);
  const salary = fmtSalary(m);
  const meta = [m.source, m.location, m.job_type, m.work_arrangement].filter(Boolean);

  return (
    <div className="job-card">
      <div className="top">
        <div>
          <h3>{m.title}</h3>
          <div className="company">{m.company}</div>
        </div>
        <div className={`score ${scoreClass(m.score)}`}>
          {pct}
          <span className="pct">cocok</span>
        </div>
      </div>

      {meta.length > 0 && (
        <div className="meta">
          {meta.map((x) => (
            <span className="pill" key={x}>
              {x}
            </span>
          ))}
          {salary && <span className="pill">{salary}</span>}
        </div>
      )}

      {m.matched_skills.length > 0 && (
        <div className="matched">
          Skill cocok: <b>{m.matched_skills.join(", ")}</b>
        </div>
      )}

      <div className="actions">
        <a href={m.url} target="_blank" rel="noreferrer">
          Lihat &amp; Lamar →
        </a>
        {loggedIn && (
          <>
            <button
              className={`btn ghost small${saved ? " saved" : ""}`}
              onClick={() => onSave(m.id)}
              title={saved ? "Tersimpan — klik untuk tandai sudah dilamar" : "Simpan lowongan"}
            >
              {saved ? "★ Tersimpan" : "☆ Simpan"}
            </button>
            <button className="btn ghost small" onClick={() => onFeedback(m.id, true)} title="Relevan">
              👍
            </button>
            <button className="btn ghost small" onClick={() => onFeedback(m.id, false)} title="Tidak relevan">
              👎
            </button>
          </>
        )}
      </div>
    </div>
  );
}
