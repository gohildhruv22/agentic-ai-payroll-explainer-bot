/**
 * Two-column earnings vs deductions table for one month’s salary record (formatted ₹).
 */
export default function SalaryTable({ record }) {
  if (!record) return null;

  const fmt = (v) => v ? `₹${Number(v).toLocaleString('en-IN')}` : '₹0';

  const earnings = [
    { label: 'Basic Salary', amount: record.basic },
    { label: 'House Rent Allowance', amount: record.hra },
    { label: 'Dearness Allowance', amount: record.da },
    { label: 'Special Allowance', amount: record.special_allowance },
    { label: 'Medical Allowance', amount: record.medical },
    { label: 'Leave Travel Allowance', amount: record.lta },
    ...(record.bonus > 0 ? [{ label: 'Bonus', amount: record.bonus }] : []),
    ...(record.arrears > 0 ? [{ label: 'Arrears', amount: record.arrears }] : []),
    ...(record.overtime > 0 ? [{ label: 'Overtime', amount: record.overtime }] : []),
  ];

  const deductions = [
    { label: 'Provident Fund', amount: record.pf_employee },
    { label: 'ESIC', amount: record.esic_employee },
    { label: 'Professional Tax', amount: record.professional_tax },
    { label: 'TDS', amount: record.tds },
    ...(record.lop_deduction > 0 ? [{ label: 'LOP Deduction', amount: record.lop_deduction }] : []),
  ];

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="grid grid-cols-2 divide-x divide-gray-200">
        <div>
          <div className="bg-emerald-50 px-4 py-2.5 border-b border-gray-200">
            <h4 className="text-sm font-semibold text-emerald-800">Earnings</h4>
          </div>
          <div className="divide-y divide-gray-100">
            {earnings.map((e, i) => (
              <div key={i} className="flex justify-between px-4 py-2 text-sm">
                <span className="text-gray-600">{e.label}</span>
                <span className="font-medium text-gray-900">{fmt(e.amount)}</span>
              </div>
            ))}
            <div className="flex justify-between px-4 py-2.5 bg-emerald-50 font-semibold text-sm">
              <span className="text-emerald-800">Gross Earnings</span>
              <span className="text-emerald-800">{fmt(record.gross_pay)}</span>
            </div>
          </div>
        </div>
        <div>
          <div className="bg-red-50 px-4 py-2.5 border-b border-gray-200">
            <h4 className="text-sm font-semibold text-red-800">Deductions</h4>
          </div>
          <div className="divide-y divide-gray-100">
            {deductions.map((d, i) => (
              <div key={i} className="flex justify-between px-4 py-2 text-sm">
                <span className="text-gray-600">{d.label}</span>
                <span className="font-medium text-gray-900">{fmt(d.amount)}</span>
              </div>
            ))}
            <div className="flex justify-between px-4 py-2.5 bg-red-50 font-semibold text-sm">
              <span className="text-red-800">Total Deductions</span>
              <span className="text-red-800">{fmt(record.total_deductions)}</span>
            </div>
          </div>
        </div>
      </div>
      <div className="bg-gradient-to-r from-purple-700 to-violet-600 px-6 py-4 flex justify-between items-center">
        <span className="text-white text-lg font-bold">Net Pay</span>
        <span className="text-white text-2xl font-bold">{fmt(record.net_pay)}</span>
      </div>
    </div>
  );
}
