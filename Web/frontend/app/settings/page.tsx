'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Save, Settings as SettingsIcon, Mail, Key, RefreshCw, CheckCircle2 } from 'lucide-react';
import Navbar from '@/components/layout/navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { PageTransition } from '@/components/ui/page-transition';
import { CardAnimated } from '@/components/ui/card-animated';
import api from '@/lib/api';
import { isAuthenticated } from '@/lib/auth';

export default function SettingsPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savedKey, setSavedKey] = useState<string | null>(null);
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
      await fetchConfig();
    };
    
    checkAuth();
  }, []);

  const fetchConfig = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/config');
      const configs = response.data || [];

      const newConfig: any = {};
      configs.forEach((item: any) => {
        if (item.key in config) {
          newConfig[item.key] = item.value.value || item.value;
        }
      });
      
      setConfig((prev) => ({ ...prev, ...newConfig }));
    } catch (error) {
      console.error('Failed to fetch config:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (key: string, value: any) => {
    setSaving(true);
    setSavedKey(key);
    try {
      await api.put(`/api/config/${key}`, { value: { value } });
      setTimeout(() => setSavedKey(null), 2000);
    } catch (error: any) {
      alert(error.response?.data?.detail || '保存失败');
      setSavedKey(null);
    } finally {
      setSaving(false);
    }
  };

  const handleSaveAllSMTP = async () => {
    setSaving(true);
    try {
      await Promise.all([
        handleSave('smtp_server', config.smtp_server),
        handleSave('smtp_port', config.smtp_port),
        handleSave('smtp_user', config.smtp_user),
        handleSave('smtp_pass', config.smtp_pass),
        handleSave('from_email', config.from_email),
        handleSave('use_tls', config.use_tls),
      ]);
    } finally {
      setSaving(false);
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
            className="flex items-center gap-3"
          >
            <SettingsIcon className="h-8 w-8 text-primary" />
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
                系统设置
              </h1>
              <p className="text-muted-foreground text-sm mt-1">
                配置系统参数和邮件服务
              </p>
            </div>
          </motion.div>

          <CardAnimated delay={0.1}>
            <Card className="transition-all hover:shadow-lg">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Key className="h-5 w-5 text-primary" />
                  <CardTitle>电费API配置</CardTitle>
                </div>
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
                    className="transition-all focus:scale-[1.01]"
                  />
                  <Button
                    onClick={() => handleSave('shiroJID', config.shiroJID)}
                    disabled={saving}
                    className="transition-all hover:scale-105"
                  >
                    {savedKey === 'shiroJID' ? (
                      <>
                        <CheckCircle2 className="h-4 w-4 mr-2" />
                        已保存
                      </>
                    ) : (
                      <>
                        <Save className="h-4 w-4 mr-2" />
                        保存
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </CardAnimated>

          <CardAnimated delay={0.2}>
            <Card className="transition-all hover:shadow-lg">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Mail className="h-5 w-5 text-primary" />
                  <CardTitle>SMTP邮件配置</CardTitle>
                </div>
                <CardDescription>配置邮件服务器用于发送告警</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="smtp_server">SMTP服务器</Label>
                    <Input
                      id="smtp_server"
                      value={config.smtp_server}
                      onChange={(e) => setConfig({ ...config, smtp_server: e.target.value })}
                      className="transition-all focus:scale-[1.01]"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="smtp_port">SMTP端口</Label>
                    <Input
                      id="smtp_port"
                      type="number"
                      value={config.smtp_port}
                      onChange={(e) => setConfig({ ...config, smtp_port: parseInt(e.target.value) })}
                      className="transition-all focus:scale-[1.01]"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="smtp_user">SMTP用户名</Label>
                  <Input
                    id="smtp_user"
                    value={config.smtp_user}
                    onChange={(e) => setConfig({ ...config, smtp_user: e.target.value })}
                    className="transition-all focus:scale-[1.01]"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="smtp_pass">SMTP密码</Label>
                  <Input
                    id="smtp_pass"
                    type="password"
                    value={config.smtp_pass}
                    onChange={(e) => setConfig({ ...config, smtp_pass: e.target.value })}
                    className="transition-all focus:scale-[1.01]"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="from_email">发件人邮箱</Label>
                  <Input
                    id="from_email"
                    type="email"
                    value={config.from_email}
                    onChange={(e) => setConfig({ ...config, from_email: e.target.value })}
                    className="transition-all focus:scale-[1.01]"
                  />
                </div>
                <Button
                  onClick={handleSaveAllSMTP}
                  disabled={saving}
                  className="transition-all hover:scale-105"
                >
                  {savedKey && savedKey.startsWith('smtp') ? (
                    <>
                      <CheckCircle2 className="h-4 w-4 mr-2" />
                      已保存
                    </>
                  ) : (
                    <>
                      <Save className="h-4 w-4 mr-2" />
                      保存SMTP配置
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          </CardAnimated>
        </div>
      </PageTransition>
    </div>
  );
}
