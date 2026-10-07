/**
 * Top bar: dynamic page title from route and simple actions placeholder (search/bell).
 */
import { useLocation } from 'react-router-dom';
import { useEffect, useRef, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Bell, Search } from 'lucide-react';
import api from '../api/axios';
import toast from 'react-hot-toast';

const pageTitles = {
  '/': 'AI Chat Assistant',
  '/payroll': 'My Payroll',
  '/disputes': 'Disputes',
  '/policies': 'Policy Library',
  '/dashboard': 'HR Dashboard',
  '/autonomy-ops': 'Autonomy Operations',
  '/settings': 'Settings',
};

export default function Navbar() {
  const location = useLocation();
  const { user } = useAuth();
  const title = pageTitles[location.pathname] || 'Payroll Bot';
  const [notifOpen, setNotifOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const menuRef = useRef(null);

  const loadNotifications = async () => {
    try {
      const res = await api.get('/notifications/my');
      setNotifications(res.data.notifications || []);
      setUnreadCount(res.data.unread_count || 0);
    } catch {
      // keep silent to avoid noisy UX
    }
  };

  useEffect(() => {
    loadNotifications();
    const id = setInterval(loadNotifications, 15000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    const onClick = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setNotifOpen(false);
    };
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, []);

  const markOneRead = async (id) => {
    try {
      await api.post(`/notifications/mark-read/${id}`);
      await loadNotifications();
    } catch {
      toast.error('Failed to update notification');
    }
  };

  const markAllRead = async () => {
    try {
      await api.post('/notifications/mark-all-read');
      await loadNotifications();
    } catch {
      toast.error('Failed to mark all as read');
    }
  };

  return (
    <header className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-6">
      <div>
        <h2 className="text-base font-semibold text-gray-900">{title}</h2>
      </div>
      <div className="flex items-center gap-3" ref={menuRef}>
        <div className="relative">
          <button
            onClick={() => setNotifOpen((v) => !v)}
            className="p-2 rounded-lg hover:bg-gray-100 text-gray-500 relative"
          >
            <Bell size={18} />
            {unreadCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 min-w-[16px] h-4 px-1 bg-red-500 text-white text-[10px] rounded-full flex items-center justify-center">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </button>
          {notifOpen && (
            <div className="absolute right-0 mt-2 w-96 bg-white border border-gray-200 rounded-xl shadow-lg z-50">
              <div className="px-3 py-2 border-b border-gray-100 flex items-center justify-between">
                <p className="text-sm font-semibold text-gray-900">Notifications</p>
                <button onClick={markAllRead} className="text-xs text-primary-700 hover:underline">Mark all read</button>
              </div>
              <div className="max-h-80 overflow-y-auto">
                {notifications.length === 0 && <p className="p-4 text-sm text-gray-400">No notifications</p>}
                {notifications.map((n) => (
                  <button
                    key={n.id}
                    onClick={() => markOneRead(n.id)}
                    className={`w-full text-left px-3 py-2 border-b border-gray-50 hover:bg-gray-50 ${n.status !== 'read' ? 'bg-blue-50/40' : ''}`}
                  >
                    <p className="text-xs font-medium text-gray-900">{n.subject}</p>
                    <p className="text-xs text-gray-600 mt-0.5">{n.body}</p>
                    <p className="text-[10px] text-gray-400 mt-1">{n.sent_at ? new Date(n.sent_at).toLocaleString() : ''}</p>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
        <div className="h-8 w-px bg-gray-200" />
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-600 to-violet-500 flex items-center justify-center shadow-sm">
            <span className="text-xs font-semibold text-white">
              {user?.name?.split(' ').map(n => n[0]).join('').slice(0, 2)}
            </span>
          </div>
          <div className="hidden sm:block">
            <p className="text-xs font-medium text-gray-900">{user?.name}</p>
            <p className="text-[10px] text-gray-400">{user?.designation}</p>
          </div>
        </div>
      </div>
    </header>
  );
}
