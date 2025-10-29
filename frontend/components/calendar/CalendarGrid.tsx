"use client"

import { DayCell } from './DayCell';
import { startOfMonth, endOfMonth, startOfWeek, endOfWeek, eachDayOfInterval, format, isSameMonth } from 'date-fns';
import type { ScheduledPost } from '@/types/scheduled-posts';

interface CalendarGridProps {
  currentDate: Date;
  posts: ScheduledPost[];
  onPostClick: (post: ScheduledPost) => void;
}

const WEEKDAYS = [
  { short: 'Sun', full: 'Sunday' },
  { short: 'Mon', full: 'Monday' },
  { short: 'Tue', full: 'Tuesday' },
  { short: 'Wed', full: 'Wednesday' },
  { short: 'Thu', full: 'Thursday' },
  { short: 'Fri', full: 'Friday' },
  { short: 'Sat', full: 'Saturday' },
];

export function CalendarGrid({ currentDate, posts, onPostClick }: CalendarGridProps) {
  const monthStart = startOfMonth(currentDate);
  const monthEnd = endOfMonth(currentDate);
  const calendarStart = startOfWeek(monthStart);
  const calendarEnd = endOfWeek(monthEnd);

  const days = eachDayOfInterval({ start: calendarStart, end: calendarEnd });

  // Group posts by day
  // Ensure posts is always an array, even if API fails or returns unexpected data
  const postsArray = Array.isArray(posts) ? posts : [];
  const postsByDay = postsArray.reduce((acc, post) => {
    const dayKey = format(new Date(post.publish_at), 'yyyy-MM-dd');
    if (!acc[dayKey]) acc[dayKey] = [];
    acc[dayKey].push(post);
    return acc;
  }, {} as Record<string, ScheduledPost[]>);

  return (
    <div className="flex-1 flex flex-col overflow-auto bg-background/95 p-4 sm:p-6">
      <div className="flex-1 flex flex-col min-h-0">
        {/* Weekday Headers */}
        <div className="grid grid-cols-7 gap-px mb-3 pb-2 border-b border-border/60">
          {WEEKDAYS.map((day) => (
            <div
              key={day.short}
              className="text-center py-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground/80"
              aria-label={day.full}
            >
              {day.short}
            </div>
          ))}
        </div>

        {/* Calendar Grid */}
        <div className="grid grid-cols-7 gap-1 flex-1 auto-rows-fr">
          {days.map((day) => {
            const dayKey = format(day, 'yyyy-MM-dd');
            const dayPosts = postsByDay[dayKey] || [];
            const isCurrentMonth = isSameMonth(day, currentDate);

            return (
              <DayCell
                key={dayKey}
                day={day}
                posts={dayPosts}
                isCurrentMonth={isCurrentMonth}
                onPostClick={onPostClick}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
}
