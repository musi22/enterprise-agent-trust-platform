/** @type {import('next').NextConfig} */
const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

const nextConfig = {
  reactStrictMode: true,
  // Only enable backend API rewrites in local development
  // On Vercel (no NEXT_PUBLIC_API_URL set), rewrites are omitted
  ...(API_URL
    ? {
        async rewrites() {
          return [
            {
              source: "/api/v1/:path*",
              destination: `${API_URL}/api/v1/:path*`,
            },
            {
              source: "/health/:path*",
              destination: `${API_URL}/health/:path*`,
            },
          ];
        },
      }
    : {}),
};

module.exports = nextConfig;
