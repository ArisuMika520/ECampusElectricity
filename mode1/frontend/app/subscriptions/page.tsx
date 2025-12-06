'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Navbar from '@/components/layout/navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import api from '@/lib/api';
import { isAuthenticated } from '@/lib/auth';

interface Subscription {
  id: string;
  room_name: string;
  threshold: number;
  email_recipients: string[];
  is_active: boolean;
}

export default function SubscriptionsPage() {
  const router = useRouter();
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    room_name: '',
    area_id: '',
    building_code: '',
    floor_code: '',
    room_code: '',
    threshold: 20.0,
    email_recipients: '',
  });

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const emailList = formData.email_recipients
        .split(',')
        .map(email => email.trim())
        .filter(email => email);
      
      await api.post('/api/subscriptions', {
        ...formData,
        email_recipients: emailList,
      });
      
      setDialogOpen(false);
      setFormData({
        room_name: '',
        area_id: '',
        building_code: '',
        floor_code: '',
        room_code: '',
        threshold: 20.0,
        email_recipients: '',
      });
      fetchSubscriptions();
    } catch (error: any) {
      alert(error.response?.data?.detail || '创建订阅失败');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('确定要删除这个订阅吗？')) return;
    
    try {
      await api.delete(`/api/subscriptions/${id}`);
      fetchSubscriptions();
    } catch (error) {
      alert('删除失败');
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
          <h1 className="text-3xl font-bold">订阅管理</h1>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button>添加订阅</Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>添加新订阅</DialogTitle>
                <DialogDescription>
                  填写房间信息以创建新的电费监控订阅
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleSubmit}>
                <div className="grid gap-4 py-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="room_name">房间名称</Label>
                      <Input
                        id="room_name"
                        value={formData.room_name}
                        onChange={(e) => setFormData({ ...formData, room_name: e.target.value })}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="threshold">告警阈值 (元)</Label>
                      <Input
                        id="threshold"
                        type="number"
                        step="0.1"
                        value={formData.threshold}
                        onChange={(e) => setFormData({ ...formData, threshold: parseFloat(e.target.value) })}
                        required
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="area_id">校区ID</Label>
                      <Input
                        id="area_id"
                        value={formData.area_id}
                        onChange={(e) => setFormData({ ...formData, area_id: e.target.value })}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="building_code">楼栋代码</Label>
                      <Input
                        id="building_code"
                        value={formData.building_code}
                        onChange={(e) => setFormData({ ...formData, building_code: e.target.value })}
                        required
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="floor_code">楼层代码</Label>
                      <Input
                        id="floor_code"
                        value={formData.floor_code}
                        onChange={(e) => setFormData({ ...formData, floor_code: e.target.value })}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="room_code">房间代码</Label>
                      <Input
                        id="room_code"
                        value={formData.room_code}
                        onChange={(e) => setFormData({ ...formData, room_code: e.target.value })}
                        required
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email_recipients">收件人邮箱 (逗号分隔)</Label>
                    <Input
                      id="email_recipients"
                      type="email"
                      value={formData.email_recipients}
                      onChange={(e) => setFormData({ ...formData, email_recipients: e.target.value })}
                      placeholder="email1@example.com, email2@example.com"
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button type="submit">创建订阅</Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>订阅列表</CardTitle>
            <CardDescription>管理你的电费监控订阅</CardDescription>
          </CardHeader>
          <CardContent>
            {subscriptions.length === 0 ? (
              <div className="text-center py-8 text-gray-500">还没有订阅</div>
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
                        阈值: {sub.threshold} 元 | 收件人: {sub.email_recipients.length} 个
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge variant={sub.is_active ? 'default' : 'secondary'}>
                        {sub.is_active ? '活跃' : '已停用'}
                      </Badge>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => handleDelete(sub.id)}
                      >
                        删除
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}



