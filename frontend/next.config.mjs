/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  // Ensure we don't try to use serverless the wrong way
  output: 'standalone',
};

export default nextConfig;
