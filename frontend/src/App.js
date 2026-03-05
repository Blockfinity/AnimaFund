import React, { useState, useEffect, useCallback } from 'react';
import { Toaster } from 'sonner';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Overview from './pages/Overview';
import AgentNetwork from './pages/AgentNetwork';
import DealFlow from './pages/DealFlow';
import Portfolio from './pages/Portfolio';
import Financials from './pages/Financials';
import Activity from './pages/Activity';
import Configuration from './pages/Configuration';

const API = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [currentPage, setCurrentPage] = useState('overview');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchOverview = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/fund/overview`);
      const data = await res.json();
      setOverview(data);
    } catch (e) {
      console.error('Failed to fetch overview:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchOverview();
    const interval = setInterval(fetchOverview, 30000);
    return () => clearInterval(interval);
  }, [fetchOverview]);

  const renderPage = () => {
    switch (currentPage) {
      case 'overview': return <Overview overview={overview} loading={loading} />;
      case 'agents': return <AgentNetwork />;
      case 'deals': return <DealFlow />;
      case 'portfolio': return <Portfolio />;
      case 'financials': return <Financials />;
      case 'activity': return <Activity />;
      case 'config': return <Configuration />;
      default: return <Overview overview={overview} loading={loading} />;
    }
  };

  return (
    <div className="flex h-screen bg-[#fafafa]" data-testid="app-container">
      <Toaster position="top-right" richColors />
      <Sidebar 
        currentPage={currentPage} 
        setCurrentPage={setCurrentPage} 
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
      />
      <div className={`flex-1 flex flex-col overflow-hidden transition-all duration-200 ${sidebarOpen ? 'ml-60' : 'ml-16'}`}>
        <Header 
          overview={overview}
          currentPage={currentPage}
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        />
        <main className="flex-1 overflow-y-auto p-6">
          {renderPage()}
        </main>
      </div>
    </div>
  );
}

export default App;
