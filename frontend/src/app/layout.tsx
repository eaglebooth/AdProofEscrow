import type { Metadata } from "next";
import "./globals.css";
import { WalletProvider } from "@/components/WalletProvider";
import { SiteShell } from "@/components/SiteShell";
export const metadata: Metadata = { title: "AdProofEscrow V2", description: "Funded creator campaigns settled by public proof on GenLayer." };
export default function RootLayout({ children }: { children: React.ReactNode }) { return <html lang="en"><body><WalletProvider><SiteShell>{children}</SiteShell></WalletProvider></body></html>; }
