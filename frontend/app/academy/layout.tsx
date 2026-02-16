import React from 'react';
import { cn } from '@/lib/utils';

export default function AcademyLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className={cn('academy-layout', 'relative')}>
      {children}
    </div>
  );
}
