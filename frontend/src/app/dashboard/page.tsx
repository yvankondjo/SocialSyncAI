import DashboardLayout from '@/features/dashboard/components/DashboardLayout';
import DashboardPage from '@/features/dashboard/pages/DashboardPage';

export default function Page() {
  return (
    <DashboardLayout>
      <DashboardPage />
    </DashboardLayout>
  );
}
