/**
 * Left navigation: app routes, collapse toggle, chat session list, logout.
 */
import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  MessageSquare, CreditCard, AlertTriangle, BookOpen, Settings,
  LayoutDashboard, Plus, ChevronLeft, ChevronRight, User, LogOut, FileText,
  ShieldCheck
} from 'lucide-react';
import { useState } from 'react';

export default function Sidebar({ sessions = [], onNewChat, onSelectSession, activeSession }) {
  const { user, logout, isHR, isAdmin } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  const navItems = [
    // Admin-only items
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', adminOnly: true },
    { path: '/admin-disputes', icon: ShieldCheck, label: 'Dispute Review', adminOnly: true },
    { path: '/autonomy-ops', icon: Settings, label: 'Autonomy Ops', adminOnly: true },
    // HR + Employee items (not shown to admin)
    { path: '/', icon: MessageSquare, label: 'Chat', employeeHR: true },
    { path: '/payroll', icon: CreditCard, label: 'My Payroll', employeeHR: true },
    { path: '/disputes', icon: AlertTriangle, label: 'Disputes', employeeHR: true },
    { path: '/policies', icon: BookOpen, label: 'Policies', employeeHR: true },
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', hrOnly: true },
    { path: '/settings', icon: Settings, label: 'Settings', employeeHR: true },
  ];

  const filteredNav = navItems.filter(item => {
    if (isAdmin) return item.adminOnly;
    if (item.adminOnly) return false;
    if (item.hrOnly) return isHR;
    return item.employeeHR;
  });

  const groupSessions = (sessions) => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today); yesterday.setDate(yesterday.getDate() - 1);
    const weekAgo = new Date(today); weekAgo.setDate(weekAgo.getDate() - 7);

    const groups = { 'Today': [], 'Yesterday': [], 'This Week': [], 'Earlier': [] };
    sessions.forEach(s => {
      const d = new Date(s.last_active || s.created_at);
      if (d >= today) groups['Today'].push(s);
      else if (d >= yesterday) groups['Yesterday'].push(s);
      else if (d >= weekAgo) groups['This Week'].push(s);
      else groups['Earlier'].push(s);
    });
    return groups;
  };

  const grouped = groupSessions(sessions);

  return (
    <aside className={`h-screen bg-white border-r border-gray-200 flex flex-col transition-all duration-300 ${collapsed ? 'w-16' : 'w-72'}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-100 flex items-center justify-between">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-600 to-violet-500 flex items-center justify-center shadow-sm">
              <FileText size={16} className="text-white" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-purple-800">PayrollBot</h1>
              <p className="text-[10px] text-gray-400">AI Assistant</p>
            </div>
          </div>
        )}
        <button onClick={() => setCollapsed(!collapsed)} className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400">
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* New Chat */}
      {!collapsed && location.pathname === '/' && (
        <div className="p-3">
          <button
            onClick={onNewChat}
            className="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg border border-dashed border-gray-300
                       text-sm text-gray-600 hover:border-primary-400 hover:text-primary-700 hover:bg-primary-50 transition-all"
          >
            <Plus size={16} /> New Chat
          </button>
        </div>
      )}

      {/* Navigation */}
      <nav className="px-3 py-2 space-y-0.5">
        {filteredNav.map(item => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all ${
                isActive
                  ? 'bg-primary-50 text-primary-800 font-medium'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              } ${collapsed ? 'justify-center' : ''}`
            }
          >
            <item.icon size={18} />
            {!collapsed && <span>{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Chat Sessions */}
      {!collapsed && location.pathname === '/' && sessions.length > 0 && (
        <div className="flex-1 overflow-y-auto px-3 py-2">
          <p className="text-[10px] uppercase font-semibold text-gray-400 px-3 mb-2 tracking-wider">History</p>
          {Object.entries(grouped).map(([group, items]) => items.length > 0 && (
            <div key={group} className="mb-2">
              <p className="text-[10px] text-gray-400 px-3 mb-1">{group}</p>
              {items.map(s => (
                <button
                  key={s.session_id}
                  onClick={() => onSelectSession(s.session_id)}
                  className={`w-full text-left px-3 py-1.5 rounded-lg text-xs truncate transition-all ${
                    activeSession === s.session_id
                      ? 'bg-primary-50 text-primary-800 font-medium'
                      : 'text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  {s.title}
                </button>
              ))}
            </div>
          ))}
        </div>
      )}

      <div className="mt-auto" />

      {/* User Info */}
      <div className="p-3 border-t border-gray-100">
        <div className={`flex items-center gap-3 ${collapsed ? 'justify-center' : ''}`}>
          <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
            <User size={14} className="text-primary-700" />
          </div>
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-gray-900 truncate">{user?.name}</p>
              <p className="text-[10px] text-gray-400 capitalize">{user?.role?.replace('_', ' ')}</p>
            </div>
          )}
          {!collapsed && (
            <button onClick={logout} className="p-1.5 rounded-lg hover:bg-red-50 text-gray-400 hover:text-red-500">
              <LogOut size={14} />
            </button>
          )}
        </div>
      </div>
    </aside>
  );
}
