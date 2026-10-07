/**
 * Summary card for one dispute (status, priority, amounts, link to detail).
 */
const statusColors = {
  open: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  in_review: 'bg-blue-100 text-blue-800 border-blue-200',
  resolved: 'bg-green-100 text-green-800 border-green-200',
  escalated: 'bg-red-100 text-red-800 border-red-200',
};

const priorityColors = {
  low: 'bg-gray-100 text-gray-600',
  medium: 'bg-yellow-100 text-yellow-700',
  high: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700',
};

export default function DisputeCard({ dispute, onClick }) {
  const statusClass = statusColors[dispute.status] || statusColors.open;
  const priorityClass = priorityColors[dispute.priority] || priorityColors.medium;

  return (
    <div
      onClick={onClick}
      className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow cursor-pointer"
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <span className="text-xs font-mono text-gray-500">{dispute.ticket_id}</span>
          <h3 className="text-sm font-semibold text-gray-900 mt-0.5 capitalize">{dispute.category} Dispute</h3>
        </div>
        <div className="flex gap-2">
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${statusClass}`}>
            {dispute.status.replace('_', ' ')}
          </span>
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${priorityClass}`}>
            {dispute.priority}
          </span>
        </div>
      </div>
      <p className="text-sm text-gray-600 line-clamp-2 mb-3">{dispute.description}</p>
      <div className="flex items-center justify-between text-xs text-gray-400">
        <span>Created: {dispute.created_at ? new Date(dispute.created_at).toLocaleDateString() : 'N/A'}</span>
        {dispute.discrepancy_amount && (
          <span className="font-medium text-red-600">
            Discrepancy: ₹{Math.abs(dispute.discrepancy_amount).toLocaleString('en-IN')}
          </span>
        )}
      </div>
      {dispute.employee_name && (
        <div className="mt-2 pt-2 border-t border-gray-100">
          <span className="text-xs text-gray-500">Employee: {dispute.employee_name}</span>
        </div>
      )}
    </div>
  );
}
