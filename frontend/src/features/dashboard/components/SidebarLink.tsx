'use client';

import Link from 'next/link';
import React from 'react';
import { cn } from '@/lib/utils';
import { usePathname } from 'next/navigation';

interface SidebarLinkProps {
  href: string;
  label: string;
  icon: React.ReactNode;
  isSublink?: boolean;
}

const SidebarLink = ({ href, label, icon, isSublink = false }: SidebarLinkProps) => {
  const pathname = usePathname();
  const isActive = pathname === href;

  return (
    <Link
      href={href}
      className={cn(
        'flex items-center px-4 py-3 rounded-xl font-medium text-gray-600 hover:bg-gray-100',
        {
          'bg-gradient-to-r from-indigo-500/10 to-violet-500/10 text-violet-700': isActive,
          'text-sm py-2': isSublink,
        }
      )}
    >
      <div className="w-6 mr-3 flex items-center justify-center">
        {icon}
      </div>
      <span>{label}</span>
    </Link>
  );
};

export default SidebarLink;