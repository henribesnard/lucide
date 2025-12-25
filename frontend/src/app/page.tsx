
"use client";

import Image from "next/image";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { AuthManager } from "@/utils/auth";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // Vérifier l'authentification avant de rediriger
    if (typeof window !== 'undefined') {
      const isAuthenticated = AuthManager.isAuthenticated();

      if (isAuthenticated) {
        router.push("/chat");
      } else {
        router.push("/login");
      }
    }
  }, [router]);

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="w-16 h-16 rounded-2xl bg-white/90 shadow-lg shadow-slate-200/60 border border-white/70 flex items-center justify-center">
          <Image src="/statos-s.svg" alt="STATOS" width={42} height={42} priority />
        </div>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600" />
      </div>
    </div>
  );
}
