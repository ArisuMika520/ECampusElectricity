'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Plus, Trash2, Mail, Zap, RefreshCw } from 'lucide-react';
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
import { PageTransition } from '@/components/ui/page-transition';
import { CardAnimated } from '@/components/ui/card-animated';
import api from '@/lib/api';
import { isAuthenticated } from '@/lib/auth';

interface Subscription {
  id: string;
  room_name: string;
  threshold: number;
  email_recipients: string[];
  is_active: boolean;
  is_owner?: boolean;
}

export default function SubscriptionsPage() {
  const router = useRouter();
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    building_name: '',
    room_number: '',
    threshold: 20.0,
    email_recipients: '',
  });

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
    } catch (error) {
      console.error('Failed to fetch subscriptions:', error);
      setSubscriptions([]);
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
        building_name: formData.building_name.trim(),
        room_number: formData.room_number.trim(),
        threshold: formData.threshold,
        email_recipients: emailList,
      });
      
      setDialogOpen(false);
      setFormData({
        building_name: '',
        room_number: '',
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
            <div className="flex items-center gap-3">
              <Zap className="h-8 w-8 text-primary" />
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
                  订阅管理
                </h1>
                <p className="text-muted-foreground text-sm mt-1">
                  管理你的电费监控订阅
                </p>
              </div>
            </div>
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button className="transition-all hover:scale-105">
                  <Plus className="h-4 w-4 mr-2" />
                  添加订阅
                </Button>
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
                      <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="space-y-2"
                      >
                        <Label htmlFor="building_name">楼栋</Label>
                        <Input
                          id="building_name"
                          placeholder="如 10南 或 D9东"
                          value={formData.building_name}
                          onChange={(e) => setFormData({ ...formData, building_name: e.target.value })}
                          required
                          className="transition-all focus:scale-[1.01]"
                        />
                      </motion.div>
                      <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="space-y-2"
                      >
                        <Label htmlFor="room_number">房间号</Label>
                        <Input
                          id="room_number"
                          placeholder="如 101 或 425"
                          value={formData.room_number}
                          onChange={(e) => setFormData({ ...formData, room_number: e.target.value })}
                          required
                          className="transition-all focus:scale-[1.01]"
                        />
                      </motion.div>
                    </div>
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="space-y-2"
                    >
                      <Label htmlFor="threshold">告警阈值 (元)</Label>
                      <Input
                        id="threshold"
                        type="number"
                        step="0.1"
                        value={formData.threshold}
                        onChange={(e) => setFormData({ ...formData, threshold: parseFloat(e.target.value) })}
                        required
                        className="transition-all focus:scale-[1.01]"
                      />
                    </motion.div>
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.1 }}
                      className="space-y-2"
                    >
                      <Label htmlFor="email_recipients">收件人邮箱 (逗号分隔)</Label>
                      <Input
                        id="email_recipients"
                        type="email"
                        value={formData.email_recipients}
                        onChange={(e) => setFormData({ ...formData, email_recipients: e.target.value })}
                        placeholder="email1@example.com, email2@example.com"
                        className="transition-all focus:scale-[1.01]"
                      />
                    </motion.div>
                  </div>
                  <DialogFooter>
                    <Button type="submit" className="transition-all hover:scale-105">
                      创建订阅
                    </Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          </motion.div>

          <CardAnimated delay={0.2}>
            <Card className="transition-all hover:shadow-lg">
              <CardHeader>
                <CardTitle>订阅列表</CardTitle>
                <CardDescription>管理你的电费监控订阅</CardDescription>
              </CardHeader>
              <CardContent>
                {subscriptions.length === 0 ? (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-center py-12"
                  >
                    <Zap className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                    <p className="text-muted-foreground">还没有订阅</p>
                  </motion.div>
                ) : (
                  <div className="space-y-3">
                    {subscriptions.map((sub, index) => (
                      <motion.div
                        key={sub.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.3 + index * 0.05 }}
                        className="group flex flex-col gap-4 rounded-lg border bg-card p-4 transition-all hover:border-primary/50 hover:shadow-md md:flex-row md:items-center md:justify-between"
                      >
                        <div className="flex-1 space-y-2">
                          <div className="flex items-center gap-2">
                            <h3 className="font-semibold text-lg">{sub.room_name}</h3>
                            <Badge
                              variant={sub.is_active ? 'default' : 'secondary'}
                              className="transition-all group-hover:scale-105"
                            >
                              {sub.is_active ? '活跃' : '已停用'}
                            </Badge>
                          </div>
                          <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
                            <div className="flex items-center gap-1">
                              <span>阈值:</span>
                              <span className="font-medium text-foreground">{sub.threshold} 元</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <Mail className="h-4 w-4" />
                              <span>收件人:</span>
                              <span className="font-medium text-foreground">{sub.email_recipients.length} 个</span>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="destructive"
                            size="sm"
                            disabled={!sub.is_owner}
                            onClick={() => handleDelete(sub.id)}
                            className="transition-all hover:scale-105"
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            {sub.is_owner ? '删除' : '无权限'}
                          </Button>
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
    </div>
  );
}
