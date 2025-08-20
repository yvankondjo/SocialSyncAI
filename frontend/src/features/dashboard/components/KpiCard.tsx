import React from 'react';
import { cn } from '@/lib/utils';
import { Sparkles, MessageSquare, DollarSign, Heart } from 'lucide-react';

interface KpiCardProps {
  title: string;
  value: string;
  change: string;
  changeType: 'positive' | 'negative' | 'neutral';
  iconType: 'magic' | 'dm' | 'roi' | 'engagement';
}

const icons = {
  magic: <Sparkles className="w-5 h-5 text-white" />,
  dm: <MessageSquare className="w-5 h-5 text-blue-500" />,
  roi: <DollarSign className="w-5 h-5 text-green-500" />,
  engagement: <Heart className="w-5 h-5 text-pink-500" />,
};

const iconBackgrounds = {
  magic: 'gradient-bg',
  dm: 'bg-blue-100',
  roi: 'bg-green-100',
  engagement: 'bg-pink-100',
};

const KpiCard = ({ title, value, change, changeType, iconType }: KpiCardProps) => {
  return (
    <div className="glass-panel rounded-2xl p-5 card-hover bg-white/80 backdrop-blur-md">
      <div className="flex justify-between">
        <div>
          <div className={cn("w-12 h-12 rounded-xl flex items-center justify-center mb-4", iconBackgrounds[iconType])}>
            {icons[iconType]}
          </div>
          <h3 className="text-gray-500 text-sm font-medium uppercase tracking-wider">{title}</h3>
          <div className="mt-1 flex items-baseline">
            <p className="text-3xl font-bold text-gray-800">{value}</p>
            <span className={cn("ml-2 text-sm font-medium", {
              'text-green-500': changeType === 'positive',
              'text-red-500': changeType === 'negative',
              'text-gray-500': changeType === 'neutral',
            })}>
              {change}
            </span>
          </div>
        </div>
        <div className="w-20 h-10 relative">
          <svg viewBox="0 0 100 40" className="w-full h-full">
            <polyline
              points={
                iconType === 'magic' ? "0,35 25,20 50,30 75,10 100,15" :
                iconType === 'dm' ? "0,25 25,35 50,20 75,25 100,10" :
                iconType === 'roi' ? "0,15 25,10 50,20 75,25 100,35" :
                "0,20 25,15 50,35 75,10 100,25"
              }
              className="fill-none stroke-current text-indigo-500"
              strokeWidth="2"
            />
          </svg>
        </div>
      </div>
    </div>
  );
};

export default KpiCard;