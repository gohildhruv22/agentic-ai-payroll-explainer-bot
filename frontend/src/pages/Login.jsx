/**
 * Email/password login form; stores JWT and user, then navigates to the app.
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { FileText, Eye, EyeOff, Sparkles, ArrowRight } from 'lucide-react';
import toast from 'react-hot-toast';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) { toast.error('Please fill in all fields'); return; }
    setLoading(true);
    try {
      await login(email, password);
      toast.success('Welcome back!');
      navigate('/');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 via-white to-violet-50 p-4 relative overflow-hidden">
      {/* Background decorative elements */}
      <div className="absolute top-0 left-0 w-[500px] h-[500px] bg-purple-200/30 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2" />
      <div className="absolute bottom-0 right-0 w-[400px] h-[400px] bg-violet-200/30 rounded-full blur-3xl translate-x-1/3 translate-y-1/3" />
      <div className="absolute top-1/2 left-1/2 w-[300px] h-[300px] bg-fuchsia-100/20 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2" />

      <div className="w-full max-w-[440px] relative z-10">
        <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-[0_8px_40px_rgba(107,33,168,0.08)] border border-purple-100/50 p-8 sm:p-10 animate-fade-in">
          {/* Logo */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-600 to-violet-500 flex items-center justify-center mx-auto mb-5 shadow-lg shadow-purple-200/50 rotate-3 hover:rotate-0 transition-transform duration-300">
              <FileText size={28} className="text-white" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Payroll Explainer Bot</h1>
            <div className="flex items-center justify-center gap-1.5 mt-2">
              <Sparkles size={14} className="text-purple-400" />
              <p className="text-sm text-gray-400">AI-Powered HR Assistant</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Email Address</label>
              <input
                type="email" value={email} onChange={e => setEmail(e.target.value)}
                placeholder="name@company.com"
                className="w-full px-4 py-3 rounded-xl border border-gray-200 text-sm bg-gray-50/50 focus:bg-white focus:ring-2 focus:ring-purple-500/20 focus:border-purple-400 outline-none transition-all duration-200 placeholder:text-gray-300"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Password</label>
              <div className="relative">
                <input
                  type={showPw ? 'text' : 'password'} value={password} onChange={e => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full px-4 py-3 rounded-xl border border-gray-200 text-sm bg-gray-50/50 focus:bg-white focus:ring-2 focus:ring-purple-500/20 focus:border-purple-400 outline-none transition-all duration-200 pr-10 placeholder:text-gray-300"
                />
                <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-3 top-3 text-gray-300 hover:text-gray-500 transition-colors">
                  {showPw ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>
            <button
              type="submit" disabled={loading}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-purple-600 to-violet-500 text-white text-sm font-semibold hover:from-purple-700 hover:to-violet-600 focus:ring-4 focus:ring-purple-200 transition-all duration-200 disabled:opacity-50 shadow-md shadow-purple-200/50 flex items-center justify-center gap-2 group"
            >
              {loading ? (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Signing in...
                </div>
              ) : (
                <>
                  Sign In
                  <ArrowRight size={16} className="group-hover:translate-x-0.5 transition-transform" />
                </>
              )}
            </button>
          </form>

          <div className="mt-8 pt-6 border-t border-gray-100/80">
            <p className="text-xs text-gray-400 text-center mb-3 font-medium uppercase tracking-wider">Quick Access</p>
            <div className="space-y-2">
              {[
                { label: 'Employee', email: 'rahul.sharma@company.com', color: 'bg-blue-50 border-blue-100 hover:bg-blue-100/70' },
                { label: 'HR Manager', email: 'priya.patel@company.com', color: 'bg-purple-50 border-purple-100 hover:bg-purple-100/70' },
                { label: 'Admin', email: 'neha.agarwal@company.com', color: 'bg-amber-50 border-amber-100 hover:bg-amber-100/70' },
              ].map(cred => (
                <button
                  key={cred.email}
                  onClick={() => { setEmail(cred.email); setPassword('password123'); }}
                  className={`w-full flex items-center justify-between px-4 py-2.5 rounded-xl border transition-all duration-200 text-xs ${cred.color}`}
                >
                  <span className="font-semibold text-gray-700">{cred.label}</span>
                  <span className="text-gray-400 font-mono text-[11px]">{cred.email}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        <p className="text-center text-xs text-gray-300 mt-6">Secured with JWT Authentication</p>
      </div>
    </div>
  );
}
