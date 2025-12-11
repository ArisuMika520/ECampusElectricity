'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Navbar from '@/components/layout/navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import api from '@/lib/api';
import { isAuthenticated } from '@/lib/auth';

interface Subscription {
  id: string;
  room_name: string;
  threshold: number;
  is_active: boolean;
  is_owner?: boolean;
}

export default function DashboardPage() {
  const router = useRouter();
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }

    fetchSubscriptions();
  }, [router]);

  const fetchSubscriptions = async () => {
    try {
      const response = await api.get('/api/subscriptions');
      setSubscriptions(response.data);
    } catch (error) {
      console.error('Failed to fetch subscriptions:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div>
        <Navbar />
        <div className="container mx-auto p-4">加载中...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="container mx-auto p-6">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-3xl font-bold">仪表盘</h1>
          <Link href="/subscriptions">
            <Button>管理订阅</Button>
          </Link>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle>总订阅数</CardTitle>
              <CardDescription>当前活跃的订阅数量</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{subscriptions.length}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>活跃订阅</CardTitle>
              <CardDescription>正在监控的房间</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {subscriptions.filter(s => s.is_active).length}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>最近订阅</CardTitle>
              <CardDescription>最近添加的订阅</CardDescription>
            </CardHeader>
            <CardContent>
              {subscriptions.length > 0 ? (
                <div className="text-lg font-semibold">
                  {subscriptions[subscriptions.length - 1].room_name}
                </div>
              ) : (
                <div className="text-gray-500">暂无订阅</div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>订阅列表</CardTitle>
              <CardDescription>所有订阅的房间</CardDescription>
            </CardHeader>
            <CardContent>
              {subscriptions.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  还没有订阅，<Link href="/subscriptions" className="text-blue-600 hover:underline">立即添加</Link>
                </div>
              ) : (
                <div className="space-y-2">
                  {subscriptions.map((sub) => (
                    <div
                      key={sub.id}
                      className="flex items-center justify-between rounded-lg border p-4"
                    >
                      <div>
                        <div className="font-semibold">{sub.room_name}</div>
                        <div className="text-sm text-gray-500">
                          阈值: {sub.threshold} 元
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Badge variant={sub.is_active ? 'default' : 'secondary'}>
                          {sub.is_active ? '活跃' : '已停用'}
                        </Badge>
                        <Link href={`/history/${sub.id}`}>
                          <Button variant="outline" size="sm">查看历史</Button>
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}



