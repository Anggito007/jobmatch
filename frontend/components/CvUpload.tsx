"use client";

import { useState } from "react";

interface Props {
  file: File | null;
  onFile: (f: File | null) => void;
}

export default function CvUpload({ file, onFile }: Props) {
  const [drag, setDrag] = useState(false);

  return (
    <div
      className={`upload-zone${drag ? " drag" : ""}`}
      onClick={() => document.getElementById("cv-file")?.click()}
      onDragOver={(e) => {
        e.preventDefault();
        setDrag(true);
      }}
      onDragLeave={() => setDrag(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDrag(false);
        const f = e.dataTransfer.files?.[0];
        if (f) onFile(f);
      }}
    >
      <input
        id="cv-file"
        type="file"
        accept=".pdf,.docx,.txt,.md"
        onChange={(e) => onFile(e.target.files?.[0] ?? null)}
      />
      {file ? (
        <>
          <div className="icon">📄</div>
          <div className="filename">{file.name}</div>
          <div>{(file.size / 1024).toFixed(0)} KB — klik untuk ganti</div>
        </>
      ) : (
        <>
          <div className="icon">📤</div>
          <div>
            <strong>Unggah CV kamu</strong> (PDF, DOCX, TXT)
          </div>
          <div>atau tarik &amp; letakkan file di sini</div>
        </>
      )}
    </div>
  );
}
