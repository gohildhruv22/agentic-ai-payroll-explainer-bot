/**
 * Top-level routes and shell layout: sidebar, navbar, and role-based pages (employee vs HR vs admin).
 * Chat sessions are listed in the sidebar; admin skips chat and uses dashboard + dispute admin.
 */
import { useState, useEffect, useCallback } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import api from './api/axios';
import ProtectedRoute from './components/ProtectedRoute';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Chat from './pages/Chat';
import Dashboard from './pages/Dashboard';
import Payroll from './pages/Payroll';
import Disputes from './pages/Disputes';
import Policies from './pages/Policies';
import Settings from './pages/Settings';
import AdminDisputes from './pages/AdminDisputes';
import AutonomyOps from './pages/AutonomyOps';

function AppLayout() {
  const { isAdmin } = useAuth();
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);

  const refreshSessions = useCallback(() => {
    if (isAdmin) return; // Admin doesn't use chat
    api.get('/chat/sessions')
      .then(res => setSessions(res.data.sessions || []))
      .catch(() => {});
  }, [isAdmin]);

  useEffect(() => { refreshSessions(); }, [refreshSessions]);

  const handleNewChat = () => setActiveSession(null);
  const handleSelectSession = (sid) => setActiveSession(sid);

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar
        sessions={sessions}
        onNewChat={handleNewChat}
        onSelectSession={handleSelectSession}
        activeSession={activeSession}
      />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar />
        <main className="flex-1 overflow-hidden">
          <Routes>
            {isAdmin ? (
              <>
                {/* Admin only sees Dashboard + Dispute Management */}
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/admin-disputes" element={<AdminDisputes />} />
                <Route path="/autonomy-ops" element={<AutonomyOps />} />
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </>
            ) : (
              <>
                {/* Employee / HR Manager routes */}
                <Route path="/" element={<Chat sessionId={activeSession} setSessionId={setActiveSession} refreshSessions={refreshSessions} />} />
                <Route path="/payroll" element={<Payroll />} />
                <Route path="/disputes" element={<Disputes />} />
                <Route path="/policies" element={<Policies />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/dashboard" element={
                  <ProtectedRoute requiredRole={['hr_manager']}>
                    <Dashboard />
                  </ProtectedRoute>
                } />
                <Route path="*" element={<Navigate to="/" replace />} />
              </>
            )}
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-800"></div>
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/" replace /> : <Login />} />
      <Route path="/*" element={
        <ProtectedRoute>
          <AppLayout />
        </ProtectedRoute>
      } />
    </Routes>
  );
}
