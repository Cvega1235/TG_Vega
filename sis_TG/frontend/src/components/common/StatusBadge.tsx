import { STATUS_LABELS, STATUS_COLORS } from '../../utils/constants';

interface Props {
  status: string;
}

export default function StatusBadge({ status }: Props) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
        STATUS_COLORS[status] || 'bg-gray-100 text-gray-800'
      }`}
    >
      {STATUS_LABELS[status] || status}
    </span>
  );
}
