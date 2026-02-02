import { useState } from 'react';
import { Sidebar } from './Sidebar';
import { Plus, Trash2, ChevronRight, ChevronDown, RefreshCw, CheckCircle2, AlertCircle } from 'lucide-react';
import { monitoredCompanies, companiesWithFilings } from '../data/mockData';
import type { MonitoredCompany, CompanyWithFilings } from '../data/mockData';

export function Settings() {
  const [cikInput, setCikInput] = useState('');
  const [companies, setCompanies] = useState<MonitoredCompany[]>(monitoredCompanies);
  const [updateFrequency, setUpdateFrequency] = useState('weekly');
  const [isUpdating, setIsUpdating] = useState(false);
  const [expandedCompanies, setExpandedCompanies] = useState<Set<string>>(new Set());
  const [selectedFilings, setSelectedFilings] = useState<Set<string>>(new Set());

  const handleAddCompany = () => {
    if (cikInput) {
      const newCompany: MonitoredCompany = {
        id: Date.now().toString(),
        cik: cikInput,
        name: `Company ${cikInput}`,
        addedDate: new Date().toISOString().split('T')[0],
      };
      setCompanies([...companies, newCompany]);
      setCikInput('');
    }
  };

  const handleDeleteCompany = (id: string) => {
    setCompanies(companies.filter((c) => c.id !== id));
  };

  const handleManualUpdate = () => {
    setIsUpdating(true);
    setTimeout(() => setIsUpdating(false), 2000);
  };

  const toggleCompanyExpansion = (companyId: string) => {
    const newExpanded = new Set(expandedCompanies);
    if (newExpanded.has(companyId)) {
      newExpanded.delete(companyId);
    } else {
      newExpanded.add(companyId);
    }
    setExpandedCompanies(newExpanded);
  };

  const toggleFilingSelection = (filingId: string) => {
    const newSelected = new Set(selectedFilings);
    if (newSelected.has(filingId)) {
      newSelected.delete(filingId);
    } else {
      newSelected.add(filingId);
    }
    setSelectedFilings(newSelected);
  };

  const handleDeleteSelected = () => {
    setSelectedFilings(new Set());
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      
      <div className="flex-1 overflow-y-auto">
        <div className="p-8 max-w-6xl">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2">Data Configuration</h1>
            <p className="text-[var(--text-secondary)]">
              Manage tracked companies, update schedules, and database maintenance
            </p>
          </div>

          {/* Section 1: Target Management */}
          <div className="grid grid-cols-3 gap-6 mb-6">
            <div className="col-span-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Target Management</h2>
              
              <div className="mb-4">
                <label className="block text-sm text-[var(--text-secondary)] mb-2">
                  CIK Code
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={cikInput}
                    onChange={(e) => setCikInput(e.target.value)}
                    placeholder="e.g., 0000789019"
                    className="flex-1 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded px-3 py-2 text-sm mono focus:outline-none focus:border-[var(--accent-buy)]"
                  />
                  <button
                    onClick={handleAddCompany}
                    className="bg-[var(--accent-buy)] hover:bg-[var(--accent-buy)]/80 text-black font-semibold px-4 py-2 rounded flex items-center gap-2 transition-colors"
                  >
                    <Plus size={18} />
                    Add
                  </button>
                </div>
              </div>

              {/* Company List */}
              <div className="bg-[var(--bg-tertiary)] rounded-lg overflow-hidden">
                <table className="w-full">
                  <thead className="bg-[var(--bg-primary)] text-[var(--text-secondary)] text-xs uppercase">
                    <tr>
                      <th className="px-4 py-3 text-left font-medium">CIK</th>
                      <th className="px-4 py-3 text-left font-medium">Company Name</th>
                      <th className="px-4 py-3 text-left font-medium">Added Date</th>
                      <th className="px-4 py-3 text-center font-medium">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {companies.map((company, index) => (
                      <tr
                        key={company.id}
                        className={`border-b border-[var(--border-color)] ${
                          index === companies.length - 1 ? 'border-b-0' : ''
                        }`}
                      >
                        <td className="px-4 py-3 text-sm mono">{company.cik}</td>
                        <td className="px-4 py-3 text-sm">{company.name}</td>
                        <td className="px-4 py-3 text-sm text-[var(--text-secondary)]">
                          {company.addedDate}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <button
                            onClick={() => handleDeleteCompany(company.id)}
                            className="text-[var(--accent-sell)] hover:text-[var(--accent-sell)]/80 transition-colors"
                          >
                            <Trash2 size={18} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Section 2: Crawler Scheduler */}
            <div className="col-span-1 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Crawler Scheduler</h2>
              
              <div className="mb-6">
                <label className="block text-sm text-[var(--text-secondary)] mb-2">
                  Update Frequency
                </label>
                <select
                  value={updateFrequency}
                  onChange={(e) => setUpdateFrequency(e.target.value)}
                  className="w-full bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded px-3 py-2 text-sm focus:outline-none focus:border-[var(--accent-buy)]"
                >
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="quarterly">Quarterly</option>
                </select>
              </div>
              
              <div>
                <button
                  onClick={handleManualUpdate}
                  disabled={isUpdating}
                  className="w-full bg-[var(--accent-buy)] hover:bg-[var(--accent-buy)]/80 disabled:opacity-50 disabled:cursor-not-allowed text-black font-semibold px-4 py-2 rounded flex items-center justify-center gap-2 transition-colors"
                >
                  <RefreshCw size={18} className={isUpdating ? 'animate-spin' : ''} />
                  {isUpdating ? 'Updating...' : 'Trigger Manual Update Now'}
                </button>
                <p className="mt-3 text-xs text-[var(--text-secondary)] leading-relaxed">
                  Auto and manual updates download the latest and previous filings. Existing filings in the database will be skipped.
                </p>
              </div>
            </div>
          </div>

          {/* Section 3: Database Maintenance & Crawl Status */}
          <div className="grid grid-cols-3 gap-6">
            <div className="col-span-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold">Database Maintenance</h2>
                {selectedFilings.size > 0 && (
                  <button
                    onClick={handleDeleteSelected}
                    className="bg-[var(--accent-sell)] hover:bg-[var(--accent-sell)]/80 text-white font-semibold px-4 py-2 rounded flex items-center gap-2 transition-colors text-sm"
                  >
                    <Trash2 size={16} />
                    Delete Selected ({selectedFilings.size})
                  </button>
                )}
              </div>

              <div className="bg-[var(--bg-tertiary)] rounded-lg overflow-hidden max-h-[500px] overflow-y-auto">
                {companiesWithFilings.map((company) => (
                  <div key={company.id} className="border-b border-[var(--border-color)] last:border-b-0">
                    {/* Company Row */}
                    <div
                      onClick={() => toggleCompanyExpansion(company.id)}
                      className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-[var(--bg-primary)] transition-colors"
                    >
                      {expandedCompanies.has(company.id) ? (
                        <ChevronDown size={18} className="text-[var(--text-secondary)]" />
                      ) : (
                        <ChevronRight size={18} className="text-[var(--text-secondary)]" />
                      )}
                      <span className="font-semibold">{company.name}</span>
                      <span className="text-xs text-[var(--text-secondary)] mono">
                        ({company.filings.length} filings)
                      </span>
                    </div>

                    {/* Filing Rows */}
                    {expandedCompanies.has(company.id) && (
                      <div className="bg-[var(--bg-primary)]">
                        {company.filings.map((filing) => (
                          <div
                            key={filing.id}
                            className="flex items-center gap-3 px-4 py-2 pl-12 hover:bg-[var(--bg-tertiary)] transition-colors"
                          >
                            <input
                              type="checkbox"
                              checked={selectedFilings.has(filing.id)}
                              onChange={() => toggleFilingSelection(filing.id)}
                              className="w-4 h-4 cursor-pointer"
                            />
                            <span className="text-sm mono flex-1">{filing.quarter}</span>
                            <span className="text-sm text-[var(--text-secondary)]">
                              {filing.date}
                            </span>
                            <span className="text-sm text-[var(--text-tertiary)] mono">
                              {filing.holdings} holdings
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Section 4: Crawl Status */}
            <div className="col-span-1 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Crawl Status</h2>
              
              <div className="space-y-4">
                {/* Success Count */}
                <div className="bg-[var(--accent-buy)]/10 border border-[var(--accent-buy)]/30 rounded-lg p-4">
                  <div className="flex items-center gap-3 mb-2">
                    <CheckCircle2 size={20} className="text-[var(--accent-buy)]" />
                    <span className="text-sm text-[var(--text-secondary)]">Successful</span>
                  </div>
                  <div className="text-3xl font-bold mono text-[var(--accent-buy)]">1,247</div>
                </div>

                {/* Error Count */}
                <div className="bg-[var(--accent-sell)]/10 border border-[var(--accent-sell)]/30 rounded-lg p-4">
                  <div className="flex items-center gap-3 mb-2">
                    <AlertCircle size={20} className="text-[var(--accent-sell)]" />
                    <span className="text-sm text-[var(--text-secondary)]">Errors</span>
                  </div>
                  <div className="text-3xl font-bold mono text-[var(--accent-sell)]">23</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}