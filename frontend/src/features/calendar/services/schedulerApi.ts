import { DateTime } from 'luxon';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export type SchedulePlatform = 'instagram' | 'reddit';

export interface CreateScheduleInput {
  platform: SchedulePlatform;
  socialAccountId: string;
  text: string;
  mediaUrl?: string;
  scheduledAtISO: string; // Europe/Paris ISO
}

export async function createScheduledPost(input: CreateScheduleInput): Promise<{ id: string; scheduled_at: string; status: string }>{
  const dt = DateTime.fromISO(input.scheduledAtISO, { zone: 'Europe/Paris' });
  if (!dt.isValid) throw new Error('Date/heure invalide');
  if (dt <= DateTime.now().setZone('Europe/Paris')) throw new Error('La date doit être dans le futur (Europe/Paris)');

  const res = await fetch(`${API_BASE_URL}/api/scheduler/posts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      platform: input.platform,
      social_account_id: input.socialAccountId,
      text: input.text,
      media_url: input.mediaUrl,
      scheduled_at: dt.toISO(),
    }),
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`Echec de la planification: ${res.status} ${res.statusText} - ${txt}`);
  }
  return res.json();
}

