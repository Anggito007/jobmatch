"use client";

import { useState } from "react";
import type { JobFilters } from "@/lib/filters";
import {
  CURRENCIES,
  EDUCATION_LEVELS,
  JOB_TYPES,
  POPULAR_LOCATIONS,
  POSITION_LEVELS,
  SORT_OPTIONS,
  SPECIALIZATIONS,
  labelOf,
} from "@/lib/filters";

interface Props {
  filters: JobFilters;
  onChange: (f: JobFilters) => void;
  onApply: () => void;
  onClear: () => void;
  applying?: boolean;
}

function toggleIn(arr: string[], v: string): string[] {
  return arr.includes(v) ? arr.filter((x) => x !== v) : [...arr, v];
}

/* ------------------------------------------------------------------ */
/* Dropdown multi-select generik                                       */
/* ------------------------------------------------------------------ */

function MultiDropdown({
  label,
  options,
  selected,
  onToggle,
}: {
  label: string;
  options: { value: string; label: string }[];
  selected: string[];
  onToggle: (v: string) => void;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div className="dd">
      <button
        className={`dd-btn${open ? " open" : ""}${selected.length ? " has-val" : ""}`}
        onClick={() => setOpen((v) => !v)}
      >
        {label}
        {selected.length > 0 && <span className="dd-count">{selected.length}</span>}
        <span className="chev">▾</span>
      </button>
      {open && (
        <>
          <div className="dd-backdrop" onClick={() => setOpen(false)} />
          <div className="dd-panel">
            {options.map((o) => (
              <label className="dd-item" key={o.value}>
                <input
                  type="checkbox"
                  checked={selected.includes(o.value)}
                  onChange={() => onToggle(o.value)}
                />
                <span>{o.label}</span>
              </label>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Lokasi — search + kota populer + Anywhere/Remote                    */
/* ------------------------------------------------------------------ */

function LocationFilter({ filters, onChange }: { filters: JobFilters; onChange: (f: JobFilters) => void }) {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const locs = filters.locations.filter((x) => x !== "remote");
  const anywhere = filters.locations.length === 0;

  function addLoc(v: string) {
    const s = v.trim();
    if (!s) return;
    if (!locs.some((x) => x.toLowerCase() === s.toLowerCase())) {
      onChange({ ...filters, locations: [...locs, s] });
    }
    setQ("");
  }

  return (
    <div className="dd">
      <button
        className={`dd-btn${open ? " open" : ""}${locs.length ? " has-val" : ""}`}
        onClick={() => setOpen((v) => !v)}
      >
        Lokasi
        {locs.length > 0 && <span className="dd-count">{locs.length}</span>}
        <span className="chev">▾</span>
      </button>
      {open && (
        <>
          <div className="dd-backdrop" onClick={() => setOpen(false)} />
          <div className="dd-panel dd-panel--wide">
            <div className="dd-search">
              <input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Ketik kota / provinsi / negara…"
                onKeyDown={(e) => {
                  if (e.key === "Enter") addLoc(q);
                }}
              />
              <button className="dd-add" onClick={() => addLoc(q)}>
                Tambah
              </button>
            </div>

            <label className="dd-item">
              <input
                type="checkbox"
                checked={anywhere}
                onChange={() => onChange({ ...filters, locations: [] })}
              />
              <span>🌍 Anywhere / Remote</span>
            </label>

            <div className="dd-section-title">Kota populer</div>
            <div className="dd-chips">
              {POPULAR_LOCATIONS.map((c) => {
                const on = locs.some((x) => x.toLowerCase() === c.toLowerCase());
                return (
                  <button
                    key={c}
                    className={`dd-chip${on ? " on" : ""}`}
                    onClick={() =>
                      onChange({
                        ...filters,
                        locations: on
                          ? locs.filter((x) => x.toLowerCase() !== c.toLowerCase())
                          : [...locs, c],
                      })
                    }
                  >
                    {c}
                  </button>
                );
              })}
            </div>

            {locs.length > 0 && (
              <div className="dd-selected">
                {locs.map((c) => (
                  <span className="tag" key={c}>
                    {c}
                    <button onClick={() => onChange({ ...filters, locations: locs.filter((x) => x !== c) })}>
                      ×
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Perusahaan — cari & pilih (prefer + kecualikan)                     */
/* ------------------------------------------------------------------ */

function CompanyFilter({ filters, onChange }: { filters: JobFilters; onChange: (f: JobFilters) => void }) {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [exclQ, setExclQ] = useState("");

  function addPref(v: string) {
    const s = v.trim();
    if (!s) return;
    if (!filters.preferred_companies.some((x) => x.toLowerCase() === s.toLowerCase())) {
      onChange({ ...filters, preferred_companies: [...filters.preferred_companies, s] });
    }
    setQ("");
  }
  function addExcl(v: string) {
    const s = v.trim();
    if (!s) return;
    if (!filters.excluded_companies.some((x) => x.toLowerCase() === s.toLowerCase())) {
      onChange({ ...filters, excluded_companies: [...filters.excluded_companies, s] });
    }
    setExclQ("");
  }

  const n = filters.preferred_companies.length + filters.excluded_companies.length;
  return (
    <div className="dd">
      <button
        className={`dd-btn${open ? " open" : ""}${n ? " has-val" : ""}`}
        onClick={() => setOpen((v) => !v)}
      >
        Perusahaan
        {n > 0 && <span className="dd-count">{n}</span>}
        <span className="chev">▾</span>
      </button>
      {open && (
        <>
          <div className="dd-backdrop" onClick={() => setOpen(false)} />
          <div className="dd-panel dd-panel--wide">
            <div className="dd-section-title">Perusahaan pilihan</div>
            <div className="dd-search">
              <input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Cari & tambah perusahaan…"
                onKeyDown={(e) => e.key === "Enter" && addPref(q)}
              />
              <button className="dd-add" onClick={() => addPref(q)}>
                Tambah
              </button>
            </div>
            {filters.preferred_companies.length > 0 && (
              <div className="dd-selected">
                {filters.preferred_companies.map((c) => (
                  <span className="tag tag--good" key={c}>
                    {c}
                    <button
                      onClick={() =>
                        onChange({
                          ...filters,
                          preferred_companies: filters.preferred_companies.filter((x) => x !== c),
                        })
                      }
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            )}

            <div className="dd-section-title">Kecualikan perusahaan</div>
            <div className="dd-search">
              <input
                value={exclQ}
                onChange={(e) => setExclQ(e.target.value)}
                placeholder="Perusahaan yang dihindari…"
                onKeyDown={(e) => e.key === "Enter" && addExcl(exclQ)}
              />
              <button className="dd-add" onClick={() => addExcl(exclQ)}>
                Tambah
              </button>
            </div>
            {filters.excluded_companies.length > 0 && (
              <div className="dd-selected">
                {filters.excluded_companies.map((c) => (
                  <span className="tag tag--bad" key={c}>
                    {c}
                    <button
                      onClick={() =>
                        onChange({
                          ...filters,
                          excluded_companies: filters.excluded_companies.filter((x) => x !== c),
                        })
                      }
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Gaji — min/max + mata uang + "belum dicantumkan"                    */
/* ------------------------------------------------------------------ */

function SalaryFilter({ filters, onChange }: { filters: JobFilters; onChange: (f: JobFilters) => void }) {
  const [open, setOpen] = useState(false);
  const hasVal = filters.min_salary != null || filters.max_salary != null;
  return (
    <div className="dd">
      <button
        className={`dd-btn${open ? " open" : ""}${hasVal ? " has-val" : ""}`}
        onClick={() => setOpen((v) => !v)}
      >
        Gaji
        <span className="chev">▾</span>
      </button>
      {open && (
        <>
          <div className="dd-backdrop" onClick={() => setOpen(false)} />
          <div className="dd-panel">
            <div className="dd-salary-row">
              <input
                type="number"
                min={0}
                placeholder="Min"
                value={filters.min_salary ?? ""}
                onChange={(e) =>
                  onChange({
                    ...filters,
                    min_salary: e.target.value === "" ? null : Number(e.target.value),
                  })
                }
              />
              <span className="dd-dash">–</span>
              <input
                type="number"
                min={0}
                placeholder="Max"
                value={filters.max_salary ?? ""}
                onChange={(e) =>
                  onChange({
                    ...filters,
                    max_salary: e.target.value === "" ? null : Number(e.target.value),
                  })
                }
              />
            </div>
            <select
              className="dd-select"
              value={filters.salary_currency}
              onChange={(e) => onChange({ ...filters, salary_currency: e.target.value })}
            >
              {CURRENCIES.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
            <label className="dd-item">
              <input
                type="checkbox"
                checked={filters.salary_not_specified}
                onChange={(e) => onChange({ ...filters, salary_not_specified: e.target.checked })}
              />
              <span>Sertakan lowongan tanpa info gaji</span>
            </label>
          </div>
        </>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Sort — single select                                                */
/* ------------------------------------------------------------------ */

function SortFilter({ filters, onChange }: { filters: JobFilters; onChange: (f: JobFilters) => void }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="dd">
      <button className={`dd-btn dd-btn--box${open ? " open" : ""}`} onClick={() => setOpen((v) => !v)}>
        Urutkan: {labelOf(SORT_OPTIONS, filters.sort_by)}
        <span className="chev">▾</span>
      </button>
      {open && (
        <>
          <div className="dd-backdrop" onClick={() => setOpen(false)} />
          <div className="dd-panel">
            {SORT_OPTIONS.map((o) => (
              <label className="dd-item" key={o.value}>
                <input
                  type="radio"
                  name="sort"
                  checked={filters.sort_by === o.value}
                  onChange={() => {
                    onChange({ ...filters, sort_by: o.value });
                    setOpen(false);
                  }}
                />
                <span>{o.label}</span>
              </label>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Toggle pill                                                         */
/* ------------------------------------------------------------------ */

function Toggle({
  label,
  on,
  onToggle,
}: {
  label: string;
  on: boolean;
  onToggle: () => void;
}) {
  return (
    <button className={`toggle${on ? " on" : ""}`} onClick={onToggle}>
      <span className="toggle-label">{label}</span>
      <span className="track">
        <span className="knob" />
      </span>
    </button>
  );
}

/* ------------------------------------------------------------------ */
/* FilterBar utama                                                     */
/* ------------------------------------------------------------------ */

export default function FilterBar({ filters, onChange, onApply, onClear, applying }: Props) {
  // Chip terpilih (ringkasan, bisa dihapus).
  const chips: { key: string; text: string; remove: () => void }[] = [];

  filters.locations
    .filter((x) => x !== "remote")
    .forEach((l) => chips.push({ key: `loc:${l}`, text: l, remove: () => onChange({ ...filters, locations: filters.locations.filter((x) => x !== l) }) }));

  filters.position_levels.forEach((v) =>
    chips.push({
      key: `pl:${v}`,
      text: labelOf(POSITION_LEVELS, v),
      remove: () => onChange({ ...filters, position_levels: filters.position_levels.filter((x) => x !== v) }),
    })
  );
  filters.job_types.forEach((v) =>
    chips.push({
      key: `jt:${v}`,
      text: labelOf(JOB_TYPES, v),
      remove: () => onChange({ ...filters, job_types: filters.job_types.filter((x) => x !== v) }),
    })
  );
  filters.specializations.forEach((v) =>
    chips.push({
      key: `sp:${v}`,
      text: labelOf(SPECIALIZATIONS, v),
      remove: () => onChange({ ...filters, specializations: filters.specializations.filter((x) => x !== v) }),
    })
  );
  filters.education_levels.forEach((v) =>
    chips.push({
      key: `ed:${v}`,
      text: labelOf(EDUCATION_LEVELS, v),
      remove: () => onChange({ ...filters, education_levels: filters.education_levels.filter((x) => x !== v) }),
    })
  );
  filters.preferred_companies.forEach((c) =>
    chips.push({
      key: `pc:${c}`,
      text: `Perusahaan: ${c}`,
      remove: () => onChange({ ...filters, preferred_companies: filters.preferred_companies.filter((x) => x !== c) }),
    })
  );
  filters.excluded_companies.forEach((c) =>
    chips.push({
      key: `ec:${c}`,
      text: `Kecuali: ${c}`,
      remove: () => onChange({ ...filters, excluded_companies: filters.excluded_companies.filter((x) => x !== c) }),
    })
  );
  if (filters.min_salary != null || filters.max_salary != null) {
    const cur = filters.salary_currency || "IDR";
    const nf = (n: number) => n.toLocaleString("id-ID", { maximumFractionDigits: 0 });
    const text =
      filters.min_salary != null && filters.max_salary != null
        ? `Gaji ${cur} ${nf(filters.min_salary)} – ${nf(filters.max_salary)}`
        : filters.min_salary != null
          ? `Gaji ≥ ${cur} ${nf(filters.min_salary)}`
          : `Gaji ≤ ${cur} ${nf(filters.max_salary!)}`;
    chips.push({ key: "salary", text, remove: () => onChange({ ...filters, min_salary: null, max_salary: null }) });
  }
  const toggleChips: [boolean, string, () => void][] = [
    [filters.remote, "Work From Home", () => onChange({ ...filters, remote: !filters.remote })],
    [filters.hybrid, "Hybrid", () => onChange({ ...filters, hybrid: !filters.hybrid })],
    [filters.work_abroad, "Work Abroad", () => onChange({ ...filters, work_abroad: !filters.work_abroad })],
    [filters.fresh_graduate, "Fresh Graduate", () => onChange({ ...filters, fresh_graduate: !filters.fresh_graduate })],
    [filters.quick_response, "Quick Response", () => onChange({ ...filters, quick_response: !filters.quick_response })],
  ];
  toggleChips.forEach(([on, label, toggle]) => {
    if (on) chips.push({ key: `tg:${label}`, text: label, remove: toggle });
  });

  const hasAny = chips.length > 0;

  return (
    <div className="filter-bar">
      <div className="filter-row">
        <LocationFilter filters={filters} onChange={onChange} />
        <MultiDropdown
          label="Level Posisi"
          options={POSITION_LEVELS}
          selected={filters.position_levels}
          onToggle={(v) => onChange({ ...filters, position_levels: toggleIn(filters.position_levels, v) })}
        />
        <MultiDropdown
          label="Tipe Kerja"
          options={JOB_TYPES}
          selected={filters.job_types}
          onToggle={(v) => onChange({ ...filters, job_types: toggleIn(filters.job_types, v) })}
        />
        <MultiDropdown
          label="Spesialisasi"
          options={SPECIALIZATIONS}
          selected={filters.specializations}
          onToggle={(v) => onChange({ ...filters, specializations: toggleIn(filters.specializations, v) })}
        />
        <MultiDropdown
          label="Pendidikan"
          options={EDUCATION_LEVELS}
          selected={filters.education_levels}
          onToggle={(v) => onChange({ ...filters, education_levels: toggleIn(filters.education_levels, v) })}
        />
        <CompanyFilter filters={filters} onChange={onChange} />
        <SalaryFilter filters={filters} onChange={onChange} />
      </div>

      <div className="filter-row filter-row--2">
        <SortFilter filters={filters} onChange={onChange} />
        <Toggle label="Work From Home" on={filters.remote} onToggle={() => onChange({ ...filters, remote: !filters.remote })} />
        <Toggle label="Hybrid" on={filters.hybrid} onToggle={() => onChange({ ...filters, hybrid: !filters.hybrid })} />
        <Toggle label="Work Abroad" on={filters.work_abroad} onToggle={() => onChange({ ...filters, work_abroad: !filters.work_abroad })} />
        <Toggle label="Fresh Graduate" on={filters.fresh_graduate} onToggle={() => onChange({ ...filters, fresh_graduate: !filters.fresh_graduate })} />
        <Toggle label="Quick Response" on={filters.quick_response} onToggle={() => onChange({ ...filters, quick_response: !filters.quick_response })} />
        <div className="filter-actions">
          {hasAny && (
            <button className="btn ghost small" onClick={onClear}>
              Bersihkan Semua
            </button>
          )}
          <button className="btn small" onClick={onApply} disabled={applying}>
            {applying ? "Menerapkan…" : "Terapkan Filter"}
          </button>
        </div>
      </div>

      {hasAny && (
        <div className="filter-chips">
          {chips.map((c) => (
            <span className="chip chip--x" key={c.key}>
              {c.text}
              <button onClick={c.remove} aria-label="Hapus">
                ×
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
