
"use client";

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
        <div className="w-16 h-16 bg-gradient-to-br from-teal-500 to-teal-600 rounded-2xl flex items-center justify-center shadow-lg shadow-teal-500/20">
          <span className="text-white font-bold text-3xl">L</span>
        </div>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-500" />
      </div>
    </div>
  );
}
