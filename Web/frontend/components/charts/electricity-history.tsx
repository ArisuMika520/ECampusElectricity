'use client'

import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts"
import { useTheme } from "next-themes"
import { useEffect, useState } from "react"

type HistoryPoint = {
  timestamp: string | number | Date
  surplus: number
}

interface Props {
  data: HistoryPoint[]
  height?: number
}

export function ElectricityHistoryChart({ data, height = 320 }: Props) {
  const { theme } = useTheme()
  const [isDark, setIsDark] = useState(false)
  
  useEffect(() => {
    // 检测当前主题
    const checkTheme = () => {
      if (typeof window === 'undefined') return
      
      if (theme === 'dark') {
        setIsDark(true)
      } else if (theme === 'light') {
        setIsDark(false)
      } else if (theme === 'system') {
        setIsDark(window.matchMedia('(prefers-color-scheme: dark)').matches)
      }
    }
    
    checkTheme()
    
    // 监听系统主题变化
    if (theme === 'system' && typeof window !== 'undefined') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      const handleChange = (e: MediaQueryListEvent) => setIsDark(e.matches)
      mediaQuery.addEventListener('change', handleChange)
      return () => mediaQuery.removeEventListener('change', handleChange)
    }
  }, [theme])

  const formatted = (data || []).map((d) => ({
    time: new Date(d.timestamp).toLocaleString("zh-CN"),
    surplus: d.surplus,
  }))
  
  const tooltipStyle = {
    backgroundColor: isDark ? 'oklch(0.205 0 0)' : 'oklch(1 0 0)',
    border: `1px solid ${isDark ? 'oklch(1 0 0 / 10%)' : 'oklch(0.922 0 0)'}`,
    borderRadius: '0.5rem',
    color: isDark ? 'oklch(0.985 0 0)' : 'oklch(0.145 0 0)',
    padding: '0.5rem',
  }

  const tickStyle = {
    fill: isDark ? 'oklch(0.708 0 0)' : 'oklch(0.556 0 0)',
    fontSize: '12px',
  }

  const gridStroke = isDark ? 'oklch(1 0 0 / 10%)' : 'oklch(0.922 0 0)'
  const textColor = isDark ? 'oklch(0.985 0 0)' : 'oklch(0.145 0 0)'

  return (
    <div style={{ width: "100%", height }}>
      <ResponsiveContainer>
        <AreaChart data={formatted}>
          <defs>
            <linearGradient id="surplusGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
          <XAxis dataKey="time" minTickGap={20} tick={tickStyle} />
          <YAxis tick={tickStyle} />
          <Tooltip 
            contentStyle={tooltipStyle} 
            wrapperStyle={tooltipStyle}
            labelStyle={{ color: textColor }}
            itemStyle={{ color: textColor }}
          />
          <Area type="monotone" dataKey="surplus" stroke="#3b82f6" fillOpacity={1} fill="url(#surplusGradient)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}


