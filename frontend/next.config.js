/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Ignorar errores de linter durante el despliegue en Render
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  async rewrites() {
    // In production, the frontend calls the backend API directly via NEXT_PUBLIC_API_URL
    // In development, proxy /api/* to localhost:8000
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
