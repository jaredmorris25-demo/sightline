import { redirect } from 'next/navigation';
import { auth0 } from '@/lib/auth0';
import SubmitSightingForm from './SubmitSightingForm';

export default async function SubmitPage() {
  const session = await auth0.getSession();

  if (!session) {
    redirect('/auth/login');
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-10">
      <h1 className="text-2xl font-semibold text-gray-900 mb-6">Submit a sighting</h1>
      <SubmitSightingForm accessToken={session.tokenSet.accessToken} />
    </div>
  );
}
