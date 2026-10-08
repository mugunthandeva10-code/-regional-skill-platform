import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth";
import { AppShell } from "@/components/layout";

export const metadata: Metadata = {
  title: "Regional Skill Intelligence Platform",
  description: "Know what skills your market needs. Know what you're missing. Know what to build next.",
  icons: {
    icon: "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><circle cx='30' cy='50' r='20' fill='%23ff8a5c'/><circle cx='50' cy='50' r='20' fill='%232a5696'/><circle cx='70' cy='50' r='20' fill='%230f2440'/></svg>",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="scroll-smooth">
      <body className="font-sans antialiased">
        <AuthProvider>
          <AppShell>{children}</AppShell>
        </AuthProvider>
      </body>
    </html>
  );
}
