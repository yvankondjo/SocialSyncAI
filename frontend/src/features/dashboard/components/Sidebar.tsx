'use client';

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import SidebarLink from './SidebarLink';
import {
  Home,
  LayoutGrid, // Changed from Calendar
  MessageSquare,
  BarChart2,
  Users,
  Settings,
  Flame,
  AtSign,
  ChevronDown,
  Calendar, // Keep for sub-item icon
} from 'lucide-react';

const Sidebar = ({ className }: { className?: string }) => {
  const [isPostsOpen, setPostsOpen] = useState(true); // Changed from isPlannerOpen

  const navigation = [
    { name: 'Home', href: '/dashboard', icon: <Home size={20} /> },
    {
      name: 'Posts', // Parent is now Posts
      icon: <LayoutGrid size={20} />,
      sublinks: [{ name: 'Planner', href: '/dashboard/planner' }], // Child is Planner
    },
    { name: 'Social Accounts', href: '/dashboard/accounts', icon: <AtSign size={20} /> },
    { name: 'Inbox', href: '/dashboard/inbox', icon: <MessageSquare size={20} /> },
    { name: 'Analytics', href: '/dashboard/analytics', icon: <BarChart2 size={20} /> },
    { name: 'CRM', href: '/dashboard/crm', icon: <Users size={20} /> },
    { name: 'Ads', href: '/dashboard/ads', icon: <Flame size={20} /> },
    { name: 'Settings', href: '/dashboard/settings', icon: <Settings size={20} /> },
  ];

  return (
    <aside
      className={cn(
        'w-64 h-full flex flex-col py-6 px-4 transition-all duration-300 glass-panel',
        className
      )}
    >
      <div className="flex items-center px-4 mb-8">
        <h1 className="font-bold text-2xl gradient-text">SocialSync</h1>
      </div>

      <nav className="flex-1">
        <ul className="space-y-1">
          {navigation.map((item) => (
            <li key={item.name}>
              {item.sublinks ? (
                <div>
                  <button
                    onClick={() => setPostsOpen(!isPostsOpen)} // Changed to setPostsOpen
                    className="w-full flex items-center px-4 py-3 rounded-xl font-medium text-gray-600 hover:bg-gray-100"
                  >
                    <div className="w-6 mr-3 flex items-center justify-center">{item.icon}</div>
                    <span>{item.name}</span>
                    <ChevronDown
                      className={cn('ml-auto transition-transform', {
                        'rotate-180': !isPostsOpen, // Changed to isPostsOpen
                      })}
                      size={16}
                    />
                  </button>
                  {isPostsOpen && ( // Changed to isPostsOpen
                    <ul className="ml-8 mt-1 space-y-1">
                      {item.sublinks.map((sublink) => (
                        <li key={sublink.name}>
                          {/* We can pass the calendar icon to the sublink now */}
                          <SidebarLink href={sublink.href} label={sublink.name} icon={<Calendar size={16}/>} isSublink />
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              ) : (
                <SidebarLink href={item.href!} label={item.name} icon={item.icon} />
              )}
            </li>
          ))}
        </ul>
      </nav>

      <div className="px-4">
        <button className="w-full flex items-center justify-center py-2 bg-gray-100 rounded-xl text-gray-600 hover:bg-gray-200">
          <span>Compact Mode</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;