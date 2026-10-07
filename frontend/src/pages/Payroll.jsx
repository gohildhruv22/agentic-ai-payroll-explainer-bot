/**
 * Employee payroll view: month selector, salary breakdown, trend chart, PDF download.
 */
import { useState, useEffect } from 'react';
import { Download, ChevronDown, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import api from '../api/axios';
import { useAuth } from '../context/AuthContext';
import SalaryTable from '../components/SalaryTable';
import LoadingSpinner from '../components/LoadingSpinner';
import toast from 'react-hot-toast';

const MONTHS = [
  { value: '2026-04', label: 'April 2026' },
  { value: '2026-03', label: 'March 2026' },
  { value: '2026-02', label: 'February 2026' },
  { value: '2026-01', label: 'January 2026' },
  { value: '2025-12', label: 'December 2025' },
  { value: '2025-11', label: 'November 2025' },
];

export default function Payroll() {
  const { user } = useAuth();
  const [selectedMonth, setSelectedMonth] = useState('2026-04');
  const [record, setRecord] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [selectedMonth]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [recRes, histRes] = await Promise.all([
        api.get(`/payroll/${user.id}/${selectedMonth}`).catch(() => null),
        api.get(`/payroll/${user.id}/history`).catch(() => null),
      ]);
      setRecord(recRes?.data?.record || null);
      setHistory(histRes?.data?.records || []);
    } catch {
      toast.error('Failed to load payroll data');
    } finally {
      setLoading(false);
    }
  };

  const downloadPayslip = async () => {
    try {
      const res = await api.get(`/payroll/download/${user.emp_id}/${selectedMonth}`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `payslip_${user.emp_id}_${selectedMonth}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success('Payslip downloaded');
    } catch {
      toast.error('Failed to download payslip');
    }
  };

  const chartData = [...history].reverse().map(r => ({
    month: r.month.slice(5),
    net_pay: r.net_pay,
    gross_pay: r.gross_pay,
  }));

  const prevMonth = history.find((_, i) => history[i - 1]?.month === selectedMonth);
  const netDiff = record && prevMonth ? record.net_pay - prevMonth.net_pay : 0;

  if (loading) return <div className="flex items-center justify-center h-full"><LoadingSpinner text="Loading payroll..." /></div>;

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6 overflow-y-auto h-full">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Salary Details</h2>
          <p className="text-sm text-gray-500">View your monthly salary breakdown</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <select
              value={selectedMonth}
              onChange={e => setSelectedMonth(e.target.value)}
              className="appearance-none pl-4 pr-8 py-2 rounded-lg border border-gray-300 text-sm bg-white focus:ring-2 focus:ring-primary-500 outline-none cursor-pointer"
            >
              {MONTHS.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
            </select>
            <ChevronDown size={14} className="absolute right-2.5 top-3 text-gray-400 pointer-events-none" />
          </div>
          {record && (
            <button onClick={downloadPayslip}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary-800 text-white text-sm font-medium hover:bg-primary-900 transition">
              <Download size={16} /> Download PDF
            </button>
          )}
        </div>
      </div>

      {/* Net Pay Summary */}
      {record && (
        <div className="bg-gradient-to-r from-primary-800 to-primary-900 rounded-xl p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-primary-200">Net Take-Home Pay</p>
              <p className="text-3xl font-bold mt-1">₹{record.net_pay?.toLocaleString('en-IN')}</p>
              {netDiff !== 0 && (
                <div className={`flex items-center gap-1 mt-2 text-sm ${netDiff > 0 ? 'text-green-300' : 'text-red-300'}`}>
                  {netDiff > 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                  ₹{Math.abs(netDiff).toLocaleString('en-IN')} {netDiff > 0 ? 'more' : 'less'} than previous month
                </div>
              )}
            </div>
            <div className="text-right">
              <p className="text-sm text-primary-200">Monthly CTC</p>
              <p className="text-xl font-semibold">₹{record.ctc?.toLocaleString('en-IN')}</p>
            </div>
          </div>
        </div>
      )}

      {/* Salary Breakdown */}
      {record ? (
        <SalaryTable record={record} />
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <p className="text-gray-500">No salary record found for this month</p>
        </div>
      )}

      {/* Trend Chart */}
      {chartData.length > 1 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">6-Month Salary Trend</h3>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} stroke="#94a3b8" />
              <YAxis tick={{ fontSize: 12 }} stroke="#94a3b8" tickFormatter={v => `₹${(v/1000).toFixed(0)}k`} />
              <Tooltip formatter={v => `₹${v.toLocaleString('en-IN')}`} contentStyle={{ fontSize: 12, borderRadius: 8 }} />
              <Line type="monotone" dataKey="net_pay" stroke="#3b82f6" strokeWidth={2} name="Net Pay" dot={{ r: 4 }} />
              <Line type="monotone" dataKey="gross_pay" stroke="#10b981" strokeWidth={2} name="Gross Pay" dot={{ r: 4 }} strokeDasharray="5 5" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
