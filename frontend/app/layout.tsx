/** layout 파일은 Next.js 페이지와 레이아웃 기능을 담당한다. */

import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";

/** `metadata`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export const metadata: Metadata = {
  title: "StockPilot AI",
  description: "투자 의사결정 지원 플랫폼",
};

/** `RootLayout`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="ko" className="scroll-smooth"><body className="min-h-screen font-sans antialiased"><Providers>{children}</Providers></body></html>;
}
