// Tipe, opsi, dan nilai default untuk filter/preferensi pencarian lowongan.
// Nilai kanonik (value) harus cocok dengan backend `app/preferences.py`.

export interface JobFilters {
  locations: string[];
  position_levels: string[];
  job_types: string[];
  specializations: string[];
  education_levels: string[];
  preferred_companies: string[];
  excluded_companies: string[];
  min_salary: number | null;
  max_salary: number | null;
  salary_currency: string;
  salary_not_specified: boolean;
  remote: boolean;
  hybrid: boolean;
  work_abroad: boolean;
  fresh_graduate: boolean;
  quick_response: boolean;
  sort_by: string;
}

export interface Option {
  value: string;
  label: string;
}

export const POSITION_LEVELS: Option[] = [
  { value: "internship", label: "Internship" },
  { value: "fresh_graduate", label: "Fresh Graduate" },
  { value: "entry", label: "Entry Level" },
  { value: "junior", label: "Junior" },
  { value: "mid", label: "Mid Level" },
  { value: "senior", label: "Senior" },
  { value: "manager", label: "Manager" },
];

export const JOB_TYPES: Option[] = [
  { value: "full_time", label: "Full-time" },
  { value: "part_time", label: "Part-time" },
  { value: "contract", label: "Contract" },
  { value: "internship", label: "Internship" },
  { value: "freelance", label: "Freelance" },
  { value: "temporary", label: "Temporary" },
];

export const SPECIALIZATIONS: Option[] = [
  { value: "software_engineering", label: "Software Engineering" },
  { value: "network_engineering", label: "Network Engineering" },
  { value: "it_support", label: "IT Support" },
  { value: "data_science", label: "Data Science" },
  { value: "cybersecurity", label: "Cybersecurity" },
  { value: "ui_ux", label: "UI/UX" },
  { value: "marketing", label: "Marketing" },
  { value: "finance", label: "Finance" },
  { value: "business", label: "Business" },
  { value: "engineering", label: "Engineering" },
];

export const EDUCATION_LEVELS: Option[] = [
  { value: "high_school", label: "High School / SMK" },
  { value: "diploma", label: "Diploma (D3)" },
  { value: "bachelor", label: "Bachelor (S1)" },
  { value: "master", label: "Master (S2)" },
  { value: "doctorate", label: "Doctorate (S3)" },
  { value: "any", label: "No specific requirement" },
];

export const SORT_OPTIONS: Option[] = [
  { value: "relevance", label: "Relevance" },
  { value: "latest", label: "Latest" },
  { value: "salary_desc", label: "Salary: Highest → Lowest" },
  { value: "salary_asc", label: "Salary: Lowest → Highest" },
  { value: "match_score", label: "Match Score: Highest → Lowest" },
];

export const CURRENCIES: Option[] = [
  { value: "", label: "Any currency" },
  { value: "IDR", label: "IDR (Rp)" },
  { value: "USD", label: "USD ($)" },
  { value: "SGD", label: "SGD (S$)" },
  { value: "EUR", label: "EUR (€)" },
];

export const POPULAR_LOCATIONS = [
  "Jakarta", "Bandung", "Surabaya", "Yogyakarta", "Semarang", "Tangerang",
  "Depok", "Bekasi", "Medan", "Makassar", "Denpasar", "Bali", "Indonesia",
];

export const EMPTY_FILTERS: JobFilters = {
  locations: [],
  position_levels: [],
  job_types: [],
  specializations: [],
  education_levels: [],
  preferred_companies: [],
  excluded_companies: [],
  min_salary: null,
  max_salary: null,
  salary_currency: "",
  // Default true: sebagian besar lowongan tidak mencantumkan gaji — kalau ini
  // false, filter gaji minimum akan membuang hampir seluruh pool.
  salary_not_specified: true,
  remote: false,
  hybrid: false,
  work_abroad: false,
  fresh_graduate: false,
  quick_response: false,
  sort_by: "relevance",
};

// Label tampil untuk nilai kanonik (dipakai chip + alasan).
export function labelOf(group: Option[], value: string): string {
  return group.find((o) => o.value === value)?.label ?? value;
}

// Salinan dalam untuk mencegah mutasi tak sengaja.
export function cloneFilters(f: JobFilters): JobFilters {
  return JSON.parse(JSON.stringify(f));
}
