import type { NextConfig } from "next";

const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(), payment=()" },
  {
    key: "Content-Security-Policy",
    value: "object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'",
  },
];

const configuredDistDir = process.env.STOCKPILOT_NEXT_DIST_DIR?.trim();
const isolatedDistDir = configuredDistDir && /^\.[a-zA-Z0-9_-]+$/.test(configuredDistDir)
  ? configuredDistDir
  : undefined;
const isValidationBuild = process.env.STOCKPILOT_NEXT_BUILD_VALIDATION === "true";

const nextConfig: NextConfig = {
  ...(isolatedDistDir ? { distDir: isolatedDistDir } : {}),
  ...(isValidationBuild ? {} : { output: "standalone" as const }),
  outputFileTracingRoot: process.cwd().replace(/[\\/]apps[\\/]web$/, ""),
  async headers() {
    return [
      { source: "/:path*", headers: securityHeaders },
      {
        source: "/admin/:path*",
        headers: [{ key: "Cache-Control", value: "no-store, private" }],
      },
      {
        source: "/api/admin/:path*",
        headers: [{ key: "Cache-Control", value: "no-store, private" }],
      },
    ];
  },
};

export default nextConfig;
