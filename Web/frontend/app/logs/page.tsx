'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useTheme } from 'next-themes';
import Navbar from '@/components/layout/navbar';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import api from '@/lib/api';
import { isAuthenticated } from '@/lib/auth';
import { motion } from 'framer-motion';
import { RefreshCw, Trash2 } from 'lucide-react';

type LogRecord = {
  id?: string;
  level: string;
  message: string;
  module?: string | null;
  timestamp: string;
  process?: string; // PM2进程名称（web-backend, web-frontend, tracker）
};

type TerminalType = any;
type FitAddonType = any;

export default function LogsPage() {
  const router = useRouter();
  const { theme } = useTheme();
  const [loading, setLoading] = useState(true);
  const [containerReady, setContainerReady] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const terminalRef = useRef<HTMLDivElement | null>(null);
  const terminalInstanceRef = useRef<TerminalType | null>(null);
  const fitAddonRef = useRef<FitAddonType | null>(null);
  const initAttemptedRef = useRef(false);
  const isInitializedRef = useRef(false);
  const cleanupRef = useRef<(() => void) | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);

  const setTerminalRef = useCallback((element: HTMLDivElement | null) => {
    if (terminalRef.current === element) {
      return;
    }
    
    terminalRef.current = element;
    
    if (element) {
      setContainerReady(true);
    } else {
      setContainerReady(false);
    }
  }, []);
  
  useEffect(() => {
    if (typeof window === 'undefined' || containerReady || isInitializedRef.current) return;
    
    const checkElement = () => {
      if (containerReady || isInitializedRef.current) return;
      
      const element = document.getElementById('terminal-container');
      if (element) {
        terminalRef.current = element as HTMLDivElement;
        setContainerReady(true);
      }
    };
    
    const timer1 = setTimeout(checkElement, 50);
    const timer2 = setTimeout(checkElement, 200);
    const timer3 = setTimeout(checkElement, 500);
    
    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
    };
  }, [containerReady]);

  useEffect(() => {
    const timeout = setTimeout(() => {
      if (loading) {
        console.warn('Terminal initialization timeout, forcing loading to false');
        setLoading(false);
      }
    }, 10000);
    
    return () => clearTimeout(timeout);
  }, [loading]);

  useEffect(() => {
    if (isInitializedRef.current && terminalInstanceRef.current) {
      console.log('Terminal already initialized, checking WebSocket connection');
      setLoading(false);
      if (!wsRef.current || wsRef.current.readyState === WebSocket.CLOSED) {
        console.log('WebSocket not connected, reconnecting...');
        setTimeout(() => {
          if (terminalInstanceRef.current) {
            connectWebSocket(terminalInstanceRef.current);
          }
        }, 300);
      }
      return;
    }
    
    if (typeof window === 'undefined') {
      setLoading(false);
      return;
    }
    
    if (!isAuthenticated()) {
      router.push('/login');
      setLoading(false);
      return;
    }
    
    if (!containerReady) {
      const timeout = setTimeout(() => {
        if (!containerReady && !isInitializedRef.current) {
          const element = document.getElementById('terminal-container');
          if (element) {
            terminalRef.current = element as HTMLDivElement;
            setContainerReady(true);
          } else {
            console.warn('Terminal container not found after timeout');
            setLoading(false);
          }
        }
      }, 2000);
      return () => clearTimeout(timeout);
    }
    
    if (initAttemptedRef.current || isInitializedRef.current) {
      return;
    }
    
    let isMounted = true;
    initAttemptedRef.current = true;
    
    const initialize = async () => {
      if (!terminalRef.current) {
        console.error('Terminal ref is null when trying to initialize');
        if (isMounted) {
          setLoading(false);
        }
        return;
      }
      
      try {
        const cleanup = await initializeTerminal();
        cleanupRef.current = cleanup || null;
        isInitializedRef.current = true;
        if (isMounted) {
          setLoading(false);
        }
      } catch (error) {
        console.error('Failed to initialize terminal:', error);
        if (isMounted) {
          setLoading(false);
        }
        initAttemptedRef.current = false;
      }
    };
    
    const timer = setTimeout(() => {
      initialize();
    }, 100);
    
    return () => {
      isMounted = false;
      clearTimeout(timer);
    };
  }, [containerReady]);

  const getTerminalTheme = () => {
    const isDark = theme === 'dark' || (theme === 'system' && typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches);
    
    if (isDark) {
      return {
        background: '#0d1117',
        foreground: '#c9d1d9',
        cursor: '#58a6ff',
        black: '#484f58',
        red: '#f85149',
        green: '#3fb950',
        yellow: '#d29922',
        blue: '#58a6ff',
        magenta: '#bc8cff',
        cyan: '#39c5cf',
        white: '#b1bac4',
        brightBlack: '#6e7681',
        brightRed: '#ff7b72',
        brightGreen: '#7ee787',
        brightYellow: '#d29922',
        brightBlue: '#79c0ff',
        brightMagenta: '#d2a8ff',
        brightCyan: '#56d4dd',
        brightWhite: '#f0f6fc',
      };
    } else {
      return {
        background: '#ffffff',
        foreground: '#24292f',
        cursor: '#0969da',
        black: '#57606a',
        red: '#cf222e',
        green: '#1a7f37',
        yellow: '#9a6700',
        blue: '#0969da',
        magenta: '#8250df',
        cyan: '#1b7c83',
        white: '#6e7781',
        brightBlack: '#8c959f',
        brightRed: '#a40e26',
        brightGreen: '#1a7f37',
        brightYellow: '#9a6700',
        brightBlue: '#0969da',
        brightMagenta: '#8250df',
        brightCyan: '#1b7c83',
        brightWhite: '#24292f',
      };
    }
  };

  const initializeTerminal = async (): Promise<(() => void) | undefined> => {
    console.log('initializeTerminal called, terminalRef.current:', terminalRef.current);
    
    if (typeof window === 'undefined') {
      console.error('Window is undefined');
      setLoading(false);
      return;
    }
    
    if (!terminalRef.current) {
      console.error('Terminal ref is null in initializeTerminal');
      setLoading(false);
      return;
    }

    // 动态加载 xterm 模块和 CSS
    let Terminal: TerminalType;
    let FitAddon: FitAddonType;
    
    try {
      if (typeof window !== 'undefined') {
        try {
          await import('@xterm/xterm/css/xterm.css');
        } catch (cssError) {
          console.warn('Failed to load xterm CSS:', cssError);
        }
      }
      
      const [{ Terminal: TerminalClass }, { FitAddon: FitAddonClass }] = await Promise.all([
        import('@xterm/xterm'),
        import('@xterm/addon-fit'),
      ]);
      Terminal = TerminalClass;
      FitAddon = FitAddonClass;
    } catch (error) {
      console.error('Failed to load xterm modules:', error);
      setLoading(false);
      return;
    }

    try {
      const terminal = new Terminal({
        theme: getTerminalTheme(),
        fontFamily: '"Courier New", "Consolas", "Monaco", "Menlo", "Ubuntu Mono", monospace',
        fontSize: 13,
        lineHeight: 1.4,
        letterSpacing: 0.5,
        cursorBlink: true,
        cursorStyle: 'block',
        allowTransparency: false,
        rows: 30,
        fontWeight: 'normal',
        fontWeightBold: 'bold',
        disableStdin: true,
        convertEol: true,
        scrollback: 10000,
      });

      const fitAddon = new FitAddon();
      terminal.loadAddon(fitAddon);
      
      if (!terminalRef.current) {
        setLoading(false);
        return;
      }
      
      terminal.open(terminalRef.current);
      
      await new Promise(resolve => setTimeout(resolve, 300));
      
      const rect = terminalRef.current.getBoundingClientRect();
      console.log('Terminal container size:', rect.width, 'x', rect.height);
      
      if (rect.width === 0 || rect.height === 0) {
        console.warn('Terminal container has zero size, waiting more...');
        await new Promise(resolve => setTimeout(resolve, 500));
      }
      
      try {
        fitAddon.fit();
        console.log('FitAddon fitted successfully');
      } catch (error) {
        console.error('FitAddon fit error:', error);
      }

      terminalInstanceRef.current = terminal;
      fitAddonRef.current = fitAddon;

      await new Promise(resolve => setTimeout(resolve, 200));
      
      terminal.writeln('\x1b[32m╔═══════════════════════════════════════════════════════════╗\x1b[0m');
      terminal.writeln('\x1b[32m║\x1b[0m            \x1b[36m电费监控系统 - 实时日志终端\x1b[0m              \x1b[32m║\x1b[0m');
      terminal.writeln('\x1b[32m╚═══════════════════════════════════════════════════════════╝\x1b[0m');
      terminal.writeln('');
      terminal.writeln('\x1b[33m正在连接日志服务器...\x1b[0m');
      terminal.writeln('\x1b[36m终端初始化成功\x1b[0m');
      terminal.writeln('');
      
      await new Promise(resolve => setTimeout(resolve, 100));
      
      setTimeout(() => {
        if (fitAddonRef.current) {
          try {
            fitAddonRef.current.fit();
          } catch (error) {
            console.error('Second fit error:', error);
          }
        }
      }, 200);

      const handleResize = () => {
        if (fitAddonRef.current) {
          fitAddonRef.current.fit();
        }
      };
      window.addEventListener('resize', handleResize);

      const updateTheme = () => {
        if (terminalInstanceRef.current) {
          terminalInstanceRef.current.options.theme = getTerminalTheme();
        }
      };
      
      const themeObserver = new MutationObserver(updateTheme);
      if (document.documentElement) {
        themeObserver.observe(document.documentElement, {
          attributes: true,
          attributeFilter: ['class'],
        });
      }

      const cleanup = () => {
        window.removeEventListener('resize', handleResize);
        themeObserver.disconnect();
      };

      await new Promise(resolve => setTimeout(resolve, 200));

      try {
        await fetchInitialLogs(terminal);
      } catch (error) {
        console.error('Failed to fetch initial logs:', error);
        if (terminal && terminalInstanceRef.current) {
          terminal.writeln('\x1b[31m警告: 无法获取历史日志\x1b[0m');
        }
      }

      setTimeout(() => {
        if (terminalInstanceRef.current && (!wsRef.current || wsRef.current.readyState === WebSocket.CLOSED)) {
          connectWebSocket(terminalInstanceRef.current);
        }
      }, 500);

      return cleanup;
    } catch (error) {
      console.error('Failed to initialize terminal:', error);
      setLoading(false);
      throw error;
    }
  };

  useEffect(() => {
    if (terminalInstanceRef.current) {
      terminalInstanceRef.current.options.theme = getTerminalTheme();
    }
  }, [theme]);

  const fetchInitialLogs = async (terminal: TerminalType) => {
    if (!terminal) {
      console.error('Terminal not initialized');
      return;
    }
    
    try {
      console.log('Fetching initial logs from /logs...');
      terminal.writeln('\x1b[36m正在获取PM2日志...\x1b[0m');
      
      const resp = await api.get('/logs', { params: { limit: 200 } });
      console.log('Logs response:', resp.data);
      const logs = resp.data || [];
      
      // 只显示PM2日志
      const pm2Logs = logs.filter((log: LogRecord) => {
        const module = log.module || '';
        return module.startsWith('pm2.');
      });
      
      if (pm2Logs.length > 0) {
        terminal.writeln(`\x1b[32m✓ 已加载 ${pm2Logs.length} 条PM2历史日志\x1b[0m`);
        terminal.writeln('');
        
        const reversedLogs = [...pm2Logs].reverse();
        reversedLogs.forEach((log: LogRecord) => {
          writeLogToTerminal(terminal, log);
        });
      } else {
        terminal.writeln('\x1b[33m⚠ 暂无PM2历史日志\x1b[0m');
        terminal.writeln('\x1b[36m等待PM2日志输出...\x1b[0m');
      }
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || error.message || '未知错误';
      terminal.writeln(`\x1b[31m✗ 错误: 无法获取历史日志 - ${errorMsg}\x1b[0m`);
      console.error('Failed to fetch logs', error);
    }
  };

  const connectWebSocket = (terminal: TerminalType) => {
    if (!terminal) {
      console.error('Terminal not initialized for WebSocket');
      return;
    }
    
    // 如果已有连接，先关闭
    if (wsRef.current) {
      try {
        if (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING) {
          wsRef.current.close();
        }
      } catch (e) {
        console.warn('Error closing existing WebSocket:', e);
      }
      wsRef.current = null;
    }
    
    try {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 
                        process.env.API_BASE_URL || 
                        'http://localhost:8000';
      
      const apiUrl = new URL(apiBaseUrl);
      const protocol = apiUrl.protocol === 'https:' ? 'wss' : 'ws';
      const wsHost = apiUrl.host;
      const wsUrl = `${protocol}://${wsHost}/ws/logs`;
      
      console.log('Connecting to WebSocket:', wsUrl, '(API base:', apiBaseUrl, ')');
      
      if (terminal && terminalInstanceRef.current) {
        terminal.writeln(`\x1b[36m正在连接到 ${wsUrl}...\x1b[0m`);
      }
      
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;
      
      let connectTimeout: NodeJS.Timeout | null = null;
      
      connectTimeout = setTimeout(() => {
        if (wsRef.current === ws && ws.readyState === WebSocket.CONNECTING) {
          console.error('WebSocket connection timeout');
          try {
            ws.close();
          } catch (e) {
            console.warn('Error closing timed out WebSocket:', e);
          }
          
          reconnectAttemptsRef.current += 1;
          
          try {
            if (terminal && terminalInstanceRef.current) {
              terminal.writeln('\x1b[31m✗ WebSocket 连接超时，请检查后端服务是否运行\x1b[0m');
              if (reconnectAttemptsRef.current < 5) {
                const delay = Math.min(5000 * reconnectAttemptsRef.current, 30000);
                terminal.writeln(`\x1b[33m${Math.floor(delay / 1000)}秒后重试 (${reconnectAttemptsRef.current}/5)...\x1b[0m`);
              } else {
                terminal.writeln('\x1b[33m已达到最大重试次数，请手动刷新页面\x1b[0m');
              }
            }
          } catch (e) {
            console.error('Error writing timeout message to terminal:', e);
          }
          
          if (wsRef.current === ws) {
            wsRef.current = null;
          }
          
          if (reconnectAttemptsRef.current < 5) {
            const delay = Math.min(5000 * reconnectAttemptsRef.current, 30000);
            reconnectTimerRef.current = setTimeout(() => {
              if (terminalInstanceRef.current && !wsRef.current) {
                connectWebSocket(terminalInstanceRef.current);
              }
            }, delay);
          }
        }
      }, 10000);

      ws.onopen = () => {
        if (connectTimeout) {
          clearTimeout(connectTimeout);
          connectTimeout = null;
        }
        reconnectAttemptsRef.current = 0;
        console.log('WebSocket connected');
        
        try {
          if (terminal && terminalInstanceRef.current) {
            terminal.writeln('\x1b[32m✓ WebSocket 连接已建立\x1b[0m');
            terminal.writeln('');
          }
        } catch (e) {
          console.error('Error writing connection message to terminal:', e);
        }
        
        try {
          ws.send(JSON.stringify({ type: 'ping' }));
        } catch (e) {
          console.error('Failed to send ping:', e);
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'ack') {
            return;
          }
          
          if (!data.message && !data.level) {
            console.warn('Invalid WebSocket message format:', data);
            return;
          }
          
          // 过滤掉无关的日志：只显示PM2日志
          const module = data.module || '';
          const isPm2Log = module.startsWith('pm2.');
          
          // 过滤掉websocket连接相关的日志
          const isWebSocketLog = module === 'websocket' || 
                                 (typeof data.message === 'string' && 
                                  (data.message.includes('WebSocket connection') || 
                                   data.message.includes('WebSocket error') ||
                                   data.message.includes('WebSocket closed')));
          
          // 只显示PM2日志，过滤掉其他无关日志
          if (!isPm2Log || isWebSocketLog) {
            return;
          }
          
          const line: LogRecord = {
            level: (data.level || 'INFO').toUpperCase(),
            message: String(data.message || ''),
            module: data.module || null,
            timestamp: data.timestamp || new Date().toISOString(),
            process: data.process || null, // PM2进程名称
          };
          
          if (terminal && terminalInstanceRef.current) {
            writeLogToTerminal(terminal, line);
          } else {
            console.warn('Terminal not available when receiving WebSocket message');
          }
        } catch (e) {
          console.error('Failed to parse ws log message', e, event.data);
          // 尝试显示原始消息
          if (terminal && terminalInstanceRef.current) {
            try {
              terminal.writeln(`\x1b[33m[WebSocket消息解析错误] ${String(event.data).substring(0, 100)}\x1b[0m`);
            } catch (err) {
              console.error('Failed to write error to terminal:', err);
            }
          }
        }
      };

      ws.onerror = (e) => {
        if (connectTimeout) {
          clearTimeout(connectTimeout);
          connectTimeout = null;
        }
        reconnectAttemptsRef.current += 1;
        console.error('WebSocket error:', e);
        
        try {
          if (terminal && terminalInstanceRef.current) {
            terminal.writeln('\x1b[31m✗ WebSocket 连接错误\x1b[0m');
            terminal.writeln('\x1b[33m请检查后端服务是否正常运行\x1b[0m');
          }
        } catch (err) {
          console.error('Error writing error message to terminal:', err);
        }
      };

      ws.onclose = (event) => {
        if (connectTimeout) {
          clearTimeout(connectTimeout);
          connectTimeout = null;
        }
        console.log('WebSocket closed:', event.code, event.reason);
        
        if (wsRef.current === ws) {
          wsRef.current = null;
        }
        
        if (event.code !== 1000) {
          reconnectAttemptsRef.current += 1;
          
          try {
            if (terminal && terminalInstanceRef.current) {
              terminal.writeln(`\x1b[33mWebSocket 连接已关闭 (${event.code}${event.reason ? ': ' + event.reason : ''})\x1b[0m`);
              
              if (reconnectAttemptsRef.current < 5) {
                const delay = Math.min(3000 * reconnectAttemptsRef.current, 30000);
                terminal.writeln(`\x1b[33m${Math.floor(delay / 1000)}秒后重连 (${reconnectAttemptsRef.current}/5)...\x1b[0m`);
              } else {
                terminal.writeln('\x1b[33m已达到最大重试次数，请手动刷新页面或检查后端服务\x1b[0m');
              }
            }
          } catch (e) {
            console.error('Error writing close message to terminal:', e);
          }
          
          if (reconnectAttemptsRef.current < 5) {
            const delay = Math.min(3000 * reconnectAttemptsRef.current, 30000);
            reconnectTimerRef.current = setTimeout(() => {
              if (terminalInstanceRef.current && !wsRef.current) {
                connectWebSocket(terminalInstanceRef.current);
              }
            }, delay);
          }
        }
      };
    } catch (error) {
      reconnectAttemptsRef.current += 1;
      console.error('Failed to connect websocket:', error);
      if (terminal && terminalInstanceRef.current) {
        terminal.writeln(`\x1b[31m错误: 无法建立 WebSocket 连接 - ${String(error)}\x1b[0m`);
        if (reconnectAttemptsRef.current < 5) {
          const delay = Math.min(5000 * reconnectAttemptsRef.current, 30000);
          terminal.writeln(`\x1b[33m${Math.floor(delay / 1000)}秒后重试 (${reconnectAttemptsRef.current}/5)...\x1b[0m`);
        } else {
          terminal.writeln('\x1b[33m已达到最大重试次数，请检查后端服务配置\x1b[0m');
        }
      }
      if (reconnectAttemptsRef.current < 5) {
        const delay = Math.min(5000 * reconnectAttemptsRef.current, 30000);
        reconnectTimerRef.current = setTimeout(() => {
          if (terminalInstanceRef.current && !wsRef.current) {
            connectWebSocket(terminalInstanceRef.current);
          }
        }, delay);
      }
    }
  };

  const writeLogToTerminal = (terminal: TerminalType, log: LogRecord) => {
    if (!terminal) {
      console.error('Terminal not initialized');
      return;
    }
    
    try {
      let timestamp: Date;
      if (typeof log.timestamp === 'string') {
        timestamp = new Date(log.timestamp);
      } else if (log.timestamp && typeof log.timestamp === 'object' && 'getTime' in log.timestamp) {
        timestamp = log.timestamp as Date;
      } else {
        timestamp = new Date();
      }

      const time = timestamp.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
      });

      const level = (log.level || 'INFO').toUpperCase();
      let levelColor = '\x1b[32m'; // INFO - green
      let levelSymbol = 'ℹ';

      if (level === 'ERROR') {
        levelColor = '\x1b[31m'; // ERROR - red
        levelSymbol = '✗';
      } else if (level === 'WARNING' || level === 'WARN') {
        levelColor = '\x1b[33m'; // WARNING - yellow
        levelSymbol = '⚠';
      } else if (level === 'DEBUG') {
        levelColor = '\x1b[36m'; // DEBUG - cyan
        levelSymbol = '🔍';
      }

      // 根据进程名称设置颜色（从module字段提取：pm2.{service_name}.{log_type}）
      let process = log.process || '';
      if (!process && log.module && log.module.startsWith('pm2.')) {
        // 从module中提取：pm2.web-backend.log -> web-backend
        const parts = log.module.split('.');
        if (parts.length >= 2) {
          process = parts[1]; // 提取service_name
        }
      }
      
      let processColor = '\x1b[37m'; // 默认白色
      let processName = '';
      
      if (process === 'web-backend') {
        processColor = '\x1b[34m'; // 蓝色
        processName = '[web-backend]';
      } else if (process === 'web-frontend') {
        processColor = '\x1b[32m'; // 绿色
        processName = '[web-frontend]';
      } else if (process === 'tracker') {
        processColor = '\x1b[33m'; // 黄色
        processName = '[tracker]';
      }
      
      const processTag = processName ? `${processColor}${processName}\x1b[0m` : '';
      const module = log.module && !processName ? `\x1b[34m[${log.module}]\x1b[0m` : '';
      const timestampStr = `\x1b[90m${time}\x1b[0m`;
      const levelText = `${levelColor}${levelSymbol} ${level}\x1b[0m`;
      const message = String(log.message || '').trim();

      if (message) {
        const parts = [timestampStr, levelText];
        if (processTag) parts.push(processTag);
        if (module) parts.push(module);
        parts.push(message);
        terminal.writeln(parts.join(' '));
      } else {
        const parts = [timestampStr, levelText];
        if (processTag) parts.push(processTag);
        if (module) parts.push(module);
        parts.push('(空消息)');
        terminal.writeln(parts.join(' '));
      }
    } catch (error) {
      console.error('Failed to write log to terminal:', error, log);
      try {
        terminal.writeln(`\x1b[33m[日志解析错误] ${JSON.stringify(log)}\x1b[0m`);
      } catch (e) {
        console.error('Failed to write error log to terminal:', e);
      }
    }
  };

  const handleClear = () => {
    if (terminalInstanceRef.current) {
      terminalInstanceRef.current.clear();
      terminalInstanceRef.current.writeln('\x1b[32m终端已清空\x1b[0m');
      terminalInstanceRef.current.writeln('');
    }
  };

  const handleRefresh = async () => {
    if (terminalInstanceRef.current) {
      terminalInstanceRef.current.clear();
      terminalInstanceRef.current.writeln('\x1b[33m正在重新加载日志...\x1b[0m');
      terminalInstanceRef.current.writeln('');
      await fetchInitialLogs(terminalInstanceRef.current);
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        connectWebSocket(terminalInstanceRef.current);
      }
    }
  };
  
  useEffect(() => {
    return () => {
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      if (cleanupRef.current) {
        cleanupRef.current();
        cleanupRef.current = null;
      }
      reconnectAttemptsRef.current = 0;
    };
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <div className="container mx-auto p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex items-center justify-center h-[60vh]"
          >
            <div className="text-center">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                className="inline-block mb-4"
              >
                <RefreshCw className="h-8 w-8 text-primary" />
              </motion.div>
              <p className="text-muted-foreground">正在初始化终端...</p>
            </div>
          </motion.div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="container mx-auto p-6 space-y-4">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="flex items-center justify-between"
        >
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
              实时日志
            </h1>
            <p className="text-muted-foreground text-sm mt-1">
              显示程序启动后的实时日志（上海时间）
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              className="transition-all hover:scale-105"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              重新加载
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleClear}
              className="transition-all hover:scale-105"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              清空终端
            </Button>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3, delay: 0.1 }}
        >
          <Card className="overflow-hidden border-2">
            <CardHeader className="bg-muted/50">
              <CardTitle>Shell 终端</CardTitle>
              <CardDescription>
                实时滚动窗口，支持 ANSI 颜色代码和完整的终端体验
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0 bg-transparent">
              <div
                ref={setTerminalRef}
                id="terminal-container"
                className="w-full h-[70vh] rounded-b-lg overflow-hidden"
                style={{
                  backgroundColor: theme === 'dark' || (theme === 'system' && typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches) ? '#0d1117' : '#ffffff',
                  minHeight: '400px',
                  display: 'block',
                  position: 'relative',
                  fontFamily: '"Courier New", "Consolas", "Monaco", "Menlo", "Ubuntu Mono", monospace',
                  fontFeatureSettings: '"liga" 0, "calt" 0',
                  textRendering: 'optimizeLegibility',
                }}
              />
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
