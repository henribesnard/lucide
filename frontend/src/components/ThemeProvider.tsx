"use client";

import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

export type ThemePreference = "light" | "dark" | "auto";
type ResolvedTheme = "light" | "dark";

type ThemeContextValue = {
  preference: ThemePreference;
  resolvedTheme: ResolvedTheme;
  setPreference: (preference: ThemePreference) => void;
};

const ThemeContext = createContext<ThemeContextValue | null>(null);

const STORAGE_KEY = "statos-theme-preference";

const isPreference = (value: string | null): value is ThemePreference =>
  value === "light" || value === "dark" || value === "auto";

const getSystemTheme = (): ResolvedTheme => {
  if (typeof window === "undefined" || !window.matchMedia) {
    return "light";
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
};

const applyTheme = (preference: ThemePreference): ResolvedTheme => {
  const resolved = preference === "auto" ? getSystemTheme() : preference;
  const root = document.documentElement;
  root.dataset.theme = resolved;
  root.dataset.themePreference = preference;
  root.style.colorScheme = resolved;
  return resolved;
};

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [preference, setPreferenceState] = useState<ThemePreference>("auto");
  const [resolvedTheme, setResolvedTheme] = useState<ResolvedTheme>("light");

  useEffect(() => {
    if (typeof window === "undefined") return;
    const storedValue = localStorage.getItem(STORAGE_KEY);
    const storedPreference = isPreference(storedValue) ? storedValue : "auto";
    setPreferenceState(storedPreference);
    setResolvedTheme(applyTheme(storedPreference));
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (preference !== "auto") return;

    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const handleChange = () => setResolvedTheme(applyTheme("auto"));

    if (media.addEventListener) {
      media.addEventListener("change", handleChange);
      return () => media.removeEventListener("change", handleChange);
    }
    media.addListener(handleChange);
    return () => media.removeListener(handleChange);
  }, [preference]);

  const setPreference = useCallback((next: ThemePreference) => {
    setPreferenceState(next);
    if (typeof window !== "undefined") {
      localStorage.setItem(STORAGE_KEY, next);
      setResolvedTheme(applyTheme(next));
    }
  }, []);

  const value = useMemo(
    () => ({ preference, resolvedTheme, setPreference }),
    [preference, resolvedTheme, setPreference]
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within ThemeProvider");
  }
  return context;
}
