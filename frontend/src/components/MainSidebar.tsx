"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import {
  HomeIcon,
  ClockIcon,
  ArchiveBoxIcon,
  ArrowUturnLeftIcon,
  Cog6ToothIcon,
  PlusIcon,
  ChevronRightIcon,
  Bars3Icon,
  XMarkIcon,
} from "@heroicons/react/24/outline";
import { AuthManager } from "@/utils/auth";
import type { Conversation } from "@/types/conversation";

interface StoredUser {
  email?: string;
  full_name?: string;
  first_name?: string;
  last_name?: string;
}

interface MainSidebarProps {
  conversations: Conversation[];
  activeConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewConversation: () => void;
  onToggleArchive: (id: string, archived: boolean) => void;
}

export default function MainSidebar({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  onToggleArchive,
}: MainSidebarProps) {
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [user, setUser] = useState<StoredUser | null>(null);

  useEffect(() => {
    setUser(AuthManager.getUser());
  }, []);

  const fullName =
    user?.full_name ||
    [user?.first_name, user?.last_name].filter(Boolean).join(" ") ||
    "";
  const userEmail = user?.email || "";

  const initials = (() => {
    const cleaned = fullName.trim();
    if (cleaned) {
      const parts = cleaned.split(/\s+/).filter(Boolean);
      if (parts.length === 1) {
        return parts[0].slice(0, 1).toUpperCase();
      }
      return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
    }
    if (userEmail) {
      return userEmail.slice(0, 1).toUpperCase();
    }
    return "U";
  })();

  const displayName = fullName.trim() || userEmail.split("@")[0] || "Utilisateur";
  const historyConversations = conversations.filter((c) => !c.isArchived);
  const archivedConversations = conversations.filter((c) => c.isArchived);

  const handleSelectConversation = (id: string) => {
    onSelectConversation(id);
    if (isMobileMenuOpen) {
      setIsMobileMenuOpen(false);
    }
  };

  const toggleArchive = (id: string, archived: boolean) => {
    onToggleArchive(id, archived);
  };

  const handleLogout = async () => {
    await AuthManager.logout();
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  };

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
      count: historyConversations.length,
    },
    {
      id: "archive",
      icon: ArchiveBoxIcon,
      label: "Archives",
      hasSubmenu: true,
      count: archivedConversations.length,
    },
    {
      id: "settings",
      icon: Cog6ToothIcon,
      label: "Parametres",
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
        className={`lg:hidden fixed inset-y-0 left-0 w-64 bg-white shadow-2xl z-50 transform transition-transform duration-300 ease-in-out ${isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"
          }`}
      >
        {/* Mobile Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-white ring-1 ring-slate-200/60 flex items-center justify-center">
              <Image src="/statos-s.svg" alt="STATOS" width={24} height={24} />
            </div>
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
            className="w-full p-3 bg-gradient-to-r from-teal-600 to-teal-700 hover:from-teal-700 hover:to-teal-800 text-white rounded-lg flex items-center justify-center gap-2 transition-colors font-medium"
            onClick={() => {
              onNewConversation();
              setActiveSection(null);
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
                  className={`w-full p-3 rounded-lg flex items-center gap-3 transition-all ${isActive
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
              {historyConversations
                .filter((c) => c.dateLabel === "Aujourd'hui")
                .map((conv) => {
                  const isActive = conv.id === activeConversationId;
                  return (
                    <div
                      key={conv.id}
                      className={`flex items-start gap-2 p-3 rounded-lg transition-colors ${isActive ? "bg-teal-50" : "hover:bg-gray-50"
                        }`}
                    >
                      <button
                        className="flex-1 text-left"
                        onClick={() => handleSelectConversation(conv.id)}
                      >
                        <div className="font-medium text-sm text-gray-900">
                          {conv.title}
                        </div>
                        <div className="text-xs text-gray-500 mt-1 line-clamp-1">
                          {conv.preview}
                        </div>
                      </button>
                      <button
                        onClick={() => toggleArchive(conv.id, true)}
                        className="p-1 rounded-md hover:bg-gray-100"
                        aria-label="Archiver la conversation"
                      >
                        <ArchiveBoxIcon className="w-4 h-4 text-gray-400" />
                      </button>
                    </div>
                  );
                })}
              {historyConversations.filter((c) => c.dateLabel === "Aujourd'hui")
                .length === 0 && (
                  <div className="p-3 text-xs text-gray-500">
                    Aucune conversation aujourd'hui.
                  </div>
                )}
            </div>
          )}

          {activeSection === "archive" && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <h3 className="text-xs font-semibold text-gray-500 uppercase px-3 py-2">
                Conversations archivees
              </h3>
              {archivedConversations.length === 0 && (
                <div className="p-3 text-xs text-gray-500">
                  Aucune conversation archivee.
                </div>
              )}
              {archivedConversations.map((conv) => {
                const isActive = conv.id === activeConversationId;
                return (
                  <div
                    key={conv.id}
                    className={`flex items-start gap-2 p-3 rounded-lg transition-colors ${isActive ? "bg-teal-50" : "hover:bg-gray-50"
                      }`}
                  >
                    <button
                      className="flex-1 text-left"
                      onClick={() => handleSelectConversation(conv.id)}
                    >
                      <div className="font-medium text-sm text-gray-900">
                        {conv.title}
                      </div>
                      <div className="text-xs text-gray-500 mt-1 line-clamp-1">
                        {conv.preview}
                      </div>
                      <div className="text-xs text-gray-400 mt-1">
                        {conv.dateLabel}
                      </div>
                    </button>
                    <button
                      onClick={() => toggleArchive(conv.id, false)}
                      className="p-1 rounded-md hover:bg-gray-100"
                      aria-label="Restaurer la conversation"
                    >
                      <ArrowUturnLeftIcon className="w-4 h-4 text-gray-400" />
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Mobile Footer - User */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200 bg-white">
          <button
            type="button"
            className="w-full flex items-center gap-3"
            onClick={() => setIsUserMenuOpen((prev) => !prev)}
          >
            <div className="w-10 h-10 bg-gradient-to-br from-teal-600 to-teal-700 rounded-full flex items-center justify-center">
              <span className="text-white font-semibold text-sm">{initials}</span>
            </div>
            <div className="text-left">
              <div className="font-medium text-sm text-gray-900">
                {displayName}
              </div>
              <div className="text-xs text-gray-500">{userEmail}</div>
            </div>
          </button>
          {isUserMenuOpen && (
            <div className="mt-3 p-3 rounded-lg bg-slate-50 border border-slate-200">
              <button
                onClick={handleLogout}
                className="w-full text-sm font-medium text-red-600 hover:text-red-700"
              >
                Deconnexion
              </button>
            </div>
          )}
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
          <div className="w-12 h-12 rounded-lg bg-white ring-1 ring-slate-200/60 flex items-center justify-center">
            <Image src="/statos-s.svg" alt="STATOS" width={28} height={28} />
          </div>
        </div>

        {/* New Chat Button */}
        <button
          className="w-10 h-10 bg-gray-100 hover:bg-gray-200 rounded-lg flex items-center justify-center mb-6 transition-colors"
          onClick={() => {
            onNewConversation();
            setActiveSection(null);
          }}
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
                onClick={() => setActiveSection(isActive ? null : item.id)}
                className={`relative w-12 h-12 rounded-lg flex items-center justify-center transition-all ${isActive
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
        <div className="mt-auto relative flex flex-col items-center">
          <button
            type="button"
            onClick={() => setIsUserMenuOpen((prev) => !prev)}
            className="w-10 h-10 bg-gradient-to-br from-teal-600 to-teal-700 rounded-full flex items-center justify-center"
            title={displayName}
          >
            <span className="text-white font-semibold text-sm">{initials}</span>
          </button>
          {isUserMenuOpen && (
            <div className="absolute bottom-14 left-14 w-56 bg-white border border-slate-200 rounded-xl shadow-lg p-3">
              <div className="text-sm font-semibold text-slate-900">
                {displayName}
              </div>
              <div className="text-xs text-slate-500 mt-0.5">
                {userEmail}
              </div>
              <button
                onClick={handleLogout}
                className="mt-3 w-full text-sm font-medium text-red-600 hover:text-red-700"
              >
                Deconnexion
              </button>
            </div>
          )}
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
                  {historyConversations
                    .filter((c) => c.dateLabel === "Aujourd'hui")
                    .map((conv) => {
                      const isActive = conv.id === activeConversationId;
                      return (
                        <div
                          key={conv.id}
                          className={`flex items-start gap-2 p-3 rounded-lg transition-colors group ${isActive ? "bg-teal-50" : "hover:bg-gray-50"
                            }`}
                        >
                          <button
                            className="flex-1 text-left"
                            onClick={() => handleSelectConversation(conv.id)}
                          >
                            <div className="font-medium text-sm text-gray-900 group-hover:text-teal-600">
                              {conv.title}
                            </div>
                            <div className="text-xs text-gray-500 mt-1 line-clamp-1">
                              {conv.preview}
                            </div>
                          </button>
                          <button
                            onClick={() => toggleArchive(conv.id, true)}
                            className="p-1 rounded-md hover:bg-gray-100"
                            aria-label="Archiver la conversation"
                          >
                            <ArchiveBoxIcon className="w-4 h-4 text-gray-400" />
                          </button>
                        </div>
                      );
                    })}
                  {historyConversations.filter((c) => c.dateLabel === "Aujourd'hui")
                    .length === 0 && (
                      <div className="px-3 py-2 text-xs text-gray-500">
                        Aucune conversation aujourd'hui.
                      </div>
                    )}
                </div>

                <div className="mb-4">
                  <h3 className="text-xs font-semibold text-gray-500 uppercase px-3 py-2">
                    Cette semaine
                  </h3>
                  {historyConversations
                    .filter((c) => c.dateLabel !== "Aujourd'hui")
                    .map((conv) => {
                      const isActive = conv.id === activeConversationId;
                      return (
                        <div
                          key={conv.id}
                          className={`flex items-start gap-2 p-3 rounded-lg transition-colors group ${isActive ? "bg-teal-50" : "hover:bg-gray-50"
                            }`}
                        >
                          <button
                            className="flex-1 text-left"
                            onClick={() => handleSelectConversation(conv.id)}
                          >
                            <div className="font-medium text-sm text-gray-900 group-hover:text-teal-600">
                              {conv.title}
                            </div>
                            <div className="text-xs text-gray-500 mt-1 line-clamp-1">
                              {conv.preview}
                            </div>
                            <div className="text-xs text-gray-400 mt-1">
                              {conv.dateLabel}
                            </div>
                          </button>
                          <button
                            onClick={() => toggleArchive(conv.id, true)}
                            className="p-1 rounded-md hover:bg-gray-100"
                            aria-label="Archiver la conversation"
                          >
                            <ArchiveBoxIcon className="w-4 h-4 text-gray-400" />
                          </button>
                        </div>
                      );
                    })}
                  {historyConversations.filter((c) => c.dateLabel !== "Aujourd'hui")
                    .length === 0 && (
                      <div className="px-3 py-2 text-xs text-gray-500">
                        Aucune conversation cette semaine.
                      </div>
                    )}
                </div>
              </div>
            )}

            {activeSection === "archive" && (
              <div className="p-2">
                {archivedConversations.length === 0 && (
                  <div className="p-4 text-center text-gray-500">
                    <ArchiveBoxIcon className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                    <p className="text-sm">Aucune conversation archivee</p>
                  </div>
                )}
                {archivedConversations.map((conv) => {
                  const isActive = conv.id === activeConversationId;
                  return (
                    <div
                      key={conv.id}
                      className={`flex items-start gap-2 p-3 rounded-lg transition-colors group ${isActive ? "bg-teal-50" : "hover:bg-gray-50"
                        }`}
                    >
                      <button
                        className="flex-1 text-left"
                        onClick={() => handleSelectConversation(conv.id)}
                      >
                        <div className="font-medium text-sm text-gray-900 group-hover:text-teal-600">
                          {conv.title}
                        </div>
                        <div className="text-xs text-gray-500 mt-1 line-clamp-1">
                          {conv.preview}
                        </div>
                        <div className="text-xs text-gray-400 mt-1">
                          {conv.dateLabel}
                        </div>
                      </button>
                      <button
                        onClick={() => toggleArchive(conv.id, false)}
                        className="p-1 rounded-md hover:bg-gray-100"
                        aria-label="Restaurer la conversation"
                      >
                        <ArrowUturnLeftIcon className="w-4 h-4 text-gray-400" />
                      </button>
                    </div>
                  );
                })}
              </div>
            )}

            {activeSection === "settings" && (
              <div className="p-4 space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">
                    Theme
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
                    <option>Francais</option>
                    <option>English</option>
                    <option>Espanol</option>
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
