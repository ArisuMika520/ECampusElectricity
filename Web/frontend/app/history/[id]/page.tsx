'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Navbar from '@/components/layout/navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
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

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }
    fetchHistory();
  }, [router, subscriptionId]);

  const fetchHistory = async () => {
    try {
      const response = await api.get(`/api/history/subscriptions/${subscriptionId}`);
      setHistory(response.data.reverse()); // Reverse to show chronological order
    } catch (error) {
      console.error('Failed to fetch history:', error);
    } finally {
      setLoading(false);
    }
  };

  const chartData = history.map(record => ({
    time: new Date(record.timestamp).toLocaleString('zh-CN'),
    surplus: record.surplus,
  }));

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
        <h1 className="mb-6 text-3xl font-bold">历史数据</h1>
        
        <Card>
          <CardHeader>
            <CardTitle>电费余额趋势</CardTitle>
            <CardDescription>历史电费余额变化图表</CardDescription>
          </CardHeader>
          <CardContent>
            {history.length === 0 ? (
              <div className="text-center py-8 text-gray-500">暂无历史数据</div>
            ) : (
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="surplus" stroke="#8884d8" name="余额 (元)" />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card className="mt-6">
          <CardHeader>
            <CardTitle>数据列表</CardTitle>
            <CardDescription>详细历史记录</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {history.map((record) => (
                <div
                  key={record.id}
                  className="flex items-center justify-between rounded-lg border p-4"
                >
                  <div>
                    <div className="font-semibold">{new Date(record.timestamp).toLocaleString('zh-CN')}</div>
                  </div>
                  <div className="text-lg font-bold">{record.surplus} 元</div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}



