"use client";

/** providers 파일은 Next.js 페이지와 레이아웃 기능을 담당한다. */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

/** `Providers`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: { staleTime: 30_000, retry: 1, refetchOnWindowFocus: false },
    },
  }));

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
