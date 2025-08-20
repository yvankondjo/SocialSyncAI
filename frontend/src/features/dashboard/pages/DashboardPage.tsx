import React from 'react';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';
import KpiCard from '../components/KpiCard';

const DashboardPage = () => {
  return (
    <main className="flex-1 overflow-y-auto p-6">
      {/* Welcome Panel */}
      <div className="glass-panel rounded-2xl p-6 mb-8 bg-gradient-to-r from-indigo-500/10 to-violet-500/10 border border-white backdrop-blur-sm">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Welcome back, Alex 👋</h1>
            <p className="text-gray-600 mt-1">Last login: Today, 08:15 AM</p>
          </div>
          <Button className="mt-4 md:mt-0 gradient-bg text-white font-medium py-2 px-6 rounded-xl hover:opacity-90 transition-all flex items-center">
            <Plus className="mr-2" size={16} />
            Create New Post
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <KpiCard
          title="Posts Automated"
          value="32"
          change="+18% WoW"
          changeType="positive"
          iconType="magic"
        />
        <KpiCard
          title="DMs Resolved"
          value="147"
          change="70% AI"
          changeType="positive"
          iconType="dm"
        />
        <KpiCard
          title="ROI Tracked"
          value="€1,240"
          change="↑12%"
          changeType="positive"
          iconType="roi"
        />
        <KpiCard
          title="Engagement Rate"
          value="7.8%"
          change="across all"
          changeType="neutral"
          iconType="engagement"
        />
      </div>

      {/* Rest of the dashboard content will go here */}
    </main>
  );
};

export default DashboardPage;