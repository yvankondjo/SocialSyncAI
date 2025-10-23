"use client"

import { format, isToday, isPast, isSameDay } from 'date-fns';
import { PostCardMini } from './PostCardMini';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { ScheduledPost } from '@/types/scheduled-posts';

interface DayCellProps {
  day: Date;
  posts: ScheduledPost[];
  isCurrentMonth: boolean;
  onPostClick: (post: ScheduledPost) => void;
}

const MAX_VISIBLE_POSTS = 3;

export function DayCell({ day, posts, isCurrentMonth, onPostClick }: DayCellProps) {
  const dayNumber = format(day, 'd');
  const isCurrentDay = isToday(day);
  const isPastDay = isPast(day) && !isToday(day);
  const visiblePosts = posts.slice(0, MAX_VISIBLE_POSTS);
  const remainingCount = posts.length - MAX_VISIBLE_POSTS;

  return (
    <div
      className={cn(
        "group relative bg-card rounded-lg border border-border/50 p-2.5 min-h-[110px] flex flex-col transition-all duration-200",
        "hover:border-border hover:shadow-sm",
        !isCurrentMonth && "bg-muted/30 opacity-60",
        isPastDay && "bg-muted/20",
        isCurrentDay && "ring-1 ring-primary/30 bg-primary/5"
      )}
      role="gridcell"
      aria-label={format(day, 'EEEE, MMMM d, yyyy')}
    >
      {/* Day Number */}
      <div className="flex items-center justify-between mb-2">
        <time
          dateTime={format(day, 'yyyy-MM-dd')}
          className={cn(
            "text-sm font-semibold inline-flex items-center justify-center w-7 h-7 rounded-full transition-colors",
            isCurrentDay && "bg-primary text-primary-foreground shadow-sm",
            !isCurrentDay && isCurrentMonth && "text-foreground",
            !isCurrentDay && !isCurrentMonth && "text-muted-foreground/70"
          )}
        >
          {dayNumber}
        </time>
        {posts.length > 0 && (
          <span
            className={cn(
              "text-xs font-medium px-1.5 py-0.5 rounded-md",
              isCurrentMonth ? "text-muted-foreground bg-muted/60" : "text-muted-foreground/50"
            )}
            aria-label={`${posts.length} scheduled posts`}
          >
            {posts.length}
          </span>
        )}
      </div>

      {/* Posts */}
      <div className="flex-1 space-y-1.5 overflow-y-auto scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent">
        {visiblePosts.map((post) => (
          <PostCardMini
            key={post.id}
            post={post}
            onClick={() => onPostClick(post)}
            isPast={isPastDay}
          />
        ))}

        {/* Show "+X more" badge if there are more posts */}
        {remainingCount > 0 && (
          <Badge
            variant="secondary"
            className="w-full justify-center text-xs py-0.5 font-medium hover:bg-secondary/80 cursor-pointer transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              // Could open a dialog showing all posts for this day
            }}
          >
            +{remainingCount} more
          </Badge>
        )}
      </div>
    </div>
  );
}
