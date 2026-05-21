import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { getRecommendations } from '../api/ml';
import type { RecommendationProspect, ZonaOportunidad, SegmentoAfin } from '../api/ml';
import { getTopProspects } from '../api/dashboard';
import type { TopProspect } from '../types/dashboard';

// ── ProspectCard (top 3 con detalle) ────────────────────────────────────────

const RANK_MEDALS = ['🥇', '🥈', '🥉'];
const RANK_BORDERS = [
  'border-yellow-300 bg-gradient-to-br from-yellow-50 to-white',
  'border-gray-300 bg-gradient-to-br from-gray-50 to-white',
  'border-amber-700/30 bg-gradient-to-br from-amber-50 to-white',
];
const RANK_SCORE_COLORS = ['text-yellow-600', 'text-gray-500', 'text-amber-700'];

const PROSPECT_STATUS_LABELS: Record<string, string> = {
  nuevo: 'Nuevo', contactado: 'Contactado', interesado: 'Interesado',
  cliente: 'Cliente', no_interesado: 'No interesado',
};
const PROSPECT_STATUS_COLORS: Record<string, string> = {
  nuevo: 'bg-blue-100 text-blue-700',
  contactado: 'bg-yellow-100 text-yellow-700',
  interesado: 'bg-orange-100 text-orange-700',
};

function getScoreColor(score: number | null): string {
  if (score === null || score === undefined) return '#9ca3af';
  if (score >= 70) return '#22c55e';
  if (score >= 50) return '#eab308';
  return '#ef4444';
}

function getReasons(p: TopProspect): string[] {
  const reasons: string[] = [];
  if ((p.cuisine_score ?? 0) >= 20) reasons.push('Alta afinidad de productos con el catálogo Don Piotr');
  if ((p.rating_score ?? 0) >= 15) reasons.push('Rating excepcional entre los restaurantes del mercado');
  if ((p.reviews_score ?? 0) >= 10) reasons.push('Alto volumen de reseñas indica establecimiento consolidado');
  if ((p.zone_score ?? 0) >= 10) reasons.push('Ubicado en zona de alto potencial comercial');
  if (p.tiene_embutidos) reasons.push('Menú con productos afines a embutidos detectado');
  if (reasons.length === 0) reasons.push('Score compuesto elevado según análisis ML del sistema');
  return reasons.slice(0, 3);
}

function ProspectCard({ prospect, rank }: { prospect: TopProspect; rank: number }) {
  const navigate = useNavigate();
  const reasons = getReasons(prospect);
  const scorePct = Math.min(prospect.total_score, 100);

  return (
    <div className={`rounded-2xl border-2 p-5 shadow-sm flex flex-col gap-4 h-full ${RANK_BORDERS[rank]}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{RANK_MEDALS[rank]}</span>
          <div>
            <p className="font-bold text-gray-800 text-base leading-tight">{prospect.nombre}</p>
            <p className="text-xs text-gray-500 mt-0.5">
              {prospect.zona ?? 'Sin zona'}{prospect.tipo_cocina ? ` · ${prospect.tipo_cocina}` : ''}
            </p>
          </div>
        </div>
        <div className="flex flex-col items-end gap-1.5 shrink-0">
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${PROSPECT_STATUS_COLORS[prospect.status] ?? 'bg-gray-100 text-gray-600'}`}>
            {PROSPECT_STATUS_LABELS[prospect.status] ?? prospect.status}
          </span>
          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
            prospect.score_source === 'ml'
              ? 'bg-blue-50 text-blue-600 border-blue-200'
              : 'bg-gray-50 text-gray-400 border-gray-200'
          }`}>
            {prospect.score_source === 'ml' ? 'Score ML' : 'Score ICP'}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative flex items-center justify-center w-20 h-20 flex-shrink-0">
          <svg className="w-20 h-20 -rotate-90" viewBox="0 0 80 80">
            <circle cx="40" cy="40" r="34" fill="none" stroke="#f3f4f6" strokeWidth="8" />
            <circle
              cx="40" cy="40" r="34" fill="none"
              stroke={getScoreColor(prospect.total_score)}
              strokeWidth="8"
              strokeDasharray={`${(scorePct / 100) * 213.6} 213.6`}
              strokeLinecap="round"
            />
          </svg>
          <div className="absolute text-center">
            <p className={`text-lg font-bold leading-none ${RANK_SCORE_COLORS[rank]}`}>
              {prospect.total_score.toFixed(0)}
            </p>
            <p className="text-[10px] text-gray-400">/100</p>
          </div>
        </div>
        <div className="space-y-1 text-sm">
          {prospect.rating && (
            <p className="flex items-center gap-1 text-gray-600">
              <span className="text-yellow-500">★</span>
              <span className="font-medium">{prospect.rating.toFixed(1)}</span>
              <span className="text-gray-400">/ 5</span>
            </p>
          )}
          {prospect.telefono && <p className="text-gray-500 text-xs">📞 Teléfono disponible</p>}
          {prospect.tiene_embutidos && <p className="text-green-600 text-xs font-medium">✓ Usa embutidos</p>}
        </div>
      </div>

      <div className="flex-1 bg-white/70 rounded-xl p-3 space-y-1.5 border border-gray-100">
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
          Por qué el sistema lo recomienda
        </p>
        {reasons.map((r, i) => (
          <p key={i} className="text-xs text-gray-600 flex items-start gap-1.5">
            <span className="text-green-500 mt-0.5 flex-shrink-0">✓</span>
            {r}
          </p>
        ))}
      </div>

      <button
        onClick={() => navigate(`/restaurants/${prospect.id}`)}
        className="w-full py-2 rounded-xl text-sm font-semibold text-white transition-all"
        style={{ background: 'linear-gradient(90deg,#7F1D1D,#9B1C2E)' }}
      >
        Ver prospecto →
      </button>
    </div>
  );
}

const STATUS_LABEL: Record<string, string> = {
  nuevo: 'Nuevo',
  contactado: 'Contactado',
  interesado: 'Interesado',
  cliente: 'Cliente',
  no_interesado: 'No interesado',
};

const STATUS_COLOR: Record<string, string> = {
  nuevo: 'bg-gray-100 text-gray-700',
  contactado: 'bg-blue-100 text-blue-700',
  interesado: 'bg-yellow-100 text-yellow-700',
};

function ScoreBadge({ score }: { score: number }) {
  const pct = Math.round(score);
  const color = pct >= 75 ? 'bg-green-100 text-green-800' : pct >= 50 ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100 text-gray-600';
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${color}`}>
      {pct}
    </span>
  );
}

function ProspectRow({ p, onClick }: { p: RecommendationProspect; onClick: () => void }) {
  return (
    <tr onClick={onClick} className="hover:bg-gray-50 cursor-pointer transition-colors">
      <td className="px-4 py-3">
        <span className="font-medium text-gray-900 block">{p.nombre}</span>
        {p.tipo_cocina && <span className="text-xs text-gray-400">{p.tipo_cocina}</span>}
      </td>
      <td className="px-4 py-3 text-sm text-gray-500">{p.zona ?? '—'}</td>
      <td className="px-4 py-3">
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${STATUS_COLOR[p.status] ?? 'bg-gray-100 text-gray-600'}`}>
          {STATUS_LABEL[p.status] ?? p.status}
        </span>
      </td>
      <td className="px-4 py-3 text-center">
        <ScoreBadge score={p.composite_score} />
      </td>
    </tr>
  );
}

function ProspectTable({ title, icon, subtitle, rows, emptyMsg }: {
  title: string;
  icon: string;
  subtitle: string;
  rows: RecommendationProspect[];
  emptyMsg: string;
}) {
  const navigate = useNavigate();
  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden flex flex-col">
      <div className="px-5 py-4 border-b border-gray-100">
        <h3 className="font-semibold text-gray-900 flex items-center gap-2">
          <span>{icon}</span> {title}
        </h3>
        <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>
      </div>
      {rows.length === 0 ? (
        <div className="flex-1 flex items-center justify-center py-10 text-sm text-gray-400">{emptyMsg}</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-xs text-gray-500">
              <tr>
                <th className="text-left px-4 py-2 font-medium">Nombre</th>
                <th className="text-left px-4 py-2 font-medium">Zona</th>
                <th className="text-left px-4 py-2 font-medium">Estado</th>
                <th className="text-center px-4 py-2 font-medium">Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {rows.map((p) => (
                <ProspectRow key={p.id} p={p} onClick={() => navigate(`/restaurants/${p.id}`)} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function ZonasCard({ zonas }: { zonas: ZonaOportunidad[] }) {
  const max = zonas[0]?.total_prospectos ?? 1;
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h3 className="font-semibold text-gray-900 flex items-center gap-2 mb-1">
        <span>📍</span> Zonas con más oportunidad
      </h3>
      <p className="text-xs text-gray-500 mb-4">
        Zonas con mayor cantidad de prospectos de calidad (score ≥ 60) sin trabajar
      </p>
      {zonas.length === 0 ? (
        <p className="text-sm text-gray-400 text-center py-6">Sin datos — ejecuta el pipeline ML primero</p>
      ) : (
        <div className="space-y-3">
          {zonas.map((z) => (
            <div key={z.zona}>
              <div className="flex justify-between text-sm mb-1">
                <span className="font-medium text-gray-800">{z.zona}</span>
                <span className="text-gray-500">
                  {z.total_prospectos} prospectos · score prom. {Math.round(z.avg_score)}
                </span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2">
                <div
                  className="bg-primary-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${Math.round((z.total_prospectos / max) * 100)}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function SegmentosCard({ segmentos }: { segmentos: SegmentoAfin[] }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h3 className="font-semibold text-gray-900 flex items-center gap-2 mb-1">
        <span>🍽️</span> Segmentos más afines
      </h3>
      <p className="text-xs text-gray-500 mb-4">
        Tipos de cocina con mayor tasa de conversión histórica a cliente
      </p>
      {segmentos.length === 0 ? (
        <p className="text-sm text-gray-400 text-center py-6">Sin datos suficientes</p>
      ) : (
        <div className="space-y-3">
          {segmentos.map((s) => (
            <div key={s.tipo_cocina} className="flex items-center justify-between gap-4">
              <div className="min-w-0 flex-1">
                <span className="text-sm font-medium text-gray-800 truncate block">{s.tipo_cocina}</span>
                <span className="text-xs text-gray-400">{s.clientes} de {s.total} restaurantes</span>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <div className="w-24 bg-gray-100 rounded-full h-2">
                  <div
                    className="bg-green-500 h-2 rounded-full"
                    style={{ width: `${Math.round(s.conversion_rate * 100)}%` }}
                  />
                </div>
                <span className="text-sm font-semibold text-green-700 w-10 text-right">
                  {Math.round(s.conversion_rate * 100)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function RecommendationsPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['recommendations'],
    queryFn: getRecommendations,
  });

  const { data: topProspects } = useQuery({
    queryKey: ['topProspects'],
    queryFn: () => getTopProspects(3),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400 text-sm">
        Cargando recomendaciones...
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3 text-center">
        <p className="text-gray-500 text-sm">
          No hay recomendaciones disponibles.
        </p>
        <p className="text-xs text-gray-400">
          Ejecuta el pipeline ML desde la sección Análisis ML para generar scores.
        </p>
      </div>
    );
  }

  const totalAcciones = data.acciones_rapidas.length;
  const totalSinContactar = data.top_sin_contactar.length;

  return (
    <div className="space-y-6">
      {/* Encabezado */}
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Recomendaciones</h1>
        <p className="text-sm text-gray-500 mt-1">
          Acciones estratégicas basadas en el análisis ML de afinidad con Don Piotr
        </p>
      </div>

      {/* Top 3 prospectos */}
      {topProspects && topProspects.length > 0 && (
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h2 className="text-lg font-bold text-gray-800">Top 3 Prospectos</h2>
            <span className="text-xs bg-primary-100 text-primary-700 font-semibold px-2 py-0.5 rounded-full">
              Análisis ML
            </span>
          </div>
          <p className="text-sm text-gray-500 mb-4">
            Los restaurantes con mayor potencial de conversión según el modelo, excluyendo clientes actuales.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5 items-stretch">
            {topProspects.map((p, i) => (
              <ProspectCard key={p.id} prospect={p} rank={i} />
            ))}
          </div>
        </div>
      )}

      {/* Resumen rápido */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <SummaryChip
          label="Acciones rápidas"
          value={totalAcciones}
          color="yellow"
          hint="Prospectos contactados con score alto"
        />
        <SummaryChip
          label="Sin contactar"
          value={totalSinContactar}
          color="blue"
          hint="Mejores prospectos nuevos"
        />
        <SummaryChip
          label="Zonas priorizadas"
          value={data.zonas_oportunidad.length}
          color="primary"
          hint="Zonas con alta densidad de prospectos"
        />
        <SummaryChip
          label="Segmentos afines"
          value={data.segmentos_afines.length}
          color="green"
          hint="Tipos de cocina con mayor conversión"
        />
      </div>

      {/* Dos listas de prospectos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ProspectTable
          title="Acciones rápidas"
          icon="⚡"
          subtitle="Ya en contacto — un empujón puede cerrar la venta"
          rows={data.acciones_rapidas}
          emptyMsg="No hay prospectos contactados con score suficiente"
        />
        <ProspectTable
          title="Top prospectos sin contactar"
          icon="🎯"
          subtitle="Mayor afinidad con Don Piotr aún sin trabajar"
          rows={data.top_sin_contactar}
          emptyMsg="Sin prospectos nuevos con score ML disponible"
        />
      </div>

      {/* Zonas y segmentos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ZonasCard zonas={data.zonas_oportunidad} />
        <SegmentosCard segmentos={data.segmentos_afines} />
      </div>
    </div>
  );
}

function SummaryChip({ label, value, color, hint }: {
  label: string;
  value: number;
  color: 'yellow' | 'blue' | 'primary' | 'green';
  hint: string;
}) {
  const colors = {
    yellow: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    blue: 'bg-blue-50 border-blue-200 text-blue-800',
    primary: 'bg-red-50 border-red-200 text-red-800',
    green: 'bg-green-50 border-green-200 text-green-800',
  };
  return (
    <div className={`rounded-xl border p-4 ${colors[color]}`} title={hint}>
      <p className="text-2xl font-bold">{value}</p>
      <p className="text-xs font-medium mt-0.5 opacity-80">{label}</p>
    </div>
  );
}
