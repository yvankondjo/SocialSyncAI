/** @type {import('next').NextConfig} */
const nextConfig = {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  webpack: (config: any) => {
    config.watchOptions = {
      poll: 1000,
      aggregateTimeout: 300,
    };
    return config;
  },
};

export default nextConfig;
