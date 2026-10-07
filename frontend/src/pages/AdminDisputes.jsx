/**
 * Admin workflow for AI-reviewed disputes: approve/reject, re-run review, view markdown analysis.
 */
import { useState, useEffect } from 'react';
import { Bot, CheckCircle, XCircle, AlertTriangle, RotateCw, Eye, ChevronDown, ShieldCheck, Clock, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import api from '../api/axios';
import StatCard from '../components/StatCard';
import LoadingSpinner from '../components/LoadingSpinner';
import toast from 'react-hot-toast';

const statusColors = {
  open: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  in_review: 'bg-blue-100 text-blue-800 border-blue-200',
  resolved: 'bg-green-100 text-green-800 border-green-200',
  escalated: 'bg-red-100 text-red-800 border-red-200',
  awaiting_approval: 'bg-purple-100 text-purple-800 border-purple-200',
};

const verdictColors = {
  resolved_valid: 'bg-red-50 text-red-700 border-red-200',
  resolved_invalid: 'bg-green-50 text-green-700 border-green-200',
  escalated: 'bg-amber-50 text-amber-700 border-amber-200',
};

const verdictLabels = {
  resolved_valid: 'Discrepancy Found',
  resolved_invalid: 'No Discrepancy',
  escalated: 'Needs Review',
};

const priorityColors = {
  low: 'bg-gray-100 text-gray-600',
  medium: 'bg-yellow-100 text-yellow-700',
  high: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700',
};

export default function AdminDisputes() {
  const [disputes, setDisputes] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedDispute, setSelectedDispute] = useState(null);
  const [filter, setFilter] = useState('all');
  const [reviewingId, setReviewingId] = useState(null);
  const [reviewingAll, setReviewingAll] = useState(false);
  const [adminAction, setAdminAction] = useState('');
  const [adminNotes, setAdminNotes] = useState('');
  const [submittingReview, setSubmittingReview] = useState(false);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [dispRes, statsRes] = await Promise.all([
        api.get('/disputes/admin/all'),
        api.get('/disputes/admin/stats'),
      ]);
      setDisputes(dispRes.data.disputes || []);
      setStats(statsRes.data);
    } catch (err) {
      toast.error('Failed to load disputes');
    } finally {
      setLoading(false);
    }
  };

  const triggerAIReview = async (ticketId) => {
    setReviewingId(ticketId);
    try {
      const res = await api.post(`/disputes/ai-review/${ticketId}`);
      toast.success(`AI Review: ${res.data.verdict}`);
      await loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'AI review failed');
    } finally {
      setReviewingId(null);
    }
  };

  const triggerReviewAll = async () => {
    setReviewingAll(true);
    try {
      const res = await api.post('/disputes/ai-review-all');
      toast.success(`Reviewed ${res.data.reviewed} disputes`);
      await loadData();
    } catch (err) {
      toast.error('Batch review failed');
    } finally {
      setReviewingAll(false);
    }
  };

  const submitAdminReview = async (ticketId) => {
    if (!adminAction) { toast.error('Select an action'); return; }
    setSubmittingReview(true);
    try {
      await api.post(`/disputes/admin-review/${ticketId}`, {
        action: adminAction,
        admin_notes: adminNotes,
      });
      toast.success('Admin review submitted');
      setSelectedDispute(null);
      setAdminAction('');
      setAdminNotes('');
      await loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Review failed');
    } finally {
      setSubmittingReview(false);
    }
  };

  const filtered = filter === 'all'
    ? disputes
    : filter === 'pending_admin'
      ? disputes.filter(d => d.ai_reviewed && !d.admin_reviewed)
      : filter === 'ai_pending'
        ? disputes.filter(d => !d.ai_reviewed)
        : disputes.filter(d => d.status === filter);

  if (loading) return <div className="flex items-center justify-center h-full"><LoadingSpinner text="Loading disputes..." /></div>;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 overflow-y-auto h-full">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Dispute Management</h2>
          <p className="text-sm text-gray-500">AI-powered review & admin oversight</p>
        </div>
        <button
          onClick={triggerReviewAll}
          disabled={reviewingAll}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary-800 text-white text-sm font-medium
                     hover:bg-primary-900 transition disabled:opacity-50"
        >
          {reviewingAll ? <Loader2 size={16} className="animate-spin" /> : <Bot size={16} />}
          {reviewingAll ? 'Reviewing...' : 'AI Review All Open'}
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatCard title="Total Disputes" value={stats.total} icon={AlertTriangle} color="blue" />
          <StatCard title="Pending AI Review" value={stats.open} icon={Clock} color="amber" />
          <StatCard title="Pending Admin" value={stats.pending_admin_review} icon={ShieldCheck} color="red" />
          <StatCard title="Admin Reviewed" value={stats.admin_reviewed} icon={CheckCircle} color="green" />
        </div>
      )}

      {/* AI Verdict Summary */}
      {stats && (
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-green-50 border border-green-200 rounded-xl p-4 text-center">
            <p className="text-2xl font-bold text-green-700">{stats.ai_resolved_invalid}</p>
            <p className="text-xs text-green-600 mt-1">AI: No Discrepancy</p>
          </div>
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-center">
            <p className="text-2xl font-bold text-red-700">{stats.ai_resolved_valid}</p>
            <p className="text-xs text-red-600 mt-1">AI: Discrepancy Found</p>
          </div>
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-center">
            <p className="text-2xl font-bold text-amber-700">{stats.ai_escalated}</p>
            <p className="text-xs text-amber-600 mt-1">AI: Escalated</p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-2 flex-wrap">
        {[
          { key: 'all', label: 'All', count: disputes.length },
          { key: 'ai_pending', label: 'Needs AI Review', count: disputes.filter(d => !d.ai_reviewed).length },
          { key: 'pending_admin', label: 'Needs Admin Review', count: disputes.filter(d => d.ai_reviewed && !d.admin_reviewed).length },
          { key: 'resolved', label: 'Resolved', count: disputes.filter(d => d.status === 'resolved').length },
          { key: 'escalated', label: 'Escalated', count: disputes.filter(d => d.status === 'escalated').length },
          { key: 'awaiting_approval', label: 'Awaiting Approval', count: disputes.filter(d => d.status === 'awaiting_approval').length },
        ].map(f => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
              filter === f.key ? 'bg-primary-800 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {f.label} ({f.count})
          </button>
        ))}
      </div>

      {/* Dispute Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                <th className="px-4 py-3">Ticket</th>
                <th className="px-4 py-3">Employee</th>
                <th className="px-4 py-3">Category</th>
                <th className="px-4 py-3">Amount</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">AI Verdict</th>
                <th className="px-4 py-3">Admin</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.map(d => (
                <tr key={d.ticket_id} className="hover:bg-gray-50 transition">
                  <td className="px-4 py-3 font-mono text-xs text-gray-900">{d.ticket_id}</td>
                  <td className="px-4 py-3 text-gray-700">{d.employee_name || `Emp #${d.employee_id}`}</td>
                  <td className="px-4 py-3 capitalize text-gray-600">{d.category}</td>
                  <td className="px-4 py-3">
                    {d.discrepancy_amount ? (
                      <span className="text-red-600 font-medium">₹{Math.abs(d.discrepancy_amount).toLocaleString('en-IN')}</span>
                    ) : '-'}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${statusColors[d.status] || 'bg-gray-100 text-gray-600'}`}>
                      {d.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {d.ai_reviewed ? (
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${verdictColors[d.ai_verdict] || 'bg-gray-100 text-gray-600'}`}>
                        {verdictLabels[d.ai_verdict] || d.ai_verdict}
                      </span>
                    ) : (
                      <span className="text-xs text-gray-400">Pending</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {d.admin_reviewed ? (
                      <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200 capitalize">
                        {d.admin_action}
                      </span>
                    ) : (
                      <span className="text-xs text-gray-400">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1.5">
                      <button
                        onClick={() => { setSelectedDispute(d); setAdminAction(''); setAdminNotes(''); }}
                        className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-500"
                        title="View details"
                      >
                        <Eye size={14} />
                      </button>
                      {!d.ai_reviewed && (
                        <button
                          onClick={() => triggerAIReview(d.ticket_id)}
                          disabled={reviewingId === d.ticket_id}
                          className="p-1.5 rounded-lg hover:bg-blue-50 text-blue-600 disabled:opacity-50"
                          title="AI Review"
                        >
                          {reviewingId === d.ticket_id ? <Loader2 size={14} className="animate-spin" /> : <Bot size={14} />}
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filtered.length === 0 && (
            <div className="text-center py-12 text-sm text-gray-400">No disputes found</div>
          )}
        </div>
      </div>

      {/* Detail / Admin Review Modal */}
      {selectedDispute && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4" onClick={() => setSelectedDispute(null)}>
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            {/* Header */}
            <div className="sticky top-0 bg-white border-b border-gray-100 px-6 py-4 flex items-center justify-between">
              <div>
                <span className="text-xs font-mono text-gray-500">{selectedDispute.ticket_id}</span>
                <h3 className="text-lg font-bold text-gray-900 capitalize">{selectedDispute.category} Dispute</h3>
              </div>
              <button onClick={() => setSelectedDispute(null)} className="text-gray-400 hover:text-gray-600 text-2xl leading-none">&times;</button>
            </div>

            <div className="px-6 py-4 space-y-5">
              {/* Employee & Dispute Info */}
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-gray-50 rounded-lg p-3">
                  <label className="text-xs text-gray-500">Employee</label>
                  <p className="font-medium text-gray-900">{selectedDispute.employee_name || `#${selectedDispute.employee_id}`}</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <label className="text-xs text-gray-500">Priority</label>
                  <p className="font-medium capitalize">{selectedDispute.priority}</p>
                </div>
              </div>

              <div>
                <label className="text-xs font-medium text-gray-500">Description</label>
                <p className="text-sm text-gray-800 mt-1 bg-gray-50 p-3 rounded-lg">{selectedDispute.description}</p>
              </div>

              {selectedDispute.expected_amount && (
                <div className="grid grid-cols-3 gap-3">
                  <div className="bg-green-50 rounded-lg p-3 text-center">
                    <label className="text-xs text-green-600">Expected</label>
                    <p className="font-bold text-green-800">₹{selectedDispute.expected_amount?.toLocaleString('en-IN')}</p>
                  </div>
                  <div className="bg-red-50 rounded-lg p-3 text-center">
                    <label className="text-xs text-red-600">Actual</label>
                    <p className="font-bold text-red-800">₹{selectedDispute.actual_amount?.toLocaleString('en-IN')}</p>
                  </div>
                  <div className="bg-amber-50 rounded-lg p-3 text-center">
                    <label className="text-xs text-amber-600">Gap</label>
                    <p className="font-bold text-amber-800">₹{Math.abs(selectedDispute.discrepancy_amount || 0).toLocaleString('en-IN')}</p>
                  </div>
                </div>
              )}

              {/* AI Analysis Section */}
              {selectedDispute.ai_reviewed && (
                <div className="border border-blue-200 rounded-xl overflow-hidden">
                  <div className="bg-blue-50 px-4 py-2.5 flex items-center gap-2">
                    <Bot size={16} className="text-blue-600" />
                    <span className="text-sm font-semibold text-blue-800">AI Agent Analysis</span>
                    <span className={`ml-auto px-2 py-0.5 rounded-full text-xs font-medium border ${verdictColors[selectedDispute.ai_verdict]}`}>
                      {verdictLabels[selectedDispute.ai_verdict] || selectedDispute.ai_verdict}
                    </span>
                  </div>
                  <div className="px-4 py-3 prose text-sm max-w-none">
                    <ReactMarkdown>{selectedDispute.ai_analysis || 'No analysis available'}</ReactMarkdown>
                  </div>
                </div>
              )}

              {/* Admin Review Section */}
              {selectedDispute.admin_reviewed ? (
                <div className="border border-purple-200 rounded-xl overflow-hidden">
                  <div className="bg-purple-50 px-4 py-2.5 flex items-center gap-2">
                    <ShieldCheck size={16} className="text-purple-600" />
                    <span className="text-sm font-semibold text-purple-800">Admin Decision</span>
                    <span className="ml-auto px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-700 capitalize">
                      {selectedDispute.admin_action}
                    </span>
                  </div>
                  {selectedDispute.admin_notes && (
                    <div className="px-4 py-3 text-sm text-gray-700">{selectedDispute.admin_notes}</div>
                  )}
                </div>
              ) : selectedDispute.ai_reviewed && (
                <div className="border border-gray-200 rounded-xl p-4 space-y-3">
                  <h4 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
                    <ShieldCheck size={16} className="text-primary-600" /> Admin Review
                  </h4>
                  <div className="flex gap-2">
                    {[
                      { value: 'approved', label: 'Approve', icon: CheckCircle, color: 'border-green-300 bg-green-50 text-green-700' },
                      { value: 'rejected', label: 'Reject', icon: XCircle, color: 'border-red-300 bg-red-50 text-red-700' },
                      { value: 'modified', label: 'Modify', icon: RotateCw, color: 'border-amber-300 bg-amber-50 text-amber-700' },
                    ].map(opt => (
                      <button
                        key={opt.value}
                        onClick={() => setAdminAction(opt.value)}
                        className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg border text-sm font-medium transition
                          ${adminAction === opt.value ? opt.color + ' ring-2 ring-offset-1' : 'border-gray-200 text-gray-500 hover:bg-gray-50'}`}
                      >
                        <opt.icon size={14} /> {opt.label}
                      </button>
                    ))}
                  </div>
                  <textarea
                    value={adminNotes}
                    onChange={e => setAdminNotes(e.target.value)}
                    placeholder="Add your notes or decision rationale..."
                    rows={3}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 outline-none"
                  />
                  <button
                    onClick={() => submitAdminReview(selectedDispute.ticket_id)}
                    disabled={!adminAction || submittingReview}
                    className="w-full py-2.5 rounded-lg bg-primary-800 text-white text-sm font-semibold hover:bg-primary-900
                               disabled:opacity-40 disabled:cursor-not-allowed transition flex items-center justify-center gap-2"
                  >
                    {submittingReview ? <Loader2 size={16} className="animate-spin" /> : <ShieldCheck size={16} />}
                    Submit Admin Decision
                  </button>
                </div>
              )}

              {/* AI Review trigger if not yet reviewed */}
              {!selectedDispute.ai_reviewed && (
                <button
                  onClick={() => triggerAIReview(selectedDispute.ticket_id)}
                  disabled={reviewingId === selectedDispute.ticket_id}
                  className="w-full py-2.5 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700
                             disabled:opacity-50 transition flex items-center justify-center gap-2"
                >
                  {reviewingId === selectedDispute.ticket_id ? <Loader2 size={16} className="animate-spin" /> : <Bot size={16} />}
                  Run AI Review
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
