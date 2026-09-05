/** @type {import('next').NextConfig} */
const backend = process.env.API_PROXY_TARGET || "http://localhost:8000";

const nextConfig = {
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${backend}/:path*` }];
  },
};

export default nextConfig;
