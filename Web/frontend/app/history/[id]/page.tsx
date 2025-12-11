'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { motion } from 'framer-motion';
import { RefreshCw, Zap, TrendingUp } from 'lucide-react';
import Navbar from '@/components/layout/navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ElectricityHistoryChart } from '@/components/charts/electricity-history';
import { Button } from '@/components/ui/button';
import { Modal, ModalContent, ModalFooter } from '@/components/ui/modal';
import { PageTransition } from '@/components/ui/page-transition';
import { CardAnimated } from '@/components/ui/card-animated';
import api from '@/lib/api';
import { isAuthenticated } from '@/lib/auth';

interface HistoryRecord {
  id: string;
  surplus: number;
  timestamp: string;
}

export default function HistoryPage() {
  const router = useRouter();
  const params = useParams();
  const subscriptionId = params.id as string;
  const [history, setHistory] = useState<HistoryRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [subscriptionName, setSubscriptionName] = useState<string>('');
  const [querying, setQuerying] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalContent, setModalContent] = useState<{ title: string; message: string; type: 'success' | 'error' } | null>(null);

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
      await fetchHistory();
    };
    
    checkAuth();
  }, [subscriptionId]);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      console.log('Fetching history for subscription:', subscriptionId);
      
      try {
        const subResponse = await api.get(`/api/subscriptions/${subscriptionId}`);
        if (subResponse.data) {
          setSubscriptionName(subResponse.data.room_name || '');
        }
      } catch (e) {
        console.warn('Failed to fetch subscription info:', e);
      }
      
      const response = await api.get(`/api/history/subscriptions/${subscriptionId}`);
      if (response.data && Array.isArray(response.data)) {
        setHistory(response.data.reverse());
      } else {
        console.warn('Invalid history data format:', response.data);
        setHistory([]);
      }
    } catch (error: any) {
      console.error('Failed to fetch history:', error);
      setHistory([]);
      if (error.response?.status !== 404) {
        console.error('获取历史数据失败: ' + (error.response?.data?.detail || error.message));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleQuery = async () => {
    setQuerying(true);
    try {
      const response = await api.post(`/api/subscriptions/${subscriptionId}/query`);
      setModalContent({
        title: '查询成功',
        message: `当前电费: ${response.data.surplus} 元`,
        type: 'success'
      });
      setModalOpen(true);
      await fetchHistory();
    } catch (error: any) {
      console.error('Failed to query electricity:', error);
      const detail = error.response?.data?.detail;
      const upstreamMsg =
        typeof detail === 'object'
          ? detail?.message || detail?.raw?.message || detail?.raw?.error_description
          : detail;
      const errorMsg = upstreamMsg || error.message || '查询失败';
      setModalContent({
        title: '查询失败',
        message: String(errorMsg),
        type: 'error'
      });
      setModalOpen(true);
    } finally {
      setQuerying(false);
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
                历史数据
              </h1>
              {subscriptionName && (
                <p className="text-muted-foreground mt-1 flex items-center gap-2">
                  <Zap className="h-4 w-4" />
                  房间: {subscriptionName}
                </p>
              )}
            </div>
            <Button
              onClick={handleQuery}
              disabled={querying}
              className="transition-all hover:scale-105"
            >
              {querying ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  查询中...
                </>
              ) : (
                <>
                  <Zap className="h-4 w-4 mr-2" />
                  手动查询电费
                </>
              )}
            </Button>
          </motion.div>
          
          <CardAnimated delay={0.1}>
            <Card className="transition-all hover:shadow-lg">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-primary" />
                  <CardTitle>电费余额趋势</CardTitle>
                </div>
                <CardDescription>历史电费余额变化图表</CardDescription>
              </CardHeader>
              <CardContent>
                {history.length === 0 ? (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-center py-12"
                  >
                    <TrendingUp className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                    <p className="text-muted-foreground mb-4">暂无历史数据</p>
                    <p className="text-sm text-muted-foreground mb-4">
                      点击右上角"手动查询电费"按钮来获取当前电费并创建历史记录
                    </p>
                    <Button onClick={handleQuery} disabled={querying} variant="outline" className="transition-all hover:scale-105">
                      {querying ? (
                        <>
                          <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                          查询中...
                        </>
                      ) : (
                        <>
                          <Zap className="h-4 w-4 mr-2" />
                          立即查询
                        </>
                      )}
                    </Button>
                  </motion.div>
                ) : (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.2 }}
                  >
                    <ElectricityHistoryChart data={history} height={400} />
                  </motion.div>
                )}
              </CardContent>
            </Card>
          </CardAnimated>

          <CardAnimated delay={0.2}>
            <Card className="transition-all hover:shadow-lg">
              <CardHeader>
                <CardTitle>数据列表</CardTitle>
                <CardDescription>详细历史记录</CardDescription>
              </CardHeader>
              <CardContent>
                {history.length === 0 ? (
                  <p className="text-center text-muted-foreground py-4">暂无数据</p>
                ) : (
                  <div className="space-y-3">
                    {history.map((record, index) => (
                      <motion.div
                        key={record.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.3 + index * 0.05 }}
                        className="group flex items-center justify-between rounded-lg border bg-card p-4 transition-all hover:border-primary/50 hover:shadow-md"
                      >
                        <div className="flex items-center gap-3">
                          <div className="text-muted-foreground">
                            {new Date(record.timestamp).toLocaleString('zh-CN')}
                          </div>
                        </div>
                        <div className="text-lg font-bold text-primary">
                          {record.surplus} 元
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </CardAnimated>
        </div>
      </PageTransition>

      {modalContent && (
        <Modal
          open={modalOpen}
          onOpenChange={setModalOpen}
          title={modalContent.title}
          size="md"
        >
          <ModalContent>
            <div className={`p-4 rounded-lg ${
              modalContent.type === 'success' 
                ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800' 
                : 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800'
            }`}>
              <p className={`${
                modalContent.type === 'success' 
                  ? 'text-green-800 dark:text-green-200' 
                  : 'text-red-800 dark:text-red-200'
              }`}>
                {modalContent.message}
              </p>
            </div>
          </ModalContent>
          <ModalFooter>
            <Button onClick={() => setModalOpen(false)}>
              确定
            </Button>
          </ModalFooter>
        </Modal>
      )}
    </div>
  );
}