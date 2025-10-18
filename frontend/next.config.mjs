/** @type {import('next').NextConfig} */
const nextConfig = {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  webpack: (config) => {
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
  transpilePackages: ['lucide-react'],
  optimizePackageImports: ['lucide-react', '@radix-ui/react-dialog'],
  // Note: Les appels API utilisent maintenant la lib/api.ts avec NEXT_PUBLIC_API_URL
  // Plus de proxy Next.js nécessaire
};

export default nextConfig;
