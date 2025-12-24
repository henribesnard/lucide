// utils/conversations.ts

import { AuthManager } from './auth';

export interface ConversationMessage {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export interface ConversationAPI {
  conversation_id: string;
  user_id: string;
  title: string;
  is_archived: boolean;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
  messages?: ConversationMessage[];
}

export interface ConversationListItem {
  conversation_id: string;
  user_id: string;
  title: string;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export class ConversationsAPI {
  /**
   * Récupérer toutes les conversations de l'utilisateur
   */
  static async list(archived = false): Promise<ConversationListItem[]> {
    const response = await AuthManager.authenticatedFetch(
      `/conversations?archived=${archived}`,
      {
        method: 'GET',
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to fetch conversations' }));
      throw new Error(error.detail || 'Failed to fetch conversations');
    }

    return await response.json();
  }

  /**
   * Récupérer une conversation spécifique avec tous ses messages
   */
  static async get(conversationId: string): Promise<ConversationAPI> {
    const response = await AuthManager.authenticatedFetch(
      `/conversations/${conversationId}`,
      {
        method: 'GET',
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Conversation not found' }));
      throw new Error(error.detail || 'Conversation not found');
    }

    return await response.json();
  }

  /**
   * Créer une nouvelle conversation
   */
  static async create(title?: string): Promise<ConversationAPI> {
    const response = await AuthManager.authenticatedFetch(
      `/conversations`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: title || 'Nouvelle conversation',
        }),
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to create conversation' }));
      throw new Error(error.detail || 'Failed to create conversation');
    }

    return await response.json();
  }

  /**
   * Mettre à jour une conversation (titre, archivage)
   */
  static async update(
    conversationId: string,
    updates: { title?: string; is_archived?: boolean }
  ): Promise<ConversationAPI> {
    const response = await AuthManager.authenticatedFetch(
      `/conversations/${conversationId}`,
      {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to update conversation' }));
      throw new Error(error.detail || 'Failed to update conversation');
    }

    return await response.json();
  }

  /**
   * Supprimer une conversation (soft delete)
   */
  static async delete(conversationId: string): Promise<void> {
    const response = await AuthManager.authenticatedFetch(
      `/conversations/${conversationId}`,
      {
        method: 'DELETE',
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to delete conversation' }));
      throw new Error(error.detail || 'Failed to delete conversation');
    }
  }
}
