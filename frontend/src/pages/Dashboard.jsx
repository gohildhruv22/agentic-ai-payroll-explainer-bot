/**
 * HR/Admin analytics: charts and KPIs from /api/dashboard/stats (queries, disputes, intents).
 */
import { useState, useEffect } from 'react';
import { MessageSquare, AlertTriangle, Users, TrendingUp } from 'lucide-react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import api from '../api/axios';
import StatCard from '../components/StatCard';
import LoadingSpinner from '../components/LoadingSpinner';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/dashboard/stats')
      .then(res => setStats(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center h-full"><LoadingSpinner text="Loading dashboard..." /></div>;
  if (!stats) return <div className="text-center py-20 text-gray-500">Unable to load dashboard data</div>;

  const disputeData = Object.entries(stats.dispute_breakdown || {}).map(([k, v]) => ({
    name: k.replace('_', ' '), value: v,
  }));

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 overflow-y-auto h-full">
      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Queries Today" value={stats.total_queries_today} subtitle={`${stats.total_queries_all} total`} icon={MessageSquare} color="blue" />
        <StatCard title="Active Users" value={stats.active_users_today} subtitle={`${stats.total_employees} total employees`} icon={Users} color="green" />
        <StatCard title="Open Disputes" value={stats.open_disputes} subtitle={`${stats.total_disputes} total`} icon={AlertTriangle} color="amber" />
        <StatCard title="Resolution Rate" value={stats.total_disputes > 0 ? `${Math.round((stats.dispute_breakdown?.resolved || 0) / stats.total_disputes * 100)}%` : 'N/A'} subtitle="Disputes resolved" icon={TrendingUp} color="purple" />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Query Volume */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-gray-200 p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Query Volume (Last 7 Days)</h3>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={stats.query_volume_7days}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="day" tick={{ fontSize: 12 }} stroke="#94a3b8" />
              <YAxis tick={{ fontSize: 12 }} stroke="#94a3b8" />
              <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
              <Line type="monotone" dataKey="queries" stroke="#3b82f6" strokeWidth={2} dot={{ r: 4, fill: '#3b82f6' }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Intent Distribution */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Intent Distribution</h3>
          {stats.intent_distribution?.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={stats.intent_distribution} dataKey="count" nameKey="intent" cx="50%" cy="50%" outerRadius={80} label={({ intent, percent }) => `${intent} ${(percent * 100).toFixed(0)}%`}>
                  {stats.intent_distribution.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-60 text-sm text-gray-400">No data yet</div>
          )}
        </div>
      </div>

      {/* Dispute Breakdown & Recent Queries */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Disputes */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Dispute Status</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={disputeData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} stroke="#94a3b8" />
              <YAxis tick={{ fontSize: 12 }} stroke="#94a3b8" />
              <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
              <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Recent Queries */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-gray-200 p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Recent Queries</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-gray-500 border-b border-gray-100">
                  <th className="pb-2 font-medium">Employee</th>
                  <th className="pb-2 font-medium">Query</th>
                  <th className="pb-2 font-medium">Intent</th>
                  <th className="pb-2 font-medium">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {(stats.recent_queries || []).slice(0, 10).map((q, i) => (
                  <tr key={i} className="hover:bg-gray-50">
                    <td className="py-2 text-gray-900 font-medium">{q.employee_name}</td>
                    <td className="py-2 text-gray-600 max-w-xs truncate">{q.query}</td>
                    <td className="py-2">
                      <span className="px-2 py-0.5 rounded-full text-xs bg-blue-50 text-blue-700 font-medium capitalize">
                        {q.intent}
                      </span>
                    </td>
                    <td className="py-2 text-gray-400 text-xs">
                      {q.timestamp ? new Date(q.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {(!stats.recent_queries || stats.recent_queries.length === 0) && (
              <p className="text-center py-8 text-sm text-gray-400">No queries yet</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
