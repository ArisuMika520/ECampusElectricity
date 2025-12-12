'use client';

import { motion } from 'framer-motion';
import { ReactNode } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './card';
import { cn } from '@/lib/utils';

interface CardAnimatedProps {
  children: ReactNode;
  delay?: number;
  className?: string;
}

export function CardAnimated({ children, delay = 0, className }: CardAnimatedProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay, ease: 'easeOut' }}
      className={cn('h-full', className)}
    >
      {children}
    </motion.div>
  );
}

interface StatCardProps {
  title: string;
  description?: string;
  value: string | number;
  icon?: ReactNode;
  delay?: number;
  trend?: {
    value: number;
    isPositive: boolean;
  };
}

export function StatCard({ title, description, value, icon, delay = 0, trend }: StatCardProps) {
  return (
    <CardAnimated delay={delay}>
      <Card className="h-full transition-all hover:shadow-lg hover:scale-[1.02]">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-medium">{title}</CardTitle>
            {icon && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: delay + 0.2, type: 'spring', stiffness: 200 }}
                className="text-muted-foreground"
              >
                {icon}
              </motion.div>
            )}
          </div>
          {description && <CardDescription>{description}</CardDescription>}
        </CardHeader>
        <CardContent>
          <div className="flex items-baseline justify-between">
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: delay + 0.1 }}
              className="text-3xl font-bold"
            >
              {value}
            </motion.div>
            {trend && (
              <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: delay + 0.3 }}
                className={cn(
                  'text-sm font-medium',
                  trend.isPositive ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                )}
              >
                {trend.isPositive ? '+' : ''}{trend.value}%
              </motion.span>
            )}
          </div>
        </CardContent>
      </Card>
    </CardAnimated>
  );
}



