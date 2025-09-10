import DashboardLayout from '@/features/dashboard/components/DashboardLayout';
import CalendarPage from '@/features/calendar/pages/CalendarPage';

export default function Page() {
  return (
    <DashboardLayout>
      <CalendarPage />
    </DashboardLayout>
  );
}

