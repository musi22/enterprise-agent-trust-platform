/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: "http://127.0.0.1:8005/api/v1/:path*",
      },
      {
        source: "/health/:path*",
        destination: "http://127.0.0.1:8005/health/:path*",
      }
    ];
  },
};

module.exports = nextConfig;
