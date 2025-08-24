import DashboardLayout from '@/features/dashboard/components/DashboardLayout';
import AccountsPage from '@/features/accounts/pages/AccountsPage';

export const dynamic = 'force-dynamic';

export default function Page() {
  return (
    <DashboardLayout>
      <AccountsPage />
    </DashboardLayout>
  );
}
