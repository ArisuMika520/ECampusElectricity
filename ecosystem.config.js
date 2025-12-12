/**
 * PM2 生态系统配置文件
 * 用于管理 Web 后端、Web 前端、Tracker 和 Bot 服务
 * 
 * 安装 PM2:
 *   npm install -g pm2
 * 
 * 使用方法:
 *   pm2 start ecosystem.config.js                    # 启动所有服务
 *   pm2 start ecosystem.config.js --only web-backend # 只启动后端
 *   pm2 start ecosystem.config.js --only web-frontend # 只启动前端
 *   pm2 start ecosystem.config.js --only tracker     # 只启动 Tracker
 *   pm2 start ecosystem.config.js --only bot         # 只启动 Bot
 *   pm2 stop all                                     # 停止所有服务
 *   pm2 restart all                                  # 重启所有服务
 *   pm2 logs                                         # 查看所有日志
 *   pm2 logs web-backend                             # 查看后端日志
 *   pm2 monit                                        # 监控面板
 *   pm2 save                                         # 保存当前进程列表
 *   pm2 startup                                      # 设置开机自启
 * 
 * 注意事项:
 *   1. 首次运行前，确保已执行 npm run setup（Web 版本）
 *   2. 确保已配置根目录 .env 文件（或使用 bash scripts/init-config.sh）
 *   3. 确保数据库已初始化（npm run db:init）
 *   4. Web 前端需要先构建（npm run build）
 */

module.exports = {
  apps: [
    // Web 后端 (FastAPI)
    {
      name: 'web-backend',
      script: './scripts/pm2-start-backend.sh',
      cwd: './',
      interpreter: 'bash',
      instances: 1,
      exec_mode: 'fork',
      env: {
        NODE_ENV: 'production',
        PYTHONUNBUFFERED: '1',
      },
      error_file: './logs/pm2/web-backend-error.log',
      out_file: './logs/pm2/web-backend-out.log',
      log_file: './logs/pm2/web-backend.log',
      time: true,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      merge_logs: true,
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      // 等待后端启动
      wait_ready: false,
      listen_timeout: 30000,
    },

    // Web 前端 (Next.js)
    {
      name: 'web-frontend',
      script: './scripts/pm2-start-frontend.sh',
      cwd: './',
      interpreter: 'bash',
      instances: 1,
      exec_mode: 'fork',
      env: {
        NODE_ENV: 'production',
        PORT: 3000,
        NEXT_PUBLIC_API_URL: 'http://localhost:8000',
      },
      error_file: './logs/pm2/web-frontend-error.log',
      out_file: './logs/pm2/web-frontend-out.log',
      log_file: './logs/pm2/web-frontend.log',
      time: true,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      merge_logs: true,
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      // 等待后端启动后再启动前端
      wait_ready: false,
      listen_timeout: 30000,
    },

    // Tracker (数据库版本)
    {
      name: 'tracker',
      script: './scripts/pm2-start-tracker.sh',
      cwd: './',
      interpreter: 'bash',
      instances: 1,
      exec_mode: 'fork',
      env: {
        NODE_ENV: 'production',
        PYTHONUNBUFFERED: '1',
      },
      error_file: './logs/pm2/tracker-error.log',
      out_file: './logs/pm2/tracker-out.log',
      log_file: './logs/pm2/tracker.log',
      time: true,
      autorestart: true,
      watch: false,
      max_memory_restart: '300M',
      merge_logs: true,
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      // 等待 Web 后端启动后再启动 Tracker
      wait_ready: false,
      listen_timeout: 30000,
    },

    // Bot (QQ 机器人)
    {
      name: 'bot',
      script: './scripts/pm2-start-bot.sh',
      cwd: './',
      interpreter: 'bash',
      instances: 1,
      exec_mode: 'fork',
      env: {
        NODE_ENV: 'production',
        PYTHONUNBUFFERED: '1',
      },
      error_file: './logs/pm2/bot-error.log',
      out_file: './logs/pm2/bot-out.log',
      log_file: './logs/pm2/bot.log',
      time: true,
      autorestart: true,
      watch: false,
      max_memory_restart: '300M',
      merge_logs: true,
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },
  ],
};

