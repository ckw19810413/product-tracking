import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "數位商品市集 | 繁體中文 AI 工具與模板",
  description: "高品質繁體中文 AI Prompt 庫、AI 實戰課程、飛書模板市集 — 提升你的生產力與創造力",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="zh-TW"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-background">
        {/* Navbar */}
        <header className="fixed top-0 left-0 right-0 z-50 border-b border-card-border bg-background/80 backdrop-blur-md">
          <div className="mx-auto max-w-7xl flex items-center justify-between px-6 py-4">
            <a href="/" className="text-xl font-bold tracking-tight text-foreground">
              <span className="text-primary">✦</span> 數位市集
            </a>
            <nav className="hidden sm:flex items-center gap-8 text-sm text-muted">
              <a href="#hero" className="hover:text-foreground transition-colors">首頁</a>
              <a href="#products" className="hover:text-foreground transition-colors">產品</a>
              <a
                href="https://github.com/ckw19810413"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-foreground transition-colors"
              >
                GitHub ⟶
              </a>
            </nav>
            <a
              href="#products"
              className="rounded-full bg-primary px-5 py-2 text-sm font-medium text-white transition-all hover:bg-primary-hover"
            >
              探索產品
            </a>
          </div>
        </header>

        {/* Main content */}
        <main className="flex-1 pt-16">{children}</main>

        {/* Footer */}
        <footer className="border-t border-card-border bg-card-bg/50">
          <div className="mx-auto max-w-7xl px-6 py-12">
            <div className="flex flex-col items-center gap-6 sm:flex-row sm:justify-between">
              <div className="text-center sm:text-left">
                <span className="text-lg font-bold text-foreground">
                  <span className="text-primary">✦</span> 數位市集
                </span>
                <p className="mt-1 text-sm text-muted">
                  繁體中文數位商品 — 提升你的生產力與創造力
                </p>
              </div>
              <div className="flex flex-col items-center gap-2 text-sm text-muted sm:items-end">
                <a
                  href="https://github.com/ckw19810413/traditional-ai-prompt-library"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-foreground transition-colors"
                >
                  AI Prompt 庫
                </a>
                <a
                  href="https://github.com/ckw19810413/ai-practical-course-tw"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-foreground transition-colors"
                >
                  AI 實戰課程
                </a>
                <a
                  href="https://github.com/ckw19810413/feishu-template-marketplace"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-foreground transition-colors"
                >
                  飛書模板市集
                </a>
              </div>
            </div>
            <div className="mt-8 border-t border-card-border pt-6 text-center text-xs text-muted">
              © {new Date().getFullYear()} 數位市集. All rights reserved.
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
