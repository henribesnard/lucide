"use client";

import Image from "next/image";

export default function Loading() {
    return (
        <div className="min-h-screen bg-slate-50 flex items-center justify-center">
            <div className="flex flex-col items-center gap-4">
                <div className="w-24 h-24 rounded-3xl bg-white/90 shadow-lg shadow-teal-500/10 ring-1 ring-slate-200/60 flex items-center justify-center">
                    <Image src="/statos-s.svg" alt="STATOS" width={64} height={64} priority />
                </div>
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600" />
            </div>
        </div>
    );
}
