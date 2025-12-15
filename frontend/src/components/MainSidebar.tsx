"use client";

import { useState } from "react";
import {
  HomeIcon,
  ClockIcon,
  BookmarkIcon,
  Cog6ToothIcon,
  PlusIcon,
  ChevronRightIcon,
  Bars3Icon,
  XMarkIcon,
} from "@heroicons/react/24/outline";

interface Conversation {
  id: string;
  title: string;
  date: string;
  preview: string;
}

export default function MainSidebar() {
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [conversations] = useState<Conversation[]>([
    {
      id: "1",
      title: "PSG vs OM - Analyse",
      date: "Aujourd'hui",
      preview: "Pronostic 1X2 pour le classique",
    },
    {
      id: "2",
      title: "Real Madrid - Buteurs",
      date: "Hier",
      preview: "Qui va marquer ce soir?",
    },
    {
      id: "3",
      title: "Premier League - Form",
      date: "Il y a 2 jours",
      preview: "Analyse de forme des équipes",
    },
  ]);

  const menuItems = [
    {
      id: "home",
      icon: HomeIcon,
      label: "Accueil",
      hasSubmenu: false,
    },
    {
      id: "history",
      icon: ClockIcon,
      label: "Historique",
      hasSubmenu: true,
      count: conversations.length,
    },
    {
      id: "saved",
      icon: BookmarkIcon,
      label: "Favoris",
      hasSubmenu: true,
      count: 0,
    },
    {
      id: "settings",
      icon: Cog6ToothIcon,
      label: "Paramètres",
      hasSubmenu: false,
    },
  ];

  return (
    <>
      {/* Hamburger Button - Mobile Only */}
      <button
        onClick={() => setIsMobileMenuOpen(true)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-white rounded-lg shadow-md hover:bg-gray-50 transition-colors"
        aria-label="Menu"
      >
        <Bars3Icon className="w-6 h-6 text-gray-700" />
      </button>

      {/* Mobile Drawer */}
      <div
        className={`lg:hidden fixed inset-y-0 left-0 w-64 bg-white shadow-2xl z-50 transform transition-transform duration-300 ease-in-out ${
          isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Mobile Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-teal-500 to-teal-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-xl">L</span>
            </div>
            <span className="font-semibold text-lg text-gray-900">Lucide</span>
          </div>
          <button
            onClick={() => setIsMobileMenuOpen(false)}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Fermer le menu"
          >
            <XMarkIcon className="w-6 h-6 text-gray-700" />
          </button>
        </div>

        {/* Mobile Menu Content */}
        <div className="p-4 space-y-2">
          {/* New Chat Button */}
          <button
            className="w-full p-3 bg-teal-500 hover:bg-teal-600 text-white rounded-lg flex items-center justify-center gap-2 transition-colors font-medium"
            onClick={() => {
              window.location.reload();
              setIsMobileMenuOpen(false);
            }}
          >
            <PlusIcon className="w-5 h-5" />
            Nouvelle conversation
          </button>

          {/* Menu Items */}
          <div className="space-y-1 mt-4">
            {menuItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeSection === item.id;

              return (
                <button
                  key={item.id}
                  onClick={() => setActiveSection(isActive ? null : item.id)}
                  className={`w-full p-3 rounded-lg flex items-center gap-3 transition-all ${
                    isActive
                      ? "bg-teal-50 text-teal-600"
                      : "text-gray-700 hover:bg-gray-100"
                  }`}
                >
                  <Icon className="w-5 h-5 flex-shrink-0" />
                  <span className="font-medium">{item.label}</span>
                  {item.count !== undefined && item.count > 0 && (
                    <span className="ml-auto px-2 py-0.5 bg-teal-500 text-white text-xs rounded-full">
                      {item.count}
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {/* Active Section Content */}
          {activeSection === "history" && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <h3 className="text-xs font-semibold text-gray-500 uppercase px-3 py-2">
                Aujourd'hui
              </h3>
              {conversations
                .filter((c) => c.date === "Aujourd'hui")
                .map((conv) => (
                  <button
                    key={conv.id}
                    className="w-full text-left p-3 hover:bg-gray-50 rounded-lg transition-colors"
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    <div className="font-medium text-sm text-gray-900">
                      {conv.title}
                    </div>
                    <div className="text-xs text-gray-500 mt-1 line-clamp-1">
                      {conv.preview}
                    </div>
                  </button>
                ))}
            </div>
          )}
        </div>

        {/* Mobile Footer - User */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200 bg-white">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-500 rounded-full flex items-center justify-center">
              <span className="text-white font-semibold text-sm">H</span>
            </div>
            <div>
              <div className="font-medium text-sm text-gray-900">Henri</div>
              <div className="text-xs text-gray-500">henri@example.com</div>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Backdrop */}
      {isMobileMenuOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-40 backdrop-blur-sm"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Main Sidebar - Desktop */}
      <div className="hidden lg:flex fixed left-0 top-0 h-screen w-16 bg-white border-r border-gray-200 flex-col items-center py-4 z-50">
        {/* Logo */}
        <div className="mb-8">
          <div className="w-10 h-10 bg-gradient-to-br from-teal-500 to-teal-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-xl">L</span>
          </div>
        </div>

        {/* New Chat Button */}
        <button
          className="w-10 h-10 bg-gray-100 hover:bg-gray-200 rounded-lg flex items-center justify-center mb-6 transition-colors"
          onClick={() => window.location.reload()}
        >
          <PlusIcon className="w-5 h-5 text-gray-700" />
        </button>

        {/* Menu Items */}
        <div className="flex-1 flex flex-col gap-2 w-full px-2">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeSection === item.id;

            return (
              <button
                key={item.id}
                onClick={() =>
                  setActiveSection(isActive ? null : item.id)
                }
                className={`relative w-12 h-12 rounded-lg flex items-center justify-center transition-all ${
                  isActive
                    ? "bg-teal-50 text-teal-600"
                    : "text-gray-600 hover:bg-gray-100"
                }`}
                title={item.label}
              >
                <Icon className="w-6 h-6" />
                {item.count !== undefined && item.count > 0 && (
                  <span className="absolute top-1 right-1 w-4 h-4 bg-teal-500 text-white text-xs rounded-full flex items-center justify-center">
                    {item.count}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* User Avatar */}
        <div className="mt-auto">
          <div className="w-10 h-10 bg-purple-500 rounded-full flex items-center justify-center">
            <span className="text-white font-semibold text-sm">H</span>
          </div>
        </div>
      </div>

      {/* Secondary Sidebar (Submenu) */}
      {activeSection && (
        <div className="fixed left-16 top-0 h-screen w-72 bg-white border-r border-gray-200 z-40 overflow-hidden">
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-lg text-gray-900">
                {menuItems.find((item) => item.id === activeSection)?.label}
              </h2>
              <button
                onClick={() => setActiveSection(null)}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <ChevronRightIcon className="w-5 h-5 text-gray-500 rotate-180" />
              </button>
            </div>
          </div>

          <div className="overflow-y-auto h-[calc(100vh-73px)]">
            {activeSection === "history" && (
              <div className="p-2">
                {/* Groupes par date */}
                <div className="mb-4">
                  <h3 className="text-xs font-semibold text-gray-500 uppercase px-3 py-2">
                    Aujourd'hui
                  </h3>
                  {conversations
                    .filter((c) => c.date === "Aujourd'hui")
                    .map((conv) => (
                      <button
                        key={conv.id}
                        className="w-full text-left p-3 hover:bg-gray-50 rounded-lg transition-colors group"
                      >
                        <div className="font-medium text-sm text-gray-900 group-hover:text-teal-600">
                          {conv.title}
                        </div>
                        <div className="text-xs text-gray-500 mt-1 line-clamp-1">
                          {conv.preview}
                        </div>
                      </button>
                    ))}
                </div>

                <div className="mb-4">
                  <h3 className="text-xs font-semibold text-gray-500 uppercase px-3 py-2">
                    Cette semaine
                  </h3>
                  {conversations
                    .filter((c) => c.date !== "Aujourd'hui")
                    .map((conv) => (
                      <button
                        key={conv.id}
                        className="w-full text-left p-3 hover:bg-gray-50 rounded-lg transition-colors group"
                      >
                        <div className="font-medium text-sm text-gray-900 group-hover:text-teal-600">
                          {conv.title}
                        </div>
                        <div className="text-xs text-gray-500 mt-1 line-clamp-1">
                          {conv.preview}
                        </div>
                        <div className="text-xs text-gray-400 mt-1">
                          {conv.date}
                        </div>
                      </button>
                    ))}
                </div>
              </div>
            )}

            {activeSection === "saved" && (
              <div className="p-4 text-center text-gray-500">
                <BookmarkIcon className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                <p className="text-sm">Aucun favori pour le moment</p>
              </div>
            )}

            {activeSection === "settings" && (
              <div className="p-4 space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">
                    Thème
                  </label>
                  <select className="w-full p-2 border border-gray-200 rounded-lg text-sm">
                    <option>Clair</option>
                    <option>Sombre</option>
                    <option>Auto</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">
                    Langue
                  </label>
                  <select className="w-full p-2 border border-gray-200 rounded-lg text-sm">
                    <option>Français</option>
                    <option>English</option>
                    <option>Español</option>
                  </select>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Overlay for mobile */}
      {activeSection && (
        <div
          className="fixed inset-0 bg-black/20 z-30 lg:hidden"
          onClick={() => setActiveSection(null)}
        />
      )}
    </>
  );
}
