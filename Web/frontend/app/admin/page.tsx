'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Users, UserPlus, Settings, Shield, UserCheck, UserX, RefreshCw } from 'lucide-react';
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
import { Switch } from '@/components/ui/switch';
import { PageTransition } from '@/components/ui/page-transition';
import { CardAnimated } from '@/components/ui/card-animated';
import api from '@/lib/api';
import { isAuthenticated } from '@/lib/auth';

interface User {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
}

export default function AdminPage() {
  const router = useRouter();
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [allowRegistration, setAllowRegistration] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    is_admin: false,
    is_active: true,
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
      await fetchCurrentUser();
      await fetchUsers();
      await fetchSystemConfig();
    };
    
    checkAuth();
  }, []);

  const fetchCurrentUser = async () => {
    try {
      const response = await api.get('/api/auth/me');
      setCurrentUser(response.data);
      if (!response.data.is_admin) {
        router.push('/dashboard');
      }
    } catch (error) {
      console.error('Failed to fetch current user:', error);
      router.push('/login');
    }
  };

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/admin/users');
      setUsers(response.data || []);
    } catch (error) {
      console.error('Failed to fetch users:', error);
      setUsers([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchSystemConfig = async () => {
    try {
      const response = await api.get('/api/admin/system/config');
      setAllowRegistration(response.data.allow_registration);
    } catch (error) {
      console.error('Failed to fetch system config:', error);
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/api/admin/users', formData);
      setDialogOpen(false);
      setFormData({
        username: '',
        email: '',
        password: '',
        is_admin: false,
        is_active: true,
      });
      fetchUsers();
    } catch (error: any) {
      alert(error.response?.data?.detail || '创建用户失败');
    }
  };

  const handleToggleRegistration = async (checked: boolean) => {
    try {
      await api.put('/api/admin/system/config', {
        allow_registration: checked,
      });
      setAllowRegistration(checked);
    } catch (error: any) {
      alert(error.response?.data?.detail || '更新配置失败');
    }
  };

  const handleToggleUserStatus = async (userId: string, isActive: boolean) => {
    try {
      await api.put(`/api/admin/users/${userId}`, {
        is_active: !isActive,
      });
      fetchUsers();
    } catch (error: any) {
      alert(error.response?.data?.detail || '更新用户状态失败');
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

  if (!currentUser?.is_admin) {
    return null;
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
              <Shield className="h-8 w-8 text-primary" />
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
                  管理员面板
                </h1>
                <p className="text-muted-foreground text-sm mt-1">
                  管理系统用户和配置
                </p>
              </div>
            </div>
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button className="transition-all hover:scale-105">
                  <UserPlus className="h-4 w-4 mr-2" />
                  创建用户
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>创建新用户</DialogTitle>
                  <DialogDescription>创建新的系统用户</DialogDescription>
                </DialogHeader>
                <form onSubmit={handleCreateUser}>
                  <div className="grid gap-4 py-4">
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="space-y-2"
                    >
                      <Label htmlFor="username">用户名</Label>
                      <Input
                        id="username"
                        value={formData.username}
                        onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                        required
                        className="transition-all focus:scale-[1.01]"
                      />
                    </motion.div>
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.1 }}
                      className="space-y-2"
                    >
                      <Label htmlFor="email">邮箱</Label>
                      <Input
                        id="email"
                        type="email"
                        value={formData.email}
                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                        required
                        className="transition-all focus:scale-[1.01]"
                      />
                    </motion.div>
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.2 }}
                      className="space-y-2"
                    >
                      <Label htmlFor="password">密码</Label>
                      <Input
                        id="password"
                        type="password"
                        value={formData.password}
                        onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                        required
                        className="transition-all focus:scale-[1.01]"
                      />
                    </motion.div>
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.3 }}
                      className="flex items-center space-x-2"
                    >
                      <Switch
                        id="is_admin"
                        checked={formData.is_admin}
                        onCheckedChange={(checked) => setFormData({ ...formData, is_admin: checked })}
                      />
                      <Label htmlFor="is_admin">管理员权限</Label>
                    </motion.div>
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.4 }}
                      className="flex items-center space-x-2"
                    >
                      <Switch
                        id="is_active"
                        checked={formData.is_active}
                        onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
                      />
                      <Label htmlFor="is_active">激活状态</Label>
                    </motion.div>
                  </div>
                  <DialogFooter>
                    <Button type="submit" className="transition-all hover:scale-105">
                      创建
                    </Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          </motion.div>

          <CardAnimated delay={0.1}>
            <Card className="transition-all hover:shadow-lg">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Settings className="h-5 w-5 text-primary" />
                  <CardTitle>系统配置</CardTitle>
                </div>
                <CardDescription>管理系统设置</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="allow_registration">允许用户注册</Label>
                    <p className="text-sm text-muted-foreground mt-1">
                      开启后，用户可以通过注册页面创建账号
                    </p>
                  </div>
                  <Switch
                    id="allow_registration"
                    checked={allowRegistration}
                    onCheckedChange={handleToggleRegistration}
                  />
                </div>
              </CardContent>
            </Card>
          </CardAnimated>

          <CardAnimated delay={0.2}>
            <Card className="transition-all hover:shadow-lg">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Users className="h-5 w-5 text-primary" />
                  <CardTitle>用户管理</CardTitle>
                </div>
                <CardDescription>管理系统中的所有用户</CardDescription>
              </CardHeader>
              <CardContent>
                {users.length === 0 ? (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-center py-12"
                  >
                    <Users className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                    <p className="text-muted-foreground">暂无用户</p>
                  </motion.div>
                ) : (
                  <div className="space-y-3">
                    {users.map((user, index) => (
                      <motion.div
                        key={user.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.3 + index * 0.05 }}
                        className="group flex flex-col gap-4 rounded-lg border bg-card p-4 transition-all hover:border-primary/50 hover:shadow-md md:flex-row md:items-center md:justify-between"
                      >
                        <div className="flex-1 space-y-1">
                          <div className="flex items-center gap-2">
                            <div className="font-semibold text-lg">{user.username}</div>
                            {user.is_admin && (
                              <Badge variant="default" className="transition-all group-hover:scale-105">
                                <Shield className="h-3 w-3 mr-1" />
                                管理员
                              </Badge>
                            )}
                            <Badge
                              variant={user.is_active ? 'default' : 'secondary'}
                              className="transition-all group-hover:scale-105"
                            >
                              {user.is_active ? (
                                <>
                                  <UserCheck className="h-3 w-3 mr-1" />
                                  活跃
                                </>
                              ) : (
                                <>
                                  <UserX className="h-3 w-3 mr-1" />
                                  已停用
                                </>
                              )}
                            </Badge>
                          </div>
                          <div className="text-sm text-muted-foreground">{user.email}</div>
                        </div>
                        <div className="flex items-center gap-2">
                          {user.id !== currentUser?.id && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleToggleUserStatus(user.id, user.is_active)}
                              className="transition-all hover:scale-105"
                            >
                              {user.is_active ? (
                                <>
                                  <UserX className="h-4 w-4 mr-2" />
                                  停用
                                </>
                              ) : (
                                <>
                                  <UserCheck className="h-4 w-4 mr-2" />
                                  启用
                                </>
                              )}
                            </Button>
                          )}
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



