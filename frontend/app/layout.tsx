import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "JobMatch — Job Seeker Automation",
  description:
    "Upload CV, pantau lowongan dari JobStreet & Glints, lihat yang cocok secara semantik.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="id">
      <body>{children}</body>
    </html>
  );
}
