import React from 'react';
import { cn } from '@/lib/utils';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Search, Bell, Bot } from 'lucide-react';

const Header = ({ className }: { className?: string }) => {
  return (
    <header
      className={cn(
        'glass-panel backdrop-blur-md py-4 px-6 flex items-center justify-between border-b border-gray-200/50',
        className
      )}
    >
      <div className="relative w-full max-w-md">
        <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
          <Search className="text-gray-400" size={16} />
        </div>
        <Input
          type="text"
          className="w-full pl-10 pr-4 py-2 rounded-xl bg-white/40 border border-gray-200/50 text-gray-700 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500/30 focus:border-violet-500/50"
          placeholder="Search anything..."
        />
      </div>

      <div className="flex items-center space-x-4">
        <Button
          variant="ghost"
          size="icon"
          className="w-9 h-9 flex items-center justify-center rounded-full bg-white/80 text-gray-600 hover:bg-white transition-all"
        >
          <Bell size={20} />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="w-9 h-9 flex items-center justify-center rounded-full bg-white/80 text-gray-600 hover:bg-white transition-all"
        >
          <Bot size={20} />
        </Button>
        <div className="relative">
          <button className="flex items-center">
            <Avatar className="w-9 h-9">
              <AvatarImage src="/avatar.jpg" alt="Alex D." />
              <AvatarFallback className="gradient-bg text-white font-medium">AD</AvatarFallback>
            </Avatar>
            <span className="ml-2 text-gray-700 font-medium">Alex D.</span>
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;