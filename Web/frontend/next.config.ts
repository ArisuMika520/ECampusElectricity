import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  /* config options here */
  // 配置 Turbopack 路径别名和根目录，解决多个 lockfiles 导致的路径解析问题
  turbopack: {
    resolveAlias: {
      "@": path.resolve(__dirname, "."),
    },
    // 明确指定根目录为 frontend 目录，避免检测到多个 lockfiles 时的警告
    root: path.resolve(__dirname, "."),
  },
};

export default nextConfig;
