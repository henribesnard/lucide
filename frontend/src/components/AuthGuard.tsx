
"use client";

import { useEffect, useState } from 'react';
import Image from "next/image";
import { useRouter } from 'next/navigation';
import { AuthManager } from '@/utils/auth';

interface AuthGuardProps {
    children: React.ReactNode;
}

export function AuthGuard({ children }: AuthGuardProps) {
    const router = useRouter();
    const [isChecking, setIsChecking] = useState(true);

    useEffect(() => {
        // Check if running on client side
        if (typeof window !== 'undefined') {
            const isAuthenticated = AuthManager.isAuthenticated();

            if (!isAuthenticated) {
                router.push('/login');
            } else {
                setIsChecking(false);
            }
        }
    }, [router]);

    if (isChecking) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-slate-50">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-16 h-16 bg-white rounded-2xl flex items-center justify-center shadow-lg shadow-teal-500/10 ring-1 ring-slate-200/60">
                        <Image src="/statos-s.svg" alt="Loading" width={32} height={32} />
                    </div>
                </div>
            </div>
        );
    }

    return <>{children}</>;
}
