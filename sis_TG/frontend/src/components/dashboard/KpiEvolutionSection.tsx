import ReactECharts from 'echarts-for-react';
import * as echarts from 'echarts/core';
import type { KpiEvolutionData } from '../../types/dashboard';

interface Props {
  data: KpiEvolutionData | undefined;
}

type TrafficStatus = 'green' | 'yellow' | 'red';

const TRAFFIC_COLORS: Record<TrafficStatus, [string, string]> = {
  green:  ['#4ade80', '#16a34a'],
  yellow: ['#fcd34d', '#d97706'],
  red:    ['#f87171', '#dc2626'],
};

const TRAFFIC_HEX: Record<TrafficStatus, string> = {
  green:  '#22c55e',
  yellow: '#f59e0b',
  red:    '#ef4444',
};

const TRAFFIC_LABELS: Record<TrafficStatus, string> = {
  green:  'En meta',
  yellow: 'En progreso',
  red:    'Por debajo de meta',
};

function gradient(status: TrafficStatus) {
  const [top, bottom] = TRAFFIC_COLORS[status];
  return new echarts.graphic.LinearGradient(0, 0, 0, 1, [
    { offset: 0, color: top },
    { offset: 1, color: bottom },
  ]);
}

function formatRevenue(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M Bs`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}k Bs`;
  return `${value.toFixed(0)} Bs`;
}

function TrafficDot({ status }: { status: TrafficStatus }) {
  return (
    <span
      className="inline-block w-2.5 h-2.5 rounded-full flex-shrink-0"
      style={{ backgroundColor: TRAFFIC_HEX[status] }}
    />
  );
}

export default function KpiEvolutionSection({ data }: Props) {
  if (!data || data.monthly.length === 0) {
    return (
      <div className="bg-white rounded-xl p-5 shadow-sm">
        <h3 className="text-sm font-medium text-gray-700 mb-2">Evolución de KPIs</h3>
        <p className="text-gray-400 text-sm">Sin datos de conversiones registrados aún.</p>
      </div>
    );
  }

  const lastPoint = data.monthly[data.monthly.length - 1];
  const labels = data.monthly.map((m) => m.label);

  // ── Opciones gráfico 1: Captación de clientes ───────────────────────────────
  const clientsOption: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: '#fff',
      borderColor: '#e5e7eb',
      borderWidth: 1,
      padding: 12,
      textStyle: { fontSize: 12, color: '#374151' },
      formatter: (params: any) => {
        const bar = params.find((p: any) => p.seriesName === 'Nuevos clientes');
        const lostBar = params.find((p: any) => p.seriesName === 'Clientes perdidos');
        const line = params.find((p: any) => p.seriesName === 'Clientes acumulados');
        const entry = data.monthly[bar?.dataIndex ?? lostBar?.dataIndex ?? 0];
        const status: TrafficStatus =
          entry.new_clients >= data.thresholds.new_clients_green ? 'green'
          : entry.new_clients >= data.thresholds.new_clients_yellow ? 'yellow'
          : 'red';
        return `
          <div style="font-weight:600;margin-bottom:6px">${entry.label}</div>
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
            <span style="width:10px;height:10px;border-radius:50%;background:${TRAFFIC_HEX[status]};display:inline-block"></span>
            <span>Ganados: <b>+${entry.new_clients}</b></span>
          </div>
          ${entry.lost_clients > 0 ? `
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
            <span style="width:10px;height:10px;border-radius:50%;background:#f87171;display:inline-block"></span>
            <span>Perdidos: <b>−${entry.lost_clients}</b></span>
          </div>` : ''}
          <div style="display:flex;align-items:center;gap:8px;margin-top:4px;padding-top:4px;border-top:1px solid #f3f4f6">
            <span style="width:10px;height:10px;border-radius:50%;background:#9B1C2E;display:inline-block"></span>
            <span>Acumulado: <b>${line?.value ?? entry.cumulative_clients}</b></span>
          </div>
        `;
      },
    },
    legend: {
      bottom: 0,
      icon: 'circle',
      itemWidth: 8,
      itemHeight: 8,
      textStyle: { fontSize: 11, color: '#6b7280' },
    },
    grid: { top: 16, right: 48, bottom: 48, left: 40, containLabel: false },
    xAxis: {
      type: 'category',
      data: labels,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { fontSize: 11, color: '#6b7280', rotate: -30 },
    },
    yAxis: [
      {
        type: 'value',
        name: 'Nuevos',
        nameTextStyle: { fontSize: 10, color: '#9ca3af' },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: '#f3f4f6' } },
        axisLabel: { fontSize: 11, color: '#6b7280' },
        minInterval: 1,
      },
      {
        type: 'value',
        name: 'Acumulado',
        nameTextStyle: { fontSize: 10, color: '#9B1C2E' },
        position: 'right',
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { fontSize: 11, color: '#9B1C2E' },
        minInterval: 1,
      },
    ],
    series: [
      {
        name: 'Nuevos clientes',
        type: 'bar',
        stack: 'clients',
        yAxisIndex: 0,
        barMaxWidth: 52,
        itemStyle: { borderRadius: [6, 6, 0, 0] },
        data: data.monthly.map((m) => {
          const status: TrafficStatus =
            m.new_clients >= data.thresholds.new_clients_green ? 'green'
            : m.new_clients >= data.thresholds.new_clients_yellow ? 'yellow'
            : 'red';
          return { value: m.new_clients, itemStyle: { color: gradient(status) } };
        }),
      },
      {
        name: 'Clientes perdidos',
        type: 'bar',
        stack: 'clients',
        yAxisIndex: 0,
        barMaxWidth: 52,
        itemStyle: { borderRadius: [0, 0, 6, 6], color: gradient('red') },
        data: data.monthly.map((m) => -m.lost_clients),
      },
      {
        name: 'Clientes acumulados',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: { color: '#9B1C2E', width: 2.5 },
        itemStyle: { color: '#9B1C2E', borderWidth: 0 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(155,28,46,0.15)' },
            { offset: 1, color: 'rgba(155,28,46,0)' },
          ]),
        },
        data: data.monthly.map((m) => m.cumulative_clients),
      },
    ],
  };

  // ── Opciones gráfico 2: Ingreso estimado ────────────────────────────────────
  const revenueOption: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: '#fff',
      borderColor: '#e5e7eb',
      borderWidth: 1,
      padding: 12,
      textStyle: { fontSize: 12, color: '#374151' },
      formatter: (params: any) => {
        const bar = params.find((p: any) => p.seriesName === 'Ingreso estimado');
        const entry = data.monthly[bar?.dataIndex ?? 0];
        return `
          <div style="font-weight:600;margin-bottom:6px">${bar?.name ?? ''}</div>
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
            <span style="width:10px;height:10px;border-radius:50%;background:${TRAFFIC_HEX[entry.traffic_revenue]};display:inline-block"></span>
            <span>Ingreso estimado: <b>${formatRevenue(entry.estimated_revenue)}</b></span>
          </div>
          <div style="color:#9ca3af;margin-top:4px;font-size:11px">
            ${entry.cumulative_clients} clientes activos · ${TRAFFIC_LABELS[entry.traffic_revenue]}
          </div>
        `;
      },
    },
    grid: { top: 24, right: 24, bottom: 48, left: 16, containLabel: true },
    xAxis: {
      type: 'category',
      data: labels,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { fontSize: 11, color: '#6b7280', rotate: -30 },
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: '#f3f4f6' } },
      axisLabel: {
        fontSize: 11,
        color: '#6b7280',
        formatter: (v: number) => formatRevenue(v),
      },
    },
    series: [
      {
        name: 'Ingreso estimado',
        type: 'bar',
        barMaxWidth: 52,
        itemStyle: { borderRadius: [6, 6, 0, 0] },
        data: data.monthly.map((m) => ({
          value: m.estimated_revenue,
          itemStyle: { color: gradient(m.traffic_revenue) },
        })),
        markLine: {
          silent: true,
          symbol: 'none',
          label: { fontSize: 10 },
          data: [
            {
              yAxis: data.thresholds.revenue_green,
              name: 'Meta alta',
              lineStyle: { color: '#374151', type: 'dashed', width: 1.5 },
              label: {
                formatter: `Meta alta (${formatRevenue(data.thresholds.revenue_green)})`,
                position: 'insideEndTop',
                color: '#374151',
                fontSize: 10,
              },
            },
            {
              yAxis: data.thresholds.revenue_yellow,
              name: 'Meta mínima',
              lineStyle: { color: '#9ca3af', type: 'dashed', width: 1.5 },
              label: {
                formatter: `Meta mínima (${formatRevenue(data.thresholds.revenue_yellow)})`,
                position: 'insideEndTop',
                color: '#9ca3af',
                fontSize: 10,
              },
            },
          ],
        },
      },
    ],
  };

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <h3 className="text-base font-semibold text-gray-800">Evolución de KPIs Comerciales</h3>
        <p className="text-xs text-gray-400">
          Ingreso estimado basado en consumo promedio por cliente (Tabla 13, ICP)
        </p>
      </div>

      {/* ── Tarjetas resumen ── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <SummaryCard
          label="Clientes activos"
          value={lastPoint.cumulative_clients.toString()}
          sub="acumulado total"
          traffic={lastPoint.traffic_clients}
          thresholdGreen={data.thresholds.clients_green}
          thresholdYellow={data.thresholds.clients_yellow}
          formatFn={(v) => `${v} clientes`}
        />
        <SummaryCard
          label="Ingreso estimado mensual"
          value={formatRevenue(lastPoint.estimated_revenue)}
          sub="basado en clientes activos"
          traffic={lastPoint.traffic_revenue}
          thresholdGreen={data.thresholds.revenue_green}
          thresholdYellow={data.thresholds.revenue_yellow}
          formatFn={formatRevenue}
        />
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <p className="text-xs text-gray-500 mb-1">Ingreso promedio por cliente</p>
          <p className="text-xl font-bold text-gray-800">
            {formatRevenue(data.avg_revenue_per_client)}
            <span className="text-xs font-normal text-gray-400 ml-1">/mes</span>
          </p>
          <p className="text-xs text-gray-400 mt-2">Estimado según catálogo Don Piotr</p>
          <details className="mt-3">
            <summary className="text-xs text-primary-600 cursor-pointer hover:underline select-none">
              Ver desglose por producto
            </summary>
            <table className="mt-2 w-full text-xs text-gray-600">
              <thead>
                <tr className="text-gray-400 border-b">
                  <th className="text-left pb-1 font-normal">Producto</th>
                  <th className="text-right pb-1 font-normal">Aporte est.</th>
                </tr>
              </thead>
              <tbody>
                {data.product_details.map((p) => (
                  <tr key={p.nombre} className="border-b border-gray-50">
                    <td className="py-0.5">{p.nombre}</td>
                    <td className="text-right py-0.5 tabular-nums">
                      {formatRevenue(p.ingreso_esperado_por_cliente)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </details>
        </div>
      </div>

      {/* ── Gráfico 1: Captación de clientes ── */}
      <div className="bg-white rounded-xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-sm font-medium text-gray-700">Captación de Clientes por Mes</h4>
          <div className="flex flex-wrap gap-3 text-xs text-gray-500">
            {(['green', 'yellow', 'red'] as TrafficStatus[]).map((s) => (
              <span key={s} className="flex items-center gap-1">
                <TrafficDot status={s} />
                {TRAFFIC_LABELS[s]}
              </span>
            ))}
          </div>
        </div>
        <ReactECharts option={clientsOption} style={{ height: 280 }} />
      </div>

      {/* ── Gráfico 2: Ingreso estimado ── */}
      <div className="bg-white rounded-xl p-5 shadow-sm">
        <div className="flex items-start justify-between mb-2">
          <div>
            <h4 className="text-sm font-medium text-gray-700">Ingreso Mensual Estimado (Bs)</h4>
            <p className="text-xs text-gray-400 mt-0.5">
              Clientes activos × {formatRevenue(data.avg_revenue_per_client)} promedio por cliente
            </p>
          </div>
          <div className="flex flex-col gap-1 text-xs text-gray-500 items-end">
            {(['green', 'yellow', 'red'] as TrafficStatus[]).map((s) => (
              <span key={s} className="flex items-center gap-1">
                <TrafficDot status={s} />
                {TRAFFIC_LABELS[s]}
              </span>
            ))}
          </div>
        </div>
        <ReactECharts option={revenueOption} style={{ height: 280 }} />
      </div>
    </div>
  );
}

// ── Tarjeta resumen ───────────────────────────────────────────────────────────
interface SummaryCardProps {
  label: string;
  value: string;
  sub: string;
  traffic: TrafficStatus;
  thresholdGreen: number;
  thresholdYellow: number;
  formatFn: (v: number) => string;
}

function SummaryCard({ label, value, sub, traffic, thresholdGreen, thresholdYellow, formatFn }: SummaryCardProps) {
  const borderColor = { green: 'border-green-200', yellow: 'border-yellow-200', red: 'border-red-200' }[traffic];
  return (
    <div className={`bg-white rounded-xl p-4 shadow-sm border ${borderColor}`}>
      <div className="flex items-center justify-between mb-1">
        <p className="text-xs text-gray-500">{label}</p>
        <TrafficDot status={traffic} />
      </div>
      <p className="text-2xl font-bold text-gray-800 tabular-nums">{value}</p>
      <p className="text-xs text-gray-400 mt-0.5">{sub}</p>
      <div className="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-400 space-y-1">
        <div className="flex items-center gap-1.5">
          <TrafficDot status="green" />
          <span>Meta: ≥ {formatFn(thresholdGreen)}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <TrafficDot status="yellow" />
          <span>Aceptable: ≥ {formatFn(thresholdYellow)}</span>
        </div>
      </div>
    </div>
  );
}
