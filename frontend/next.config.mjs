/** @type {import('next').NextConfig} */
const nextConfig = {
  // Webpack configuration for Docker hot reload
  webpack: (config, { dev }) => {
    if (dev) {
      // Optimize for Docker development
      config.watchOptions = {
        poll: 2000, // Poll every 2 seconds
        aggregateTimeout: 600,
        ignored: [
          '**/node_modules/**',
          '**/.git/**',
          '**/.next/**',
          '**/public/**'
        ],
      };
    }
    
    // Disable caching in development
    if (dev) {
      config.cache = false;
    }
    
    return config;
  },

  // Compiler options
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },

  // Transpile packages
  transpilePackages: ['lucide-react'],

  // Output for production (standalone for Docker)
  output: process.env.NODE_ENV === 'production' ? 'standalone' : undefined,

  // Disable telemetry
  telemetry: false,

  // React strict mode
  reactStrictMode: true,

  // Experimental features
  experimental: {
    // Optimize for Docker
    turbotrace: {
      contextDirectory: process.cwd(),
    },
  },
};

export default nextConfig;