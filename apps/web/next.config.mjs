const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  output: "standalone",
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "images.unsplash.com" },
      { protocol: "https", hostname: "**.zehno.uz" },
      { protocol: "http", hostname: "localhost" },
      { protocol: "http", hostname: "minio" },
    ],
  },
  eslint: { ignoreDuringBuilds: false },
  experimental: { optimizePackageImports: ["lucide-react", "recharts"] },
};

export default nextConfig;
