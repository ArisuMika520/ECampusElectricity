'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import Navbar from '@/components/layout/navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import api from '@/lib/api';
import { isAuthenticated } from '@/lib/auth';

const ALLOWED_KEYS = [
  'SHIRO_JID',
  'SMTP_SERVER',
  'SMTP_PORT',
  'SMTP_USER',
  'SMTP_PASS',
  'FROM_EMAIL',
];

export default function SettingsPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [envConfig, setEnvConfig] = useState<Record<string, any>>({});
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }
    fetchConfig();
  }, [router]);

  const fetchConfig = async () => {
    try {
      const me = await api.get('/api/auth/me');
      setIsAdmin(me.data.is_admin);
      if (!me.data.is_admin) {
        router.push('/dashboard');
        return;
      }
      const response = await api.get('/api/admin/env');
      const filtered: Record<string, any> = {};
      ALLOWED_KEYS.forEach((k) => {
        if (response.data.hasOwnProperty(k)) {
          filtered[k] = response.data[k] ?? '';
        }
      });
      setEnvConfig(filtered);
    } catch (error) {
      console.error('Failed to fetch config:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put('/api/admin/env', envConfig);
      alert('保存成功（需要重启服务生效）');
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

        {!isAdmin ? (
          <div className="text-red-600">需要管理员权限</div>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle>系统环境参数</CardTitle>
              <CardDescription>仅展示关键参数（邮箱配置、ShiroJID），保存后需重启生效</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {ALLOWED_KEYS.map((key) => {
                const hints: Record<string, string> = {
                  SHIRO_JID: '易校园登录凭证，必填，否则无法查询电费',
                  SMTP_SERVER: '邮件服务器地址，如 smtp.qq.com',
                  SMTP_PORT: '邮件服务器端口，如 465',
                  SMTP_USER: '邮件登录用户名/邮箱',
                  SMTP_PASS: '邮件授权码/密码',
                  FROM_EMAIL: '邮件发件人地址',
                };
                return (
                  <div key={key} className="space-y-1">
                    <Label htmlFor={key}>{key}</Label>
                    <Input
                      id={key}
                      value={envConfig[key] ?? ''}
                      onChange={(e) => setEnvConfig({ ...envConfig, [key]: e.target.value })}
                    />
                    <p className="text-xs text-gray-500">{hints[key]}</p>
                  </div>
                );
              })}
              <Button onClick={handleSave} disabled={saving}>
                保存（需重启）
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}



