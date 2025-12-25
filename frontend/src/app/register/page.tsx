"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { AuthManager } from "@/utils/auth";

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);
    try {
      await AuthManager.register(email, password, fullName);
      setSuccess("Compte cree. Verifiez votre email.");
      router.push("/login");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-10">
      <div className="relative w-full max-w-md">
        <div className="absolute -top-24 -right-16 h-40 w-40 rounded-full bg-teal-200/40 blur-3xl" />
        <div className="absolute -bottom-24 -left-16 h-40 w-40 rounded-full bg-amber-200/40 blur-3xl" />

        <div className="relative rounded-2xl border border-white/70 bg-white/90 p-8 shadow-2xl backdrop-blur">
          <div className="text-center mb-8">
            <div className="mx-auto mb-4 flex h-24 w-24 items-center justify-center rounded-3xl bg-white shadow-md ring-1 ring-slate-200/60">
              <Image src="/statos-s.svg" alt="STATOS" width={64} height={64} priority />
            </div>
            <h1 className="mt-3 text-2xl font-semibold text-slate-900">Creer un compte</h1>
            <p className="mt-2 text-sm text-slate-500">
              Demarrez avec STATOS pour vos analyses.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {error}
              </div>
            )}
            {success && (
              <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
                {success}
              </div>
            )}

            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">
                Nom complet
              </label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
                autoComplete="name"
                className="input-field"
                placeholder="Prenom Nom"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
                className="input-field"
                placeholder="vous@email.com"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">
                Mot de passe
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="new-password"
                className="input-field"
                placeholder="********"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full flex items-center justify-center"
            >
              {loading ? "Creation..." : "Creer mon compte"}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-slate-500">
            Deja un compte ?{" "}
            <Link
              href="/login"
              className="font-semibold text-teal-700 hover:text-teal-800"
            >
              Se connecter
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
