import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/** @type {import('next').NextConfig} */
const nextConfig = {
  webpack: (config, { dev }) => {
    if (dev) {
      config.watchOptions = {
        poll: 2000,
        aggregateTimeout: 600,
        ignored: [
          '**/node_modules/**',
          '**/.git/**',
          '**/.next/**',
          '**/public/**'
        ],
      };
    }
    
    if (dev) {
      config.cache = false;
    }
    
    return config;
  },

  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },

  transpilePackages: ['lucide-react'],

  reactStrictMode: true,

  output: 'standalone',
  
  outputFileTracingRoot: __dirname,
};

export default nextConfig;