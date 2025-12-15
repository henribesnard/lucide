"use client";

import MainSidebar from "@/components/MainSidebar";
import ChatBubble from "@/components/ChatBubble";

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Main Sidebar */}
      <MainSidebar />

      {/* Main Content Area */}
      <div className="w-full lg:ml-16">
        <ChatBubble />
      </div>
    </div>
  );
}
