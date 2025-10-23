"use client"

import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight, Calendar as CalendarIcon } from 'lucide-react';
import { format, addMonths, subMonths, isThisMonth } from 'date-fns';

interface CalendarHeaderProps {
  currentDate: Date;
  onDateChange: (date: Date) => void;
}

export function CalendarHeader({ currentDate, onDateChange }: CalendarHeaderProps) {
  const handlePrevMonth = () => {
    onDateChange(subMonths(currentDate, 1));
  };

  const handleNextMonth = () => {
    onDateChange(addMonths(currentDate, 1));
  };

  const handleToday = () => {
    onDateChange(new Date());
  };

  const isCurrentMonth = isThisMonth(currentDate);

  return (
    <header className="border-b border-border/60 bg-background px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <CalendarIcon className="h-5 w-5 text-muted-foreground" aria-hidden="true" />
            <h1 className="text-2xl font-semibold tracking-tight text-foreground">
              {format(currentDate, 'MMMM yyyy')}
            </h1>
          </div>
          <Button
            variant={isCurrentMonth ? "secondary" : "outline"}
            size="sm"
            onClick={handleToday}
            className="h-9 px-3 text-sm font-medium transition-colors"
          >
            Today
          </Button>
        </div>

        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={handlePrevMonth}
            className="h-9 w-9 p-0 hover:bg-muted transition-colors"
          >
            <ChevronLeft className="h-4 w-4" />
            <span className="sr-only">Previous month</span>
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleNextMonth}
            className="h-9 w-9 p-0 hover:bg-muted transition-colors"
          >
            <ChevronRight className="h-4 w-4" />
            <span className="sr-only">Next month</span>
          </Button>
        </div>
      </div>
    </header>
  );
}
