import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";
import { ThemeToggle } from "@/components/theme-toggle";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Handout to Calendar",
  description: "AI-powered schedule extractor from university handouts.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      suppressHydrationWarning
    >
      <body className="min-h-screen flex flex-col bg-background text-foreground">
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="container flex h-14 items-center px-4 md:px-8 max-w-7xl mx-auto justify-between">
              <div className="font-bold text-lg">📅 Handout2Calendar</div>
              <ThemeToggle />
            </div>
          </header>
          
          <main className="flex-1 w-full max-w-7xl mx-auto px-4 md:px-8 py-8">
            {children}
          </main>

          <footer className="border-t py-6 md:py-0">
            <div className="container flex flex-col items-center justify-center gap-4 md:h-16 md:flex-row max-w-7xl mx-auto px-4 md:px-8">
              <p className="text-sm leading-loose text-center text-muted-foreground">
                &copy; 2026 Vaiebhav - aka - BlazingFire27. All rights reserved.
              </p>
            </div>
          </footer>
        </ThemeProvider>
      </body>
    </html>
  );
}
