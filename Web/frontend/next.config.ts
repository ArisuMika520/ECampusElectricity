import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // Turbopack 会自动读取 tsconfig.json 中的 paths 配置
  // 无需额外配置 webpack 或 turbopack
};

export default nextConfig;
