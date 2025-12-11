import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts"

type HistoryPoint = {
  timestamp: string | number | Date
  surplus: number
}

interface Props {
  data: HistoryPoint[]
  height?: number
}

export function ElectricityHistoryChart({ data, height = 320 }: Props) {
  const formatted = (data || []).map((d) => ({
    time: new Date(d.timestamp).toLocaleString("zh-CN"),
    surplus: d.surplus,
  }))

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
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" minTickGap={20} />
          <YAxis />
          <Tooltip />
          <Area type="monotone" dataKey="surplus" stroke="#3b82f6" fillOpacity={1} fill="url(#surplusGradient)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
