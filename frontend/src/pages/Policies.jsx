/**
 * Browse HR policy documents from the API; search and read full policy text in a panel.
 */
import { useState, useEffect } from 'react';
import { BookOpen, Search, FileText } from 'lucide-react';
import api from '../api/axios';
import LoadingSpinner from '../components/LoadingSpinner';

export default function Policies() {
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedPolicy, setSelectedPolicy] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    api.get('/policies')
      .then(res => setPolicies(res.data.policies || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const filtered = policies.filter(p =>
    p.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const categoryColors = {
    Leave: 'bg-blue-100 text-blue-700',
    Compensation: 'bg-green-100 text-green-700',
    Benefits: 'bg-purple-100 text-purple-700',
    Compliance: 'bg-red-100 text-red-700',
  };

  if (loading) return <div className="flex items-center justify-center h-full"><LoadingSpinner text="Loading policies..." /></div>;

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6 overflow-y-auto h-full">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Policy Library</h2>
          <p className="text-sm text-gray-500">{policies.length} documents available</p>
        </div>
        <div className="relative">
          <Search size={16} className="absolute left-3 top-2.5 text-gray-400" />
          <input
            type="text" value={searchTerm} onChange={e => setSearchTerm(e.target.value)}
            placeholder="Search policies..."
            className="pl-9 pr-4 py-2 rounded-lg border border-gray-300 text-sm focus:ring-2 focus:ring-primary-500 outline-none w-64"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filtered.map(p => (
          <div
            key={p.id}
            onClick={() => setSelectedPolicy(p)}
            className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow cursor-pointer group"
          >
            <div className="flex items-start gap-3">
              <div className="p-2.5 rounded-lg bg-primary-50 text-primary-600 group-hover:bg-primary-100 transition">
                <FileText size={20} />
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-gray-900 group-hover:text-primary-700 transition">{p.title}</h3>
                <div className="flex items-center gap-2 mt-1.5">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${categoryColors[p.category] || 'bg-gray-100 text-gray-600'}`}>
                    {p.category}
                  </span>
                  <span className="text-xs text-gray-400">
                    {p.uploaded_at ? new Date(p.uploaded_at).toLocaleDateString() : ''}
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-2 line-clamp-2">{p.content?.slice(0, 120)}...</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-12">
          <BookOpen size={40} className="mx-auto text-gray-300 mb-3" />
          <p className="text-gray-500">No policies found</p>
        </div>
      )}

      {/* Policy Detail Modal */}
      {selectedPolicy && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4" onClick={() => setSelectedPolicy(null)}>
          <div className="bg-white rounded-2xl max-w-3xl w-full p-6 max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4 sticky top-0 bg-white pb-3 border-b border-gray-100">
              <div>
                <h3 className="text-lg font-bold text-gray-900">{selectedPolicy.title}</h3>
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${categoryColors[selectedPolicy.category] || 'bg-gray-100 text-gray-600'}`}>
                  {selectedPolicy.category}
                </span>
              </div>
              <button onClick={() => setSelectedPolicy(null)} className="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
            </div>
            <div className="prose text-sm whitespace-pre-line text-gray-700 leading-relaxed">
              {selectedPolicy.content}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
