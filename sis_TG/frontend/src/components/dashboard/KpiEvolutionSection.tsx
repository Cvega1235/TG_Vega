import { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import ReactECharts from 'echarts-for-react';
import type EChartsReact from 'echarts-for-react';
import * as echarts from 'echarts/core';
import type { KpiEvolutionData, KpiSettings } from '../../types/dashboard';
import { getClientsByMonth, getKpiSettings, updateKpiSettings } from '../../api/dashboard';

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
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedMonth, setSelectedMonth] = useState<string | null>(null);
  const [editingGoals, setEditingGoals] = useState(false);
  const [goalsForm, setGoalsForm] = useState<KpiSettings | null>(null);
  const chartRef = useRef<EChartsReact>(null);

  const { data: kpiSettings } = useQuery({
    queryKey: ['kpiSettings'],
    queryFn: getKpiSettings,
  });

  const settingsMutation = useMutation({
    mutationFn: updateKpiSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['kpiSettings'] });
      queryClient.invalidateQueries({ queryKey: ['kpiEvolution'] });
      setEditingGoals(false);
    },
  });

  const { data: monthClients, isLoading: loadingClients } = useQuery({
    queryKey: ['clientsByMonth', selectedMonth],
    queryFn: () => getClientsByMonth(selectedMonth!),
    enabled: selectedMonth !== null,
  });

  useEffect(() => {
    if (!data) return;
    const instance = chartRef.current?.getEchartsInstance();
    if (!instance) return;
    const handler = (params: any) => {
      if (params.componentType === 'series' && params.dataIndex != null) {
        const month = data.monthly[params.dataIndex]?.month ?? null;
        if (month) setSelectedMonth((prev) => (prev === month ? null : month));
      }
    };
    instance.on('click', handler);
    return () => { instance.off('click', handler); };
  }, [data?.monthly]);

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

  const selectedLabel = selectedMonth
    ? data.monthly.find((m) => m.month === selectedMonth)?.label ?? selectedMonth
    : null;

  const maxClients = kpiSettings?.max_clients ?? 72;
  const maxKgDay = kpiSettings?.max_kg_day ?? 40;
  const alertClients = Math.floor(maxClients * 0.9);
  const currentClients = lastPoint.cumulative_clients;
  const utilization = currentClients / maxClients;
  const utilizationPct = Math.min(100, Math.round(utilization * 100));
  const currentKgDay = Math.round(utilization * maxKgDay * 10) / 10;
  const utilizationTraffic: TrafficStatus =
    utilization >= 0.9 ? 'red' : utilization >= 0.7 ? 'yellow' : 'green';
  const showCapacityWarning = utilization >= 0.9;

  // ── Opciones gráfico 1: Captación de clientes ───────────────────────────────
  const clientsOption: echarts.EChartsCoreOption = {
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
          <div style="margin-top:6px;color:#9B1C2E;font-size:11px">Haz clic para ver clientes de este mes</div>
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
        markLine: {
          silent: true,
          symbol: 'none',
          data: [
            {
              yAxis: maxClients,
              name: 'Cap. máxima',
              lineStyle: { color: '#dc2626', type: 'dashed', width: 1.5 },
              label: {
                formatter: `Cap. máxima (${maxClients})`,
                position: 'insideEndTop',
                color: '#dc2626',
                fontSize: 10,
              },
            },
            {
              yAxis: alertClients,
              name: 'Alerta 90%',
              lineStyle: { color: '#f59e0b', type: 'dashed', width: 1.5 },
              label: {
                formatter: `Alerta 90% (${alertClients})`,
                position: 'insideEndBottom',
                color: '#f59e0b',
                fontSize: 10,
              },
            },
          ],
        },
      },
    ],
  };

  // ── Opciones gráfico 2: Ventas por mes ──────────────────────────────────────
  const revenueOption: echarts.EChartsCoreOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: '#fff',
      borderColor: '#e5e7eb',
      borderWidth: 1,
      padding: 12,
      textStyle: { fontSize: 12, color: '#374151' },
      formatter: (params: any) => {
        const anyParam = params.find((p: any) => p.dataIndex != null) ?? params[0];
        const idx = anyParam?.dataIndex ?? 0;
        const entry = data.monthly[idx];
        return `
          <div style="font-weight:600;margin-bottom:6px">${entry.label}</div>
          ${entry.revenue_gained > 0 ? `
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
            <span style="width:10px;height:10px;border-radius:50%;background:${TRAFFIC_HEX[entry.traffic_revenue]};display:inline-block"></span>
            <span>Ingresos nuevos: <b>+${formatRevenue(entry.revenue_gained)}</b></span>
          </div>` : ''}
          ${entry.revenue_lost > 0 ? `
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
            <span style="width:10px;height:10px;border-radius:50%;background:#f87171;display:inline-block"></span>
            <span>Ingresos perdidos: <b>−${formatRevenue(entry.revenue_lost)}</b></span>
          </div>` : ''}
          <div style="display:flex;align-items:center;gap:8px;margin-top:4px;padding-top:4px;border-top:1px solid #f3f4f6">
            <span style="width:10px;height:10px;border-radius:50%;background:#9B1C2E;display:inline-block"></span>
            <span>Ventas acumuladas: <b>${formatRevenue(entry.estimated_revenue)}</b></span>
          </div>
          <div style="color:#9ca3af;margin-top:4px;font-size:11px">
            ${entry.cumulative_clients} clientes activos · ${TRAFFIC_LABELS[entry.traffic_revenue]}
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
    grid: { top: 16, right: 64, bottom: 48, left: 40, containLabel: false },
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
        name: 'Variación',
        nameTextStyle: { fontSize: 10, color: '#9ca3af' },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: '#f3f4f6' } },
        axisLabel: { fontSize: 11, color: '#6b7280', formatter: (v: number) => formatRevenue(Math.abs(v)) },
      },
      {
        type: 'value',
        name: 'Acumulado',
        nameTextStyle: { fontSize: 10, color: '#9B1C2E' },
        position: 'right',
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { fontSize: 11, color: '#9B1C2E', formatter: (v: number) => formatRevenue(v) },
      },
    ],
    series: [
      {
        name: 'Ventas acumuladas',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: { color: '#9B1C2E', width: 2.5 },
        itemStyle: { color: '#9B1C2E', borderWidth: 0 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(155,28,46,0.07)' },
            { offset: 1, color: 'rgba(155,28,46,0)' },
          ]),
        },
        data: data.monthly.map((m) => m.estimated_revenue),
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
      {
        name: 'Ingresos nuevos',
        type: 'bar',
        stack: 'revenue',
        yAxisIndex: 0,
        barMaxWidth: 52,
        color: '#16a34a',
        itemStyle: {
          borderRadius: [6, 6, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#4ade80' },
            { offset: 1, color: '#16a34a' },
          ]),
        },
        data: data.monthly.map((m) => m.revenue_gained || (m.new_clients * data.avg_revenue_per_client)),
      },
      {
        name: 'Ingresos perdidos',
        type: 'bar',
        stack: 'revenue',
        yAxisIndex: 0,
        barMaxWidth: 52,
        color: '#ef4444',
        itemStyle: {
          borderRadius: [0, 0, 6, 6],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#f87171' },
            { offset: 1, color: '#dc2626' },
          ]),
        },
        data: data.monthly.map((m) => -(m.revenue_lost || (m.lost_clients * data.avg_revenue_per_client))),
      },
    ],
  };

  return (
    <div className="space-y-6">
      {/* ── Alerta de capacidad ── */}
      {showCapacityWarning && (
        <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-xl px-4 py-3">
          <span className="text-red-500 text-lg leading-none mt-0.5">⚠</span>
          <div>
            <p className="text-sm font-semibold text-red-700">
              Capacidad instalada al {utilizationPct}%
            </p>
            <p className="text-xs text-red-500 mt-0.5">
              La empresa utiliza {currentKgDay} kg/día de una capacidad instalada de {maxKgDay} kg/día.
              Se recomienda no superar el 90% para absorber imprevistos en producción.
            </p>
          </div>
        </div>
      )}

      {/* ── Header ── */}
      <div className="flex items-center justify-between">
        <h3 className="text-base font-semibold text-gray-800">Evolución Comercial</h3>
        <button
          onClick={() => {
            setGoalsForm(kpiSettings ?? { ...(data.thresholds as unknown as KpiSettings), max_clients: 72 });
            setEditingGoals((v) => !v);
          }}
          className="text-xs text-primary-600 hover:underline"
        >
          {editingGoals ? 'Cerrar' : 'Editar metas'}
        </button>
      </div>

      {/* ── Formulario de metas ── */}
      {editingGoals && goalsForm && (
        <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
          <p className="text-xs font-medium text-gray-600 mb-3">Umbrales del semáforo</p>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            {[
              { key: 'new_clients_green',  label: 'Captación/mes (verde)',    unit: '' },
              { key: 'new_clients_yellow', label: 'Captación/mes (amarillo)', unit: '' },
              { key: 'revenue_green',      label: 'Ventas (verde)',            unit: 'Bs' },
              { key: 'revenue_yellow',     label: 'Ventas (amarillo)',         unit: 'Bs' },
              { key: 'max_kg_day',          label: 'Capacidad máxima',          unit: 'kg/día' },
            ].map(({ key, label, unit }) => (
              <div key={key}>
                <label className="block text-xs text-gray-500 mb-1">{label}</label>
                <div className="flex items-center gap-1">
                  <input
                    type="number"
                    min="0"
                    value={(goalsForm as any)[key]}
                    onChange={(e) =>
                      setGoalsForm((prev) => prev ? { ...prev, [key]: Number(e.target.value) } : prev)
                    }
                    className="w-full px-2 py-1.5 border border-gray-300 rounded-lg text-xs focus:ring-2 focus:ring-primary-500 outline-none"
                  />
                  {unit && <span className="text-xs text-gray-400">{unit}</span>}
                </div>
              </div>
            ))}
          </div>
          <div className="flex justify-end gap-2 mt-3">
            <button
              onClick={() => setEditingGoals(false)}
              className="px-3 py-1.5 border border-gray-300 text-gray-600 rounded-lg text-xs hover:bg-gray-100"
            >
              Cancelar
            </button>
            <button
              onClick={() => settingsMutation.mutate(goalsForm)}
              disabled={settingsMutation.isPending}
              className="px-3 py-1.5 bg-primary-500 text-white rounded-lg text-xs hover:bg-primary-600 disabled:opacity-50"
            >
              {settingsMutation.isPending ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </div>
      )}

      {/* ── Tarjetas resumen ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <SummaryCard
          label="Clientes activos"
          value={lastPoint.cumulative_clients.toString()}
          sub="acumulado total"
          traffic={lastPoint.traffic_clients}
        />
        {data.actual_total_revenue != null ? (
          <SummaryCard
            label="Ventas mensuales"
            value={formatRevenue(data.actual_total_revenue)}
            sub="suma de ventas de clientes activos"
            traffic={
              data.actual_total_revenue >= data.thresholds.revenue_green ? 'green'
              : data.actual_total_revenue >= data.thresholds.revenue_yellow ? 'yellow'
              : 'red'
            }
          />
        ) : (
          <SummaryCard
            label="Ventas mensuales"
            value={formatRevenue(lastPoint.estimated_revenue)}
            sub="basado en clientes activos"
            traffic={lastPoint.traffic_revenue}
          />
        )}
        {/* Tarjeta 4: Capacidad instalada */}
        <div className={`bg-white rounded-xl p-4 shadow-sm border ${
          utilizationTraffic === 'red' ? 'border-red-200'
          : utilizationTraffic === 'yellow' ? 'border-yellow-200'
          : 'border-green-200'
        }`}>
          <div className="flex items-center justify-between mb-1">
            <p className="text-xs text-gray-500">Capacidad instalada</p>
            <TrafficDot status={utilizationTraffic} />
          </div>
          <p className="text-2xl font-bold text-gray-800 tabular-nums">{utilizationPct}%</p>
          <p className="text-xs text-gray-400 mt-0.5">
            {currentKgDay} / {maxKgDay} kg/día
          </p>
          <div className="mt-3 h-2 rounded-full bg-gray-100 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${
                utilizationTraffic === 'red' ? 'bg-red-400'
                : utilizationTraffic === 'yellow' ? 'bg-yellow-400'
                : 'bg-green-400'
              }`}
              style={{ width: `${utilizationPct}%` }}
            />
          </div>
        </div>

        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <p className="text-xs text-gray-500 mb-1">Venta promedio por cliente</p>
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
        <div className="flex items-center justify-between mb-3">
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
        <ReactECharts
          ref={chartRef}
          option={clientsOption}
          style={{ height: 280 }}
        />
      </div>

      {/* ── Gráfico 2: Ingreso estimado ── */}
      <div className="bg-white rounded-xl p-5 shadow-sm">
        <div className="flex items-start justify-between mb-2">
          <h4 className="text-sm font-medium text-gray-700">Ventas por mes</h4>
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

      {/* ── Selector de mes + tabla de clientes ── */}
      <div className="bg-white rounded-xl p-5 shadow-sm">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-4">
          <h4 className="text-sm font-medium text-gray-700">
            Clientes captados
            {selectedLabel && (
              <span className="ml-2 text-primary-600 font-semibold">{selectedLabel}</span>
            )}
          </h4>
          <div className="flex items-center gap-2">
            <label className="text-xs text-gray-500 whitespace-nowrap">Ver mes:</label>
            <select
              value={selectedMonth ?? ''}
              onChange={(e) => setSelectedMonth(e.target.value || null)}
              className="border border-gray-300 rounded-lg px-2 py-1.5 text-xs focus:ring-2 focus:ring-primary-500 outline-none"
            >
              <option value="">— Seleccionar mes —</option>
              {data.monthly.map((m) => (
                <option key={m.month} value={m.month}>
                  {m.label} ({m.new_clients} nuevos)
                </option>
              ))}
            </select>
            {selectedMonth && (
              <button
                onClick={() => setSelectedMonth(null)}
                className="text-xs text-gray-400 hover:text-gray-600 px-1"
                title="Limpiar selección"
              >
                ✕
              </button>
            )}
          </div>
        </div>

        {!selectedMonth && (
          <p className="text-sm text-gray-400 text-center py-6">
            Selecciona un mes del desplegable o haz clic en una barra del gráfico.
          </p>
        )}

        {selectedMonth && loadingClients && (
          <p className="text-sm text-gray-400 text-center py-6">Cargando...</p>
        )}

        {selectedMonth && !loadingClients && monthClients && (
          monthClients.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-6">
              No se registraron nuevos clientes en {selectedLabel}.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 text-xs text-gray-400">
                    <th className="text-left pb-2 font-normal">Nombre</th>
                    <th className="text-left pb-2 font-normal">Zona</th>
                    <th className="text-left pb-2 font-normal">Tipo cocina</th>
                    <th className="text-right pb-2 font-normal">Ingreso mensual</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {monthClients.map((c) => (
                    <tr
                      key={c.id}
                      onClick={() => navigate(`/restaurants/${c.id}`)}
                      className="hover:bg-gray-50 cursor-pointer transition-colors"
                    >
                      <td className="py-2.5 font-medium text-gray-800">{c.nombre}</td>
                      <td className="py-2.5 text-gray-500">{c.zona ?? '—'}</td>
                      <td className="py-2.5 text-gray-500">{c.tipo_cocina ?? '—'}</td>
                      <td className="py-2.5 text-right tabular-nums font-medium text-gray-700">
                        {c.monthly_revenue != null
                          ? formatRevenue(c.monthly_revenue)
                          : <span className="text-gray-300 font-normal">Sin dato</span>
                        }
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="border-t border-gray-200 text-xs text-gray-500">
                    <td colSpan={3} className="pt-2">
                      Total: {monthClients.length} cliente{monthClients.length !== 1 ? 's' : ''}
                    </td>
                    <td className="pt-2 text-right tabular-nums font-semibold text-gray-700">
                      {formatRevenue(
                        monthClients.reduce((sum, c) => sum + (c.monthly_revenue ?? 0), 0)
                      )}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          )
        )}
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
}

function SummaryCard({ label, value, sub, traffic }: SummaryCardProps) {
  const borderColor = { green: 'border-green-200', yellow: 'border-yellow-200', red: 'border-red-200' }[traffic];
  return (
    <div className={`bg-white rounded-xl p-4 shadow-sm border ${borderColor}`}>
      <div className="flex items-center justify-between mb-1">
        <p className="text-xs text-gray-500">{label}</p>
        <TrafficDot status={traffic} />
      </div>
      <p className="text-2xl font-bold text-gray-800 tabular-nums">{value}</p>
      <p className="text-xs text-gray-400 mt-0.5">{sub}</p>
    </div>
  );
}
