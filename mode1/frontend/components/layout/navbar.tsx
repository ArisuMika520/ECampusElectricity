'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { removeToken } from '@/lib/auth';
import api from '@/lib/api';

export default function Navbar() {
  const router = useRouter();
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    fetchUserInfo();
  }, []);

  const fetchUserInfo = async () => {
    try {
      const response = await api.get('/api/auth/me');
      setIsAdmin(response.data.is_admin || false);
    } catch (error) {
      // Ignore errors
    }
  };

  const handleLogout = () => {
    removeToken();
    router.push('/login');
  };

  return (
    <nav className="border-b bg-white">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <div className="flex items-center space-x-6">
          <Link href="/dashboard" className="text-xl font-bold">
            电费监控系统
          </Link>
          <div className="flex space-x-4">
            <Link href="/dashboard" className="text-gray-600 hover:text-gray-900">
              仪表盘
            </Link>
            <Link href="/subscriptions" className="text-gray-600 hover:text-gray-900">
              订阅管理
            </Link>
            <Link href="/logs" className="text-gray-600 hover:text-gray-900">
              日志监控
            </Link>
            <Link href="/settings" className="text-gray-600 hover:text-gray-900">
              设置
            </Link>
            {isAdmin && (
              <Link href="/admin" className="text-gray-600 hover:text-gray-900">
                管理员
              </Link>
            )}
          </div>
        </div>
        <Button variant="outline" onClick={handleLogout}>
          退出登录
        </Button>
      </div>
    </nav>
  );
}

