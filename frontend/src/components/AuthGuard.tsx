
"use client";

import { useEffect, useState } from 'react';
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
                    <div className="w-12 h-12 bg-gradient-to-br from-teal-500 to-teal-600 rounded-xl flex items-center justify-center shadow-lg shadow-teal-500/20">
                        <span className="text-white font-bold text-xl">L</span>
                    </div>
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-500" />
                </div>
            </div>
        );
    }

    return <>{children}</>;
}
