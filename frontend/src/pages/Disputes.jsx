/**
 * Lists dispute tickets (employee or HR-wide); create new dispute and open detail navigation.
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search } from 'lucide-react';
import api from '../api/axios';
import { useAuth } from '../context/AuthContext';
import DisputeCard from '../components/DisputeCard';
import LoadingSpinner from '../components/LoadingSpinner';

export default function Disputes() {
  const { isHR } = useAuth();
  const navigate = useNavigate();
  const [disputes, setDisputes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [selectedDispute, setSelectedDispute] = useState(null);

  useEffect(() => {
    const endpoint = isHR ? '/disputes' : '/disputes/my';
    api.get(endpoint)
      .then(res => setDisputes(res.data.disputes || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [isHR]);

  const filtered = filter === 'all' ? disputes : disputes.filter(d => d.status === filter);

  if (loading) return <div className="flex items-center justify-center h-full"><LoadingSpinner text="Loading disputes..." /></div>;

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6 overflow-y-auto h-full">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-gray-900">{isHR ? 'All Disputes' : 'My Disputes'}</h2>
          <p className="text-sm text-gray-500">{disputes.length} total dispute{disputes.length !== 1 ? 's' : ''}</p>
        </div>
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary-800 text-white text-sm font-medium hover:bg-primary-900 transition"
        >
          <Plus size={16} /> File New Dispute
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        {['all', 'open', 'in_review', 'awaiting_approval', 'resolved', 'escalated'].map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition capitalize ${
              filter === f ? 'bg-primary-800 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {f.replace('_', ' ')} {f === 'all' ? `(${disputes.length})` : `(${disputes.filter(d => d.status === f).length})`}
          </button>
        ))}
      </div>

      {/* Dispute List */}
      {filtered.length > 0 ? (
        <div className="grid gap-4">
          {filtered.map(d => (
            <DisputeCard key={d.ticket_id} dispute={d} onClick={() => setSelectedDispute(d)} />
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <p className="text-gray-500">No disputes found</p>
        </div>
      )}

      {/* Detail Modal */}
      {selectedDispute && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4" onClick={() => setSelectedDispute(null)}>
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <div>
                <span className="text-xs font-mono text-gray-500">{selectedDispute.ticket_id}</span>
                <h3 className="text-lg font-bold text-gray-900 capitalize">{selectedDispute.category} Dispute</h3>
              </div>
              <button onClick={() => setSelectedDispute(null)} className="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
            </div>
            <div className="space-y-4 text-sm">
              <div>
                <label className="text-xs font-medium text-gray-500">Description</label>
                <p className="text-gray-800 mt-1">{selectedDispute.description}</p>
              </div>
              {selectedDispute.expected_amount && (
                <div className="grid grid-cols-3 gap-3">
                  <div className="bg-green-50 rounded-lg p-3">
                    <label className="text-xs text-green-600">Expected</label>
                    <p className="font-bold text-green-800">₹{selectedDispute.expected_amount?.toLocaleString('en-IN')}</p>
                  </div>
                  <div className="bg-red-50 rounded-lg p-3">
                    <label className="text-xs text-red-600">Actual</label>
                    <p className="font-bold text-red-800">₹{selectedDispute.actual_amount?.toLocaleString('en-IN')}</p>
                  </div>
                  <div className="bg-amber-50 rounded-lg p-3">
                    <label className="text-xs text-amber-600">Discrepancy</label>
                    <p className="font-bold text-amber-800">₹{Math.abs(selectedDispute.discrepancy_amount || 0).toLocaleString('en-IN')}</p>
                  </div>
                </div>
              )}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-gray-500">Status</label>
                  <p className="font-medium capitalize mt-1">{selectedDispute.status?.replace('_', ' ')}</p>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500">Priority</label>
                  <p className="font-medium capitalize mt-1">{selectedDispute.priority}</p>
                </div>
              </div>
              {selectedDispute.resolution_notes && (
                <div>
                  <label className="text-xs font-medium text-gray-500">Resolution Notes</label>
                  <p className="text-gray-800 mt-1 bg-gray-50 p-3 rounded-lg">{selectedDispute.resolution_notes}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
