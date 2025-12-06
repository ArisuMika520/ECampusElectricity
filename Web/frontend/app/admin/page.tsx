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
import { Switch } from '@/components/ui/switch';
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
    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }

    fetchCurrentUser();
    fetchUsers();
    fetchSystemConfig();
  }, [router]);

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
      const response = await api.get('/api/admin/users');
      setUsers(response.data);
    } catch (error) {
      console.error('Failed to fetch users:', error);
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
      <div>
        <Navbar />
        <div className="container mx-auto p-4">加载中...</div>
      </div>
    );
  }

  if (!currentUser?.is_admin) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="container mx-auto p-6">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-3xl font-bold">管理员面板</h1>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button>创建用户</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>创建新用户</DialogTitle>
                <DialogDescription>创建新的系统用户</DialogDescription>
              </DialogHeader>
              <form onSubmit={handleCreateUser}>
                <div className="grid gap-4 py-4">
                  <div className="space-y-2">
                    <Label htmlFor="username">用户名</Label>
                    <Input
                      id="username"
                      value={formData.username}
                      onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">邮箱</Label>
                    <Input
                      id="email"
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="password">密码</Label>
                    <Input
                      id="password"
                      type="password"
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      required
                    />
                  </div>
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="is_admin"
                      checked={formData.is_admin}
                      onCheckedChange={(checked) => setFormData({ ...formData, is_admin: checked })}
                    />
                    <Label htmlFor="is_admin">管理员权限</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="is_active"
                      checked={formData.is_active}
                      onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
                    />
                    <Label htmlFor="is_active">激活状态</Label>
                  </div>
                </div>
                <DialogFooter>
                  <Button type="submit">创建</Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        <Card className="mb-6">
          <CardHeader>
            <CardTitle>系统配置</CardTitle>
            <CardDescription>管理系统设置</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="allow_registration">允许用户注册</Label>
                <p className="text-sm text-gray-500">开启后，用户可以通过注册页面创建账号</p>
              </div>
              <Switch
                id="allow_registration"
                checked={allowRegistration}
                onCheckedChange={handleToggleRegistration}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>用户管理</CardTitle>
            <CardDescription>管理系统中的所有用户</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {users.map((user) => (
                <div
                  key={user.id}
                  className="flex items-center justify-between rounded-lg border p-4"
                >
                  <div>
                    <div className="font-semibold">{user.username}</div>
                    <div className="text-sm text-gray-500">{user.email}</div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {user.is_admin && (
                      <Badge variant="default">管理员</Badge>
                    )}
                    <Badge variant={user.is_active ? 'default' : 'secondary'}>
                      {user.is_active ? '活跃' : '已停用'}
                    </Badge>
                    {user.id !== currentUser?.id && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleToggleUserStatus(user.id, user.is_active)}
                      >
                        {user.is_active ? '停用' : '启用'}
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}



