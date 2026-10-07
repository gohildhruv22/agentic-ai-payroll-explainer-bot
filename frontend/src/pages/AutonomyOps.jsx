import { useEffect, useState } from 'react';
import { Activity, AlertTriangle, ShieldCheck, RefreshCw, CheckCircle2 } from 'lucide-react';
import api from '../api/axios';
import toast from 'react-hot-toast';

export default function AutonomyOps() {
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState(null);
  const [health, setHealth] = useState(null);
  const [approvals, setApprovals] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [events, setEvents] = useState([]);

  const load = async () => {
    setLoading(true);
    try {
      const [s, h, a, i, e] = await Promise.all([
        api.get('/autonomy/status'),
        api.get('/autonomy/phase3-health'),
        api.get('/autonomy/approvals'),
        api.get('/autonomy/sla'),
        api.get('/autonomy/events'),
      ]);
      setStatus(s.data);
      setHealth(h.data);
      setApprovals(a.data.approvals || []);
      setIncidents(i.data.incidents || []);
      setEvents(e.data.events || []);
    } catch (err) {
      toast.error('Failed to load autonomy ops data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const decideApproval = async (id, decision) => {
    try {
      await api.post(`/autonomy/approvals/${id}/decision`, { decision, notes: `Set from UI: ${decision}` });
      toast.success(`Approval ${decision}`);
      load();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Action failed');
    }
  };

  const decideIncident = async (id, decision) => {
    try {
      await api.post(`/autonomy/sla/${id}/decision`, { decision, notes: `Set from UI: ${decision}` });
      toast.success(`Incident ${decision}d`);
      load();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Action failed');
    }
  };

  if (loading) return <div className="p-6 text-sm text-gray-500">Loading autonomy ops...</div>;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 overflow-y-auto h-full">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Autonomy Operations</h2>
          <p className="text-sm text-gray-500">Phase 3 control center</p>
        </div>
        <button onClick={load} className="px-3 py-2 rounded-lg bg-primary-800 text-white text-sm flex items-center gap-2">
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white border rounded-xl p-4">
          <p className="text-xs text-gray-500">Readiness Score</p>
          <p className="text-2xl font-bold">{health?.readiness_score ?? 0}%</p>
          <p className="text-xs mt-1 capitalize text-gray-600">{health?.status}</p>
        </div>
        <div className="bg-white border rounded-xl p-4">
          <p className="text-xs text-gray-500">Engine</p>
          <p className="text-2xl font-bold">{status?.running ? 'Running' : 'Stopped'}</p>
          <p className="text-xs mt-1 text-gray-600">Poll: {status?.poll_seconds ?? '-'}s</p>
        </div>
        <div className="bg-white border rounded-xl p-4">
          <p className="text-xs text-gray-500">Pending Approvals</p>
          <p className="text-2xl font-bold">{health?.metrics?.pending_approvals ?? approvals.length}</p>
          <p className="text-xs mt-1 text-gray-600">High-risk: {health?.metrics?.pending_high_risk_approvals ?? 0}</p>
        </div>
      </div>

      <div className="bg-white border rounded-xl p-4">
        <h3 className="text-sm font-semibold mb-2">Health Checks</h3>
        <div className="space-y-2">
          {(health?.checks || []).map((c) => (
            <div key={c.id} className="flex items-center gap-2 text-sm">
              {c.ok ? <CheckCircle2 size={14} className="text-green-600" /> : <AlertTriangle size={14} className="text-red-600" />}
              <span>{c.message}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white border rounded-xl p-4">
          <h3 className="text-sm font-semibold mb-3">Pending Approvals</h3>
          <div className="space-y-2 max-h-80 overflow-y-auto">
            {approvals.length === 0 && <p className="text-sm text-gray-400">No pending approvals</p>}
            {approvals.map((a) => (
              <div key={a.id} className="border rounded-lg p-3">
                <p className="text-xs text-gray-500">{a.request_type} · {a.reference_id}</p>
                <p className="text-sm text-gray-800">{a.reason}</p>
                <p className="text-xs text-gray-500 mt-1">Risk: {Number(a.risk_score || 0).toFixed(2)}</p>
                <div className="flex gap-2 mt-2">
                  <button onClick={() => decideApproval(a.id, 'approved')} className="px-2 py-1 text-xs rounded bg-green-100 text-green-700">Approve</button>
                  <button onClick={() => decideApproval(a.id, 'rejected')} className="px-2 py-1 text-xs rounded bg-red-100 text-red-700">Reject</button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white border rounded-xl p-4">
          <h3 className="text-sm font-semibold mb-3">SLA Incidents</h3>
          <div className="space-y-2 max-h-80 overflow-y-auto">
            {incidents.length === 0 && <p className="text-sm text-gray-400">No incidents</p>}
            {incidents.map((i) => (
              <div key={i.id} className="border rounded-lg p-3">
                <p className="text-xs text-gray-500">{i.incident_type} · {i.severity}</p>
                <p className="text-sm text-gray-800">{i.summary}</p>
                <p className="text-xs text-gray-500 mt-1">Status: {i.status}</p>
                {i.status !== 'resolved' && (
                  <div className="flex gap-2 mt-2">
                    <button onClick={() => decideIncident(i.id, 'acknowledge')} className="px-2 py-1 text-xs rounded bg-blue-100 text-blue-700">Acknowledge</button>
                    <button onClick={() => decideIncident(i.id, 'resolve')} className="px-2 py-1 text-xs rounded bg-green-100 text-green-700">Resolve</button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-white border rounded-xl p-4">
        <h3 className="text-sm font-semibold mb-3">Recent Events</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left text-gray-500">
                <th className="py-1">Type</th>
                <th className="py-1">Status</th>
                <th className="py-1">Created</th>
                <th className="py-1">Processed</th>
              </tr>
            </thead>
            <tbody>
              {events.slice(0, 20).map((e) => (
                <tr key={e.id} className="border-t">
                  <td className="py-1">{e.event_type}</td>
                  <td className="py-1 capitalize">{e.status}</td>
                  <td className="py-1">{e.created_at ? new Date(e.created_at).toLocaleString() : '-'}</td>
                  <td className="py-1">{e.processed_at ? new Date(e.processed_at).toLocaleString() : '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

