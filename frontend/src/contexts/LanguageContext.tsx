"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export type Language = 'fr' | 'en';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  isLoading: boolean;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

interface LanguageProviderProps {
  children: ReactNode;
}

export const LanguageProvider: React.FC<LanguageProviderProps> = ({ children }) => {
  const [language, setLanguageState] = useState<Language>('fr');
  const [isLoading, setIsLoading] = useState(true);

  // Load language from user preferences on mount
  useEffect(() => {
    const loadUserLanguage = async () => {
      try {
        const token = localStorage.getItem('token');
        if (token) {
          const response = await fetch('http://localhost:8001/auth/me', {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          });

          if (response.ok) {
            const userData = await response.json();
            const userLang = userData.preferred_language || 'fr';
            setLanguageState(userLang as Language);
            localStorage.setItem('language', userLang);
          } else {
            // Use localStorage as fallback
            const savedLang = localStorage.getItem('language') as Language;
            if (savedLang) {
              setLanguageState(savedLang);
            }
          }
        } else {
          // No token, use localStorage or default
          const savedLang = localStorage.getItem('language') as Language;
          if (savedLang) {
            setLanguageState(savedLang);
          }
        }
      } catch (error) {
        console.error('Failed to load language:', error);
        // Use localStorage as fallback
        const savedLang = localStorage.getItem('language') as Language;
        if (savedLang) {
          setLanguageState(savedLang);
        }
      } finally {
        setIsLoading(false);
      }
    };

    loadUserLanguage();
  }, []);

  const setLanguage = async (lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem('language', lang);

    // Update user preference in backend if authenticated
    try {
      const token = localStorage.getItem('token');
      if (token) {
        await fetch(`http://localhost:8001/auth/me/language?language=${lang}`, {
          method: 'PATCH',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
      }
    } catch (error) {
      console.error('Failed to update language preference:', error);
    }
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, isLoading }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = (): LanguageContextType => {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};
