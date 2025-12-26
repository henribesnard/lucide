"use client";

import { useState } from 'react';
import { AuthGuard } from '@/components/AuthGuard';
import { useLanguage } from '@/contexts/LanguageContext';
import { useTranslation } from '@/i18n/translations';
import MainSidebar from '@/components/MainSidebar';

export default function SettingsPage() {
  const { language, setLanguage } = useLanguage();
  const { t } = useTranslation(language);

  const [selectedTheme, setSelectedTheme] = useState<'light' | 'dark' | 'auto'>('auto');

  const handleLanguageChange = (newLanguage: 'fr' | 'en') => {
    setLanguage(newLanguage);
  };

  const handleThemeChange = (theme: 'light' | 'dark' | 'auto') => {
    setSelectedTheme(theme);
    // Theme logic will be handled by ThemeProvider
    localStorage.setItem('statos-theme-preference', theme);
    window.location.reload(); // Reload to apply theme
  };

  return (
    <AuthGuard>
      <div className="flex h-screen">
        {/* Sidebar */}
        <MainSidebar activeConversationId={null} />

        {/* Main Content */}
        <div className="flex-1 flex flex-col bg-gray-50 dark:bg-gray-900">
          {/* Header */}
          <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-8 py-6">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              {t('settings')}
            </h1>
          </div>

          {/* Settings Content */}
          <div className="flex-1 overflow-y-auto px-8 py-6">
            <div className="max-w-2xl space-y-8">
              {/* Language Section */}
              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  {t('languageSettings')}
                </h2>
                <div className="space-y-3">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    {t('selectLanguage')}
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      onClick={() => handleLanguageChange('fr')}
                      className={`flex items-center gap-3 px-4 py-3 rounded-lg border-2 transition-all ${
                        language === 'fr'
                          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                      }`}
                    >
                      <span className="text-3xl">🇫🇷</span>
                      <div className="text-left">
                        <div className="font-medium text-gray-900 dark:text-white">
                          {t('french')}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          Français
                        </div>
                      </div>
                      {language === 'fr' && (
                        <svg
                          className="w-5 h-5 ml-auto text-blue-500"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                            clipRule="evenodd"
                          />
                        </svg>
                      )}
                    </button>

                    <button
                      onClick={() => handleLanguageChange('en')}
                      className={`flex items-center gap-3 px-4 py-3 rounded-lg border-2 transition-all ${
                        language === 'en'
                          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                      }`}
                    >
                      <span className="text-3xl">🇬🇧</span>
                      <div className="text-left">
                        <div className="font-medium text-gray-900 dark:text-white">
                          {t('english')}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          English
                        </div>
                      </div>
                      {language === 'en' && (
                        <svg
                          className="w-5 h-5 ml-auto text-blue-500"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                            clipRule="evenodd"
                          />
                        </svg>
                      )}
                    </button>
                  </div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {language === 'fr'
                      ? 'Change la langue de l\'interface. Les réponses du chatbot s\'adapteront automatiquement.'
                      : 'Changes the interface language. Chatbot responses will adapt automatically.'}
                  </p>
                </div>
              </div>

              {/* Theme Section */}
              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Theme
                </h2>
                <div className="space-y-3">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    {language === 'fr' ? 'Sélectionner le thème' : 'Select theme'}
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    {(['light', 'dark', 'auto'] as const).map((theme) => (
                      <button
                        key={theme}
                        onClick={() => handleThemeChange(theme)}
                        className={`px-4 py-3 rounded-lg border-2 transition-all ${
                          selectedTheme === theme
                            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                            : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                        }`}
                      >
                        <div className="font-medium text-gray-900 dark:text-white capitalize">
                          {theme === 'light' && (language === 'fr' ? 'Clair' : 'Light')}
                          {theme === 'dark' && (language === 'fr' ? 'Sombre' : 'Dark')}
                          {theme === 'auto' && 'Auto'}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AuthGuard>
  );
}
