'use client';

import { useState, useEffect } from 'react';

export function ClientTime({
  date,
  options,
}: {
  date: string | Date;
  options: Intl.DateTimeFormatOptions;
}) {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (!isMounted) {
    // Affichez un espace réservé pour éviter les décalages de mise en page et les incohérences.
    return <span style={{ display: 'inline-block', minWidth: '40px' }} />;
  }

  return <>{new Date(date).toLocaleTimeString([], options)}</>;
}
