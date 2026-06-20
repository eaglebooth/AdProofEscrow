import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AdProof Escrow - Creator Campaign Settlement",
  description: "GenLayer-native escrow for AI-reviewed creator marketing deliverables.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
