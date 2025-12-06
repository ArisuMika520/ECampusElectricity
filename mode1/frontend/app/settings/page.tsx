'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Navbar from '@/components/layout/navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import api from '@/lib/api';
import { isAuthenticated } from '@/lib/auth';

export default function SettingsPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [config, setConfig] = useState({
    shiroJID: '',
    smtp_server: 'smtp.qq.com',
    smtp_port: 465,
    smtp_user: '',
    smtp_pass: '',
    from_email: '',
    use_tls: false,
  });

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }
    fetchConfig();
  }, [router]);

  const fetchConfig = async () => {
    try {
      const response = await api.get('/api/config');
      const configs = response.data;
      
      const newConfig: any = {};
      configs.forEach((item: any) => {
        if (item.key in config) {
          newConfig[item.key] = item.value.value || item.value;
        }
      });
      
      setConfig({ ...config, ...newConfig });
    } catch (error) {
      console.error('Failed to fetch config:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (key: string, value: any) => {
    setSaving(true);
    try {
      await api.put(`/api/config/${key}`, { value: { value } });
      alert('保存成功');
    } catch (error: any) {
      alert(error.response?.data?.detail || '保存失败');
    } finally {
      setSaving(false);
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
        <h1 className="mb-6 text-3xl font-bold">系统设置</h1>

        <Card className="mb-6">
          <CardHeader>
            <CardTitle>电费API配置</CardTitle>
            <CardDescription>配置易校园API认证信息</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="shiroJID">ShiroJID</Label>
              <Input
                id="shiroJID"
                type="password"
                value={config.shiroJID}
                onChange={(e) => setConfig({ ...config, shiroJID: e.target.value })}
                placeholder="输入 shiroJID"
              />
              <Button
                onClick={() => handleSave('shiroJID', config.shiroJID)}
                disabled={saving}
              >
                保存
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>SMTP邮件配置</CardTitle>
            <CardDescription>配置邮件服务器用于发送告警</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="smtp_server">SMTP服务器</Label>
                <Input
                  id="smtp_server"
                  value={config.smtp_server}
                  onChange={(e) => setConfig({ ...config, smtp_server: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="smtp_port">SMTP端口</Label>
                <Input
                  id="smtp_port"
                  type="number"
                  value={config.smtp_port}
                  onChange={(e) => setConfig({ ...config, smtp_port: parseInt(e.target.value) })}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="smtp_user">SMTP用户名</Label>
              <Input
                id="smtp_user"
                value={config.smtp_user}
                onChange={(e) => setConfig({ ...config, smtp_user: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="smtp_pass">SMTP密码</Label>
              <Input
                id="smtp_pass"
                type="password"
                value={config.smtp_pass}
                onChange={(e) => setConfig({ ...config, smtp_pass: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="from_email">发件人邮箱</Label>
              <Input
                id="from_email"
                type="email"
                value={config.from_email}
                onChange={(e) => setConfig({ ...config, from_email: e.target.value })}
              />
            </div>
            <Button
              onClick={() => {
                handleSave('smtp_server', config.smtp_server);
                handleSave('smtp_port', config.smtp_port);
                handleSave('smtp_user', config.smtp_user);
                handleSave('smtp_pass', config.smtp_pass);
                handleSave('from_email', config.from_email);
                handleSave('use_tls', config.use_tls);
              }}
              disabled={saving}
            >
              保存SMTP配置
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}



