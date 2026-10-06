"use client";

import { useEffect, useState } from "react";
import CvUpload from "@/components/CvUpload";
import JobCard from "@/components/JobCard";
import AuthForm from "@/components/AuthForm";
import {
  deleteSaved,
  getToken,
  listSaved,
  logout,
  matchCv,
  me,
  refreshJobs,
  saveJob,
  type MatchResponse,
  type SavedJob,
} from "@/lib/api";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [keywords, setKeywords] = useState("");
  const [location, setLocation] = useState("");
  const [preference, setPreference] = useState("");
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [result, setResult] = useState<MatchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshMsg, setRefreshMsg] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  // Auth state
  const [email, setEmail] = useState<string | null>(null);
  const [savedSet, setSavedSet] = useState<Set<string>>(new Set());
  const [savedList, setSavedList] = useState<SavedJob[]>([]);
  const [showSaved, setShowSaved] = useState(false);

  useEffect(() => {
    if (getToken()) {
      me()
        .then((u) => setEmail(u.email))
        .catch(() => logout());
    }
  }, []);

  useEffect(() => {
    if (email) loadSaved();
  }, [email]);

  async function loadSaved() {
    try {
      const { saved } = await listSaved();
      setSavedList(saved);
      setSavedSet(new Set(saved.map((s) => s.id)));
    } catch {
      // abaikan
    }
  }

  function onAuth(e: string) {
    setEmail(e);
    setNotice(`Selamat datang, ${e}`);
  }

  function onLogout() {
    logout();
    setEmail(null);
    setSavedList([]);
    setSavedSet(new Set());
  }

  async function runMatch() {
    if (!file) {
      setError("Unggah CV dulu.");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await matchCv(file, keywords, location, preference, 30);
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
      setRefreshMsg(`Lowongan diperbarui: ${r.added} baru, ${r.updated} di-update.`);
    } catch (e) {
      setRefreshMsg(e instanceof Error ? e.message : "Refresh gagal.");
    } finally {
      setRefreshing(false);
    }
  }

  async function onFeedback(jobId: string, relevant: boolean) {
    // Feedback dinonaktifkan — user mengumpulkan data label secara manual.
  }

  async function toggleSave(jobId: string) {
    try {
      if (savedSet.has(jobId)) {
        await deleteSaved(jobId);
        setSavedSet((s) => {
          const n = new Set(s);
          n.delete(jobId);
          return n;
        });
        setNotice("Dihapus dari tersimpan.");
      } else {
        await saveJob(jobId, "saved");
        setSavedSet((s) => new Set(s).add(jobId));
        setNotice("Disimpan ★");
      }
      loadSaved();
    } catch (e) {
      setNotice(e instanceof Error ? e.message : "Gagal menyimpan.");
    }
  }

  async function markApplied(jobId: string) {
    try {
      await saveJob(jobId, "applied");
      setNotice("Ditandai sudah dilamar ✅");
      loadSaved();
    } catch (e) {
      setNotice(e instanceof Error ? e.message : "Gagal.");
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
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <div className="badge-sources">
            <span className="on">JobStreet</span>
            <span className="on">Glints</span>
            <span className="on">Dealls</span>
            <span className="on">Kalibrr</span>
            <span className="on">Karir</span>
            <span className="on">TechInAsia</span>
          </div>
          {email ? (
            <div className="auth-state">
              <span className="auth-email">{email}</span>
              <button className="btn ghost small" onClick={() => setShowSaved((v) => !v)}>
                Tersimpan ({savedList.length})
              </button>
              <button className="btn ghost small" onClick={onLogout}>
                Keluar
              </button>
            </div>
          ) : (
            <details className="auth-dropdown">
              <summary className="btn ghost small">Masuk / Daftar</summary>
              <div className="auth-pop">
                <AuthForm onAuth={onAuth} />
              </div>
            </details>
          )}
        </div>
      </header>

      <section className="panel">
        <h2>1. CV &amp; Preferensi</h2>
        <CvUpload file={file} onFile={setFile} />
        <div className="form-row">
          <div className="field">
            <label htmlFor="pref">Posisi / bidang yang kamu incar (opsional)</label>
            <input
              id="pref"
              value={preference}
              onChange={(e) => setPreference(e.target.value)}
              placeholder="mis. IoT Engineer, Embedded, ESP32 — kosongkan untuk mengikuti CV"
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
        {notice && <div className="note">{notice}</div>}
      </section>

      {error && (
        <section className="panel">
          <div className="error">⚠️ {error}</div>
        </section>
      )}

      {showSaved && email && (
        <section className="panel">
          <h2>Lowongan Tersimpan ({savedList.length})</h2>
          {savedList.length === 0 ? (
            <div className="empty">Belum ada lowongan tersimpan.</div>
          ) : (
            <div className="job-list">
              {savedList.map((s) => (
                <div className="job-card" key={s.id}>
                  <div className="top">
                    <div>
                      <h3 style={{ fontSize: 14 }}>{s.id}</h3>
                      <div className="company">
                        status: <b>{s.status === "applied" ? "Sudah dilamar ✅" : "Tersimpan"}</b>
                      </div>
                    </div>
                    <div className="actions">
                      {s.status !== "applied" && (
                        <button className="btn ghost small" onClick={() => markApplied(s.id)}>
                          Tandai dilamar
                        </button>
                      )}
                      <button className="btn ghost small" onClick={() => toggleSave(s.id)}>
                        Hapus
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {result && (
        <section className="panel">
          <h2>2. Hasil ({result.count} lowongan cocok)</h2>
          <div className="result-meta">
            <span className="count">
              {result.count} lowongan paling cocok dari {result.pool_size} lowongan yang
              dipindai (6 sumber).
            </span>
          </div>
          {result.profile && (
            <div className="result-meta profile-line">
              <span className="count">Profil CV:</span>
              {result.profile.target_role && <span className="pill">{result.profile.target_role}</span>}
              {result.profile.years_experience != null && (
                <span className="pill">±{result.profile.years_experience} tahun</span>
              )}
              {result.profile.education && <span className="pill">{result.profile.education}</span>}
            </div>
          )}
          {result.profile.skills.length > 0 && (
            <div className="result-meta">
              <span className="count">Skill terdeteksi:</span>
              <div className="chips">
                {result.profile.skills.map((s) => (
                  <span className="chip" key={s}>
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}
          {result.profile.preference && (
            <div className="result-meta">
              <span className="count">🎯 Target pencarian:</span>
              <div className="chips">
                <span className="chip">{result.profile.preference}</span>
              </div>
            </div>
          )}
          {result.matches.length === 0 ? (
            <div className="empty">Tidak ada lowongan ditemukan. Coba perbarui lowongan.</div>
          ) : (
            <div className="job-list">
              {result.matches.map((m) => (
                <JobCard
                  m={m}
                  key={m.id}
                  loggedIn={!!email}
                  saved={savedSet.has(m.id)}
                  onSave={toggleSave}
                />
              ))}
            </div>
          )}
        </section>
      )}

      {!result && !error && !loading && (
        <section className="panel">
          <div className="empty">
            Unggah CV, lalu klik <strong>Cari Lowongan Cocok</strong>. Backend memindai
            ribuan lowongan dari 6 portal, menghitung kecocokan semantik, lalu
            mengurutkannya. Masuk/daftar untuk menyimpan lowongan.
          </div>
        </section>
      )}
    </div>
  );
}
