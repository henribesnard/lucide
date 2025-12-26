import type { Metadata } from "next";
import Script from "next/script";
import { Space_Grotesk, IBM_Plex_Sans } from "next/font/google";
import { ThemeProvider } from "@/components/ThemeProvider";
import { LanguageProvider } from "@/contexts/LanguageContext";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import "./globals.css";

const plexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  variable: "--font-plex",
  display: "swap",
  weight: ["400", "500", "600", "700"],
});

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space",
  display: "swap",
  weight: ["500", "600", "700"],
});

export const metadata: Metadata = {
  title: "STATOS",
  description: "STATOS est la plateforme professionnelle d'analyse et de performance football.",
  icons: {
    icon: "/statos-s.svg",
    apple: "/statos-s.svg",
  },
};

const themeScript = `
(function () {
  try {
    var key = "statos-theme-preference";
    var stored = localStorage.getItem(key);
    var preference = stored === "light" || stored === "dark" || stored === "auto" ? stored : "auto";
    var mql = window.matchMedia("(prefers-color-scheme: dark)");
    var resolved = preference === "auto" ? (mql.matches ? "dark" : "light") : preference;
    var root = document.documentElement;
    root.dataset.theme = resolved;
    root.dataset.themePreference = preference;
    root.style.colorScheme = resolved;
  } catch (e) {}
})();
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr" data-theme="light" suppressHydrationWarning>
      <body className={`${plexSans.variable} ${spaceGrotesk.variable} bg-app text-ink`}>
        <Script id="theme-init" strategy="beforeInteractive">
          {themeScript}
        </Script>
        <ThemeProvider>
          <LanguageProvider>
            <ErrorBoundary>
              {children}
            </ErrorBoundary>
          </LanguageProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
