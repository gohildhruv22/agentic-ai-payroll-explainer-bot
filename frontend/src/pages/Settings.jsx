/**
 * Read-only profile summary from auth context (name, org, role, contact).
 */
import { useAuth } from '../context/AuthContext';
import { User, Building, MapPin, Calendar, Shield, Mail } from 'lucide-react';

export default function Settings() {
  const { user } = useAuth();

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6 overflow-y-auto h-full">
      <div>
        <h2 className="text-lg font-bold text-gray-900">Settings</h2>
        <p className="text-sm text-gray-500">Manage your profile and preferences</p>
      </div>

      {/* Profile Card */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-sm font-semibold text-gray-900 mb-4">Profile Information</h3>
        <div className="flex items-center gap-4 mb-6">
          <div className="w-16 h-16 rounded-full bg-primary-100 flex items-center justify-center">
            <span className="text-xl font-bold text-primary-800">
              {user?.name?.split(' ').map(n => n[0]).join('').slice(0, 2)}
            </span>
          </div>
          <div>
            <h4 className="text-base font-semibold text-gray-900">{user?.name}</h4>
            <p className="text-sm text-gray-500">{user?.designation}</p>
            <span className="inline-block mt-1 px-2 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-700 capitalize">
              {user?.role?.replace('_', ' ')}
            </span>
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {[
            { icon: Mail, label: 'Email', value: user?.email },
            { icon: User, label: 'Employee ID', value: user?.emp_id },
            { icon: Building, label: 'Department', value: user?.department },
            { icon: MapPin, label: 'Location', value: user?.location },
            { icon: Shield, label: 'Grade', value: user?.grade },
            { icon: Calendar, label: 'Joining Date', value: user?.joining_date },
          ].map((item, i) => (
            <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-gray-50">
              <item.icon size={16} className="text-gray-400 flex-shrink-0" />
              <div>
                <p className="text-[10px] text-gray-400 uppercase tracking-wider">{item.label}</p>
                <p className="text-sm font-medium text-gray-900">{item.value || 'N/A'}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Preferences */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-sm font-semibold text-gray-900 mb-4">Preferences</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-900">Language</p>
              <p className="text-xs text-gray-500">Interface language preference</p>
            </div>
            <select className="px-3 py-1.5 rounded-lg border border-gray-300 text-sm bg-white">
              <option>English</option>
              <option>Hindi</option>
            </select>
          </div>
          <div className="border-t border-gray-100 pt-4 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-900">Email Notifications</p>
              <p className="text-xs text-gray-500">Receive dispute updates via email</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" defaultChecked className="sr-only peer" />
              <div className="w-9 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary-600"></div>
            </label>
          </div>
          <div className="border-t border-gray-100 pt-4 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-900">Payslip Reminders</p>
              <p className="text-xs text-gray-500">Monthly payslip availability alerts</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" defaultChecked className="sr-only peer" />
              <div className="w-9 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary-600"></div>
            </label>
          </div>
        </div>
      </div>

      {/* About */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-sm font-semibold text-gray-900 mb-2">About</h3>
        <p className="text-xs text-gray-500">
          Payroll Explainer Bot v1.0 — Agentic AI powered by Groq.
          Multi-agent system with Payroll Calculator, Compliance Agent, Policy Explainer, and Dispute Resolver.
        </p>
      </div>
    </div>
  );
}
