'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { RefreshCw, TrendingUp, Activity, Clock, Zap, Users } from 'lucide-react';
import Navbar from '@/components/layout/navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { StatCard } from '@/components/ui/card-animated';
import { PageTransition } from '@/components/ui/page-transition';
import { ElectricityHistoryChart } from '@/components/charts/electricity-history';
import api from '@/lib/api';
import { isAuthenticated } from '@/lib/auth';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface Subscription {
  id: string;
  room_name: string;
  threshold: number;
  is_active: boolean;
  current_surplus?: number | null;
  last_query_time?: string | null;
  email_recipient_count?: number | null;
}

export default function DashboardPage() {
  const router = useRouter();
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [loading, setLoading] = useState(true);
  const [primarySubscriptionId, setPrimarySubscriptionId] = useState<string | null>(null);
  const [history, setHistory] = useState<{ timestamp: string; surplus: number }[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined') {
      setLoading(false);
      return;
    }
    
    const checkAuth = async () => {
      if (!isAuthenticated()) {
        router.push('/login');
        setLoading(false);
        return;
      }
      await fetchSubscriptions();
    };
    
    checkAuth();
  }, []);

  const fetchSubscriptions = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/subscriptions');
      setSubscriptions(response.data || []);
      const stored = typeof window !== 'undefined' ? localStorage.getItem('primary_subscription_id') : null;
      const fallback = response.data?.[0]?.id || null;
      const initId = stored || fallback;
      if (initId) {
        setPrimarySubscriptionId(initId);
        fetchHistory(initId);
      }
    } catch (error: any) {
      console.error('Failed to fetch subscriptions:', error);
      setSubscriptions([]);
      if (error.code === 'ECONNABORTED' || error.message === 'Network Error') {
        console.error('无法连接到服务器，请检查后端是否运行');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchHistory = async (subscriptionId: string) => {
    try {
      setRefreshing(true);
      const resp = await api.get(`/api/history/subscriptions/${subscriptionId}`);
      const data = resp.data || [];
      setHistory(Array.isArray(data) ? data.slice().reverse() : []);
    } catch (error) {
      console.error('Failed to fetch history:', error);
      setHistory([]);
    } finally {
      setRefreshing(false);
    }
  };

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
              <p className="text-muted-foreground">加载中...</p>
            </div>
          </motion.div>
        </div>
      </div>
    );
  }

  const activeCount = subscriptions.filter(s => s.is_active).length;
  const latestSubscription = subscriptions.length > 0 ? subscriptions[subscriptions.length - 1] : null;

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <PageTransition>
        <div className="container mx-auto p-6 space-y-6">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between"
          >
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
                仪表盘
              </h1>
              <p className="text-muted-foreground text-sm mt-1">
                监控和管理您的电费订阅
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Link href="/subscriptions">
                <Button className="transition-all hover:scale-105">
                  管理订阅
                </Button>
              </Link>
            </div>
          </motion.div>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            <StatCard
              title="总订阅数"
              description="当前活跃的订阅数量"
              value={subscriptions.length}
              icon={<Users className="h-5 w-5" />}
              delay={0.1}
            />
            <StatCard
              title="活跃订阅"
              description="正在监控的房间"
              value={activeCount}
              icon={<Activity className="h-5 w-5" />}
              delay={0.2}
            />
            <StatCard
              title="最近订阅"
              description="最近添加的订阅"
              value={latestSubscription?.room_name || '暂无订阅'}
              icon={<Clock className="h-5 w-5" />}
              delay={0.3}
            />
          </div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <Card className="transition-all hover:shadow-lg">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Zap className="h-5 w-5" />
                      历史电费
                    </CardTitle>
                    <CardDescription>选择房间查看历史电费趋势</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="mb-4 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                  <div className="flex flex-col gap-2">
                    <span className="text-sm font-medium text-muted-foreground">首要房间</span>
                    <Select
                      value={primarySubscriptionId || ''}
                      onValueChange={(id) => {
                        setPrimarySubscriptionId(id);
                        if (typeof window !== 'undefined') {
                          localStorage.setItem('primary_subscription_id', id);
                        }
                        if (id) fetchHistory(id);
                      }}
                    >
                      <SelectTrigger className="w-[200px]">
                        <SelectValue placeholder="选择房间" />
                      </SelectTrigger>
                      <SelectContent>
                        {subscriptions.map((sub) => (
                          <SelectItem key={sub.id} value={sub.id}>
                            {sub.room_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => primarySubscriptionId && fetchHistory(primarySubscriptionId)}
                    disabled={!primarySubscriptionId || refreshing}
                    className="transition-all hover:scale-105"
                  >
                    {refreshing ? (
                      <>
                        <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                        刷新中...
                      </>
                    ) : (
                      <>
                        <RefreshCw className="h-4 w-4 mr-2" />
                        刷新历史
                      </>
                    )}
                  </Button>
                </div>
                {history.length === 0 ? (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-center text-muted-foreground py-12"
                  >
                    <TrendingUp className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>暂无历史数据</p>
                  </motion.div>
                ) : (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.2 }}
                  >
                    <ElectricityHistoryChart data={history} height={320} />
                  </motion.div>
                )}
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            <Card className="transition-all hover:shadow-lg">
              <CardHeader>
                <CardTitle>订阅列表</CardTitle>
                <CardDescription>所有订阅的房间</CardDescription>
              </CardHeader>
              <CardContent>
                {subscriptions.length === 0 ? (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-center py-12"
                  >
                    <Users className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                    <p className="text-muted-foreground mb-4">
                      还没有订阅，
                      <Link href="/subscriptions" className="text-primary hover:underline ml-1">
                        立即添加
                      </Link>
                    </p>
                  </motion.div>
                ) : (
                  <div className="space-y-3">
                    {subscriptions.map((sub, index) => (
                      <motion.div
                        key={sub.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.6 + index * 0.05 }}
                        className="group flex flex-col gap-4 rounded-lg border bg-card p-4 transition-all hover:border-primary/50 hover:shadow-md md:flex-row md:items-center md:justify-between"
                      >
                        <div className="space-y-2 flex-1">
                          <div className="flex items-center gap-2">
                            <h3 className="font-semibold text-lg">{sub.room_name}</h3>
                            <Badge
                              variant={sub.is_active ? 'default' : 'secondary'}
                              className="transition-all group-hover:scale-105"
                            >
                              {sub.is_active ? '活跃' : '已停用'}
                            </Badge>
                          </div>
                          <div className="grid grid-cols-2 gap-2 text-sm md:grid-cols-4">
                            <div>
                              <span className="text-muted-foreground">阈值:</span>{' '}
                              <span className="font-medium">{sub.threshold} 元</span>
                            </div>
                            <div>
                              <span className="text-muted-foreground">当前电费:</span>{' '}
                              <span className="font-medium text-green-600 dark:text-green-400">
                                {sub.current_surplus ?? '暂无'}
                              </span>
                            </div>
                            <div>
                              <span className="text-muted-foreground">最后查询:</span>{' '}
                              <span className="font-medium">
                                {sub.last_query_time
                                  ? new Date(sub.last_query_time).toLocaleString('zh-CN', {
                                      month: '2-digit',
                                      day: '2-digit',
                                      hour: '2-digit',
                                      minute: '2-digit',
                                    })
                                  : '暂无'}
                              </span>
                            </div>
                            <div>
                              <span className="text-muted-foreground">邮件通知:</span>{' '}
                              <span className="font-medium">
                                {sub.email_recipient_count ? `${sub.email_recipient_count} 人` : '未配置'}
                              </span>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setPrimarySubscriptionId(sub.id);
                              if (typeof window !== 'undefined') {
                                localStorage.setItem('primary_subscription_id', sub.id);
                              }
                              fetchHistory(sub.id);
                            }}
                            className="transition-all hover:scale-105"
                          >
                            设为首要
                          </Button>
                          <Link href={`/history/${sub.id}`}>
                            <Button variant="outline" size="sm" className="transition-all hover:scale-105">
                              查看历史
                            </Button>
                          </Link>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </PageTransition>
    </div>
  );
}
