"use client";

import { useState } from "react";
import CvUpload from "@/components/CvUpload";
import JobCard from "@/components/JobCard";
import { matchCv, refreshJobs, type MatchResponse } from "@/lib/api";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [keywords, setKeywords] = useState("backend engineer");
  const [location, setLocation] = useState("");
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [result, setResult] = useState<MatchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshMsg, setRefreshMsg] = useState<string | null>(null);

  async function runMatch() {
    if (!file) {
      setError("Unggah CV dulu.");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await matchCv(file, keywords, location, 30);
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Terjadi kesalahan.");
    } finally {
      setLoading(false);
    }
  }

  async function runRefresh() {
    setRefreshing(true);
    setRefreshMsg(null);
    try {
      const r = await refreshJobs();
      setRefreshMsg(
        `Lowongan diperbarui: ${r.added} baru, ${r.updated} di-update.`,
      );
    } catch (e) {
      setRefreshMsg(e instanceof Error ? e.message : "Refresh gagal.");
    } finally {
      setRefreshing(false);
    }
  }

  return (
    <div className="container">
      <header className="header">
        <div className="brand">
          <div className="logo">J</div>
          <div>
            <h1>JobMatch</h1>
            <div className="tag">Job seeker automation — CV → lowongan yang cocok</div>
          </div>
        </div>
        <div className="badge-sources">
          <span className="on">JobStreet</span>
          <span className="on">Glints</span>
        </div>
      </header>

      <section className="panel">
        <h2>1. CV &amp; Preferensi</h2>
        <CvUpload file={file} onFile={setFile} />
        <div className="form-row">
          <div className="field">
            <label htmlFor="kw">Kata kunci lowongan</label>
            <input
              id="kw"
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
              placeholder="mis. backend engineer"
            />
          </div>
          <div className="field">
            <label htmlFor="loc">Lokasi (opsional)</label>
            <input
              id="loc"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="mis. Bandung"
            />
          </div>
        </div>
        <div className="form-row">
          <button className="btn" onClick={runMatch} disabled={loading || !file}>
            {loading ? (
              <>
                <span className="spinner" /> Mencari kecocokan…
              </>
            ) : (
              "🔍 Cari Lowongan Cocok"
            )}
          </button>
          <button className="btn ghost" onClick={runRefresh} disabled={refreshing}>
            {refreshing ? "Memperbarui…" : "↻ Perbarui lowongan"}
          </button>
        </div>
        {refreshMsg && <div className="note">{refreshMsg}</div>}
      </section>

      {error && (
        <section className="panel">
          <div className="error">⚠️ {error}</div>
        </section>
      )}

      {result && (
        <section className="panel">
          <h2>2. Hasil ({result.count} lowongan)</h2>
          <div className="result-meta">
            <span className="count">
              {result.count} lowongan diurutkan berdasarkan kecocokan
            </span>
          </div>
          {result.cv_skills.length > 0 && (
            <div className="result-meta">
              <span className="count">Skill terdeteksi dari CV:</span>
              <div className="chips">
                {result.cv_skills.map((s) => (
                  <span className="chip" key={s}>
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}
          {result.matches.length === 0 ? (
            <div className="empty">
              Tidak ada lowongan ditemukan. Coba ubah kata kunci atau perbarui
              lowongan.
            </div>
          ) : (
            <div className="job-list">
              {result.matches.map((m) => (
                <JobCard m={m} key={m.id} />
              ))}
            </div>
          )}
        </section>
      )}

      {!result && !error && !loading && (
        <section className="panel">
          <div className="empty">
            Unggah CV, atur kata kunci, lalu klik{" "}
            <strong>Cari Lowongan Cocok</strong>. Backend akan menarik lowongan
            live dari JobStreet &amp; Glints, menghitung kecocokan semantik, dan
            mengurutkannya.
          </div>
        </section>
      )}
    </div>
  );
}
