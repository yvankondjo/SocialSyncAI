/** @type {import('next').NextConfig} */
const nextConfig = {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  webpack: (config: any) => {
    config.watchOptions = {
      poll: 2000, // Réduire la fréquence de polling
      aggregateTimeout: 600, // Augmenter l'agrégation
      ignored: ['**/node_modules/**', '**/.git/**', '**/.next/**'],
    };
    // Optimisations pour Docker
    config.cache = false;
    return config;
  },
  // Optimisations générales
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
  experimental: {
    optimizePackageImports: ['lucide-react', '@radix-ui/react-dialog'],
  },
};

export default nextConfig;
