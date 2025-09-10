'use client';

import React, { useMemo, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import Image from 'next/image';
import { DateTime } from 'luxon';
import { createScheduledPost, SchedulePlatform } from '../services/schedulerApi';
import { SocialAccountsApi } from '@/features/accounts/services/socialAccountsApi';
import { SocialAccount } from '@/features/accounts/types/socialAccount';
import { useRouter, useSearchParams } from 'next/navigation';

type Preview = {
  platform: SchedulePlatform;
  text: string;
  mediaUrl?: string;
};

export default function CalendarPage() {
  const [platform, setPlatform] = useState<SchedulePlatform>('instagram');
  const [text, setText] = useState<string>('');
  const [mediaUrl, setMediaUrl] = useState<string>('');
  const [scheduledAt, setScheduledAt] = useState<string>('');
  const [accounts, setAccounts] = useState<SocialAccount[]>([]);
  const [accountId, setAccountId] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');
  const router = useRouter();
  const params = useSearchParams();

  React.useEffect(() => {
    SocialAccountsApi.getSocialAccounts().then(setAccounts).catch(() => {});
  }, []);

  React.useEffect(() => {
    if (params.get('addChannel') === '1') {
      router.push('/dashboard/accounts?openModal=1');
    }
  }, [params, router]);

  const preview: Preview = useMemo(() => ({ platform, text, mediaUrl }), [platform, text, mediaUrl]);

  const onSubmit = async () => {
    setError('');
    setSuccess('');
    try {
      const iso = DateTime.fromISO(scheduledAt, { zone: 'Europe/Paris' }).toISO();
      if (!iso) throw new Error('Date/heure invalide');
      if (!accountId) throw new Error('Choisissez un compte social');
      const res = await createScheduledPost({
        platform,
        socialAccountId: accountId,
        text,
        mediaUrl: mediaUrl || undefined,
        scheduledAtISO: iso,
      });
      setSuccess('Post planifié');
    } catch (e: any) {
      setError(e.message || 'Erreur');
    }
  };

  return (
    <main className="flex-1 overflow-y-auto p-6">
      <div className="max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          <h1 className="text-2xl font-bold">Planifier un post</h1>

          <div className="space-y-2">
            <label className="text-sm font-medium">Réseau</label>
            <div className="flex gap-2">
              {(['instagram', 'reddit'] as SchedulePlatform[]).map((p) => (
                <Button key={p} variant={p === platform ? 'default' : 'outline'} onClick={() => setPlatform(p)} className="capitalize">
                  <Image src={`/logos/${p}.svg`} alt={p} width={16} height={16} className="mr-2" />
                  {p}
                </Button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Compte</label>
            <select className="w-full border rounded px-3 py-2" value={accountId} onChange={(e) => setAccountId(e.target.value)}>
              <option value="">Sélectionner…</option>
              {accounts
                .filter((a) => ['instagram', 'reddit'].includes(a.platform))
                .map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.platform} • {a.username}
                  </option>
                ))}
            </select>
            <div className="text-xs text-gray-500">Pas de compte ? <button className="underline" onClick={() => router.push('/dashboard/calendar?addChannel=1')}>Add Channel</button></div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Texte</label>
            <textarea className="w-full border rounded px-3 py-2 h-32" value={text} onChange={(e) => setText(e.target.value)} />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Média (URL optionnelle)</label>
            <Input value={mediaUrl} onChange={(e) => setMediaUrl(e.target.value)} placeholder="https://..." />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Date & heure (Europe/Paris)</label>
            <Input type="datetime-local" value={scheduledAt} onChange={(e) => setScheduledAt(e.target.value)} />
          </div>

          {error && <div className="text-red-600 text-sm">{error}</div>}
          {success && <div className="text-green-600 text-sm">{success}</div>}

          <div className="flex gap-2">
            <Button onClick={onSubmit}>Planifier</Button>
            <Button variant="outline" onClick={() => router.push('/dashboard/accounts?openModal=1')}>Add Channel</Button>
          </div>
        </div>

        <div className="border rounded p-4">
          <h2 className="font-semibold mb-3">Preview</h2>
          <div className="flex items-center gap-2 mb-3">
            <Image src={`/logos/${preview.platform}.svg`} alt={preview.platform} width={20} height={20} />
            <span className="capitalize">{preview.platform}</span>
          </div>
          <div className="whitespace-pre-wrap text-sm text-gray-800 mb-3">{preview.text || 'Votre texte apparaîtra ici…'}</div>
          {preview.mediaUrl ? (
            // mock image
            // eslint-disable-next-line @next/next/no-img-element
            <img src={preview.mediaUrl} alt="media" className="w-full rounded border" />
          ) : (
            <div className="w-full h-40 bg-gray-50 border rounded flex items-center justify-center text-gray-400 text-sm">Média (optionnel)</div>
          )}
        </div>
      </div>
    </main>
  );
}

