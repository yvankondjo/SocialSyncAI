import AccountsPage from '@/features/accounts/pages/AccountsPage';
import DashboardLayout from '@/features/dashboard/components/DashboardLayout';

export default function Page() {
  return (
    <DashboardLayout>
      <AccountsPage />
    </DashboardLayout>
  );
}
