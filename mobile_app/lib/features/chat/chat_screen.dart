import 'package:flutter/material.dart';

import '../../localization/app_localizations.dart';
import '../../localization/language_scope.dart';
import '../../services/auth_service.dart';
import '../../services/chat_service.dart';
import '../../services/conversations_service.dart';
import '../../shared/widgets/gradient_background.dart';
import '../../shared/widgets/settings_sheet.dart';
import '../../shared/widgets/user_menu_sheet.dart';
import '../../theme/app_palette.dart';
import '../../theme/app_spacing.dart';
import 'models/chat_conversation.dart';
import 'models/chat_message.dart';
import 'models/user_profile.dart';
import 'widgets/chat_header.dart';
import 'widgets/chat_history_panel.dart';
import 'widgets/chat_input_bubble.dart';
import 'widgets/chat_message_bubble.dart';
import 'widgets/dropdowns/model_dropdown.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({
    super.key,
    required this.authService,
    required this.chatService,
    required this.conversationsService,
  });

  final AuthService authService;
  final ChatService chatService;
  final ConversationsService conversationsService;

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  List<ChatConversation> _conversations = [];
  String? _activeConversationId;
  bool _isLoadingConversations = false;
  String? _loadError;
  bool _isSending = false;
  Map<String, dynamic>? _currentContext;
  ModelType _selectedModel = ModelType.deepseek;
  String? _currentStatus;

  @override
  void initState() {
    super.initState();
    _loadConversations();
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  ChatConversation? get _activeConversation {
    if (_activeConversationId == null || _conversations.isEmpty) {
      return null;
    }
    return _conversations.firstWhere(
      (conversation) => conversation.id == _activeConversationId,
      orElse: () => _conversations.first,
    );
  }

  Future<void> _loadConversations() async {
    setState(() {
      _isLoadingConversations = true;
      _loadError = null;
    });

    try {
      final active =
          await widget.conversationsService.list(archived: false);
      final archived =
          await widget.conversationsService.list(archived: true);
      final all = [...active, ...archived];
      setState(() {
        _conversations = all;
        // Don't auto-load any conversation - start with empty state
        _activeConversationId = null;
      });
    } catch (error) {
      setState(() {
        _loadError = error.toString();
      });
    } finally {
      if (mounted) {
        setState(() {
          _isLoadingConversations = false;
        });
      }
    }
  }

  Future<void> _loadConversationMessages(ChatConversation conversation) async {
    if (conversation.messages.isNotEmpty) {
      return;
    }
    try {
      final data = await widget.conversationsService.get(conversation.id);
      if (mounted) {
        setState(() {
          conversation.messages = data.messages;
          // Force update by reassigning the conversations list
          _conversations = List.from(_conversations);
        });
      }
    } catch (error) {
      // Log error but keep local messages if backend has none
      debugPrint('Error loading conversation messages: $error');
    }
  }

  Future<void> _selectConversation(String id) async {
    setState(() {
      _activeConversationId = id;
    });

    final selected = _conversations.firstWhere(
      (conversation) => conversation.id == id,
      orElse: () => _conversations.first,
    );
    await _loadConversationMessages(selected);

    if (_scaffoldKey.currentState?.isDrawerOpen ?? false) {
      Navigator.of(context).pop();
    }
  }

  void _newConversation() {
    setState(() {
      _activeConversationId = null;
    });
  }

  void _handleContextChanged(Map<String, dynamic> context) {
    setState(() {
      _currentContext = context;
    });
  }

  void _handleModelTypeChanged(ModelType model) {
    setState(() {
      _selectedModel = model;
    });
  }

  void _toggleArchive(String id) async {
    final conversation = _conversations.firstWhere(
      (item) => item.id == id,
    );
    final nextArchived = !conversation.isArchived;
    setState(() {
      conversation.isArchived = nextArchived;
    });
    try {
      await widget.conversationsService.update(
        conversationId: id,
        isArchived: nextArchived,
      );
    } catch (_) {
      setState(() {
        conversation.isArchived = !nextArchived;
      });
    }
  }

  Future<void> _handleSend() async {
    final l10n = AppLocalizations.of(context);
    final text = _controller.text.trim();
    if (text.isEmpty || _isSending) {
      return;
    }

    final conversation = _ensureConversation(l10n);
    final now = DateTime.now();

    // Add user message
    setState(() {
      _isSending = true;
      conversation.messages.add(
        ChatMessage(
          role: ChatRole.user,
          content: text,
          timestamp: now,
        ),
      );
      _updateConversationTitle(conversation, text, l10n);
      _promoteConversation(conversation);
    });

    _controller.clear();
    await _scrollToBottom();

    // Create placeholder assistant message
    final assistantMessage = ChatMessage(
      role: ChatRole.assistant,
      content: '',
      timestamp: DateTime.now(),
    );

    setState(() {
      conversation.messages.add(assistantMessage);
    });

    String fullResponse = '';
    String? receivedSessionId;

    try {
      final stream = widget.chatService.sendMessageStream(
        message: text,
        sessionId: _isPendingConversation(conversation)
            ? null
            : conversation.id,
        language: LanguageScope.of(context).language,
        context: _currentContext,
        modelType: modelTypeToBackendString(_selectedModel),
      );

      await for (final event in stream) {
        if (event.type == ChatStreamEventType.status) {
          setState(() {
            _currentStatus = event.statusMessage;
          });
        } else if (event.type == ChatStreamEventType.metadata) {
          if (event.sessionId != null) {
            receivedSessionId = event.sessionId;
          }
        } else if (event.type == ChatStreamEventType.chunk) {
          fullResponse += event.content ?? '';
          setState(() {
            assistantMessage.content = fullResponse;
            _currentStatus = null; // Clear status when response starts
          });
          await _scrollToBottom();
        } else if (event.type == ChatStreamEventType.error) {
          setState(() {
            assistantMessage.content = 'Erreur: ${event.errorMessage}';
            _currentStatus = null;
          });
          break;
        }
      }

      if (receivedSessionId != null) {
        _applySessionId(conversation, receivedSessionId);
      }
      _promoteConversation(conversation);

      if (!_isPendingConversation(conversation)) {
        await widget.conversationsService.update(
          conversationId: conversation.id,
          title: conversation.title,
        );
      }
    } catch (error) {
      setState(() {
        assistantMessage.content = 'Erreur: ${error.toString()}';
      });
    } finally {
      if (mounted) {
        setState(() {
          _isSending = false;
          _currentStatus = null;
        });
      }
      await _scrollToBottom();
    }
  }

  ChatConversation _ensureConversation(AppLocalizations l10n) {
    final existing = _activeConversation;
    if (existing != null) {
      return existing;
    }
    final draft = ChatConversation(
      id: 'pending-${DateTime.now().microsecondsSinceEpoch}',
      title: l10n.t(AppTextKey.conversationPlaceholder),
      messages: [],
      updatedAt: DateTime.now(),
    );
    setState(() {
      _conversations.insert(0, draft);
      _activeConversationId = draft.id;
    });
    return draft;
  }

  void _applySessionId(ChatConversation conversation, String sessionId) {
    if (sessionId.isEmpty || !_isPendingConversation(conversation)) {
      return;
    }
    final previousId = conversation.id;
    conversation.id = sessionId;
    _activeConversationId = sessionId;
    _conversations.removeWhere(
      (item) => item.id == sessionId && item != conversation,
    );
    if (previousId != sessionId) {
      _conversations.removeWhere(
        (item) => item.id == previousId && item != conversation,
      );
    }
  }

  void _updateConversationTitle(
    ChatConversation conversation,
    String message,
    AppLocalizations l10n,
  ) {
    if (conversation.title != l10n.t(AppTextKey.conversationPlaceholder)) {
      return;
    }
    final trimmed = message.replaceAll('\n', ' ').trim();
    if (trimmed.isEmpty) {
      return;
    }
    final title = trimmed.length > 32 ? '${trimmed.substring(0, 32)}…' : trimmed;
    conversation.title = title;
  }

  void _promoteConversation(ChatConversation conversation) {
    conversation.updatedAt = DateTime.now();
    _conversations.removeWhere((item) => item.id == conversation.id);
    _conversations.insert(0, conversation);
  }

  bool _isPendingConversation(ChatConversation conversation) {
    return conversation.id.startsWith('pending-');
  }

  Future<void> _scrollToBottom() async {
    await Future.delayed(const Duration(milliseconds: 100));
    if (!_scrollController.hasClients) {
      return;
    }
    await _scrollController.animateTo(
      _scrollController.position.maxScrollExtent + 120,
      duration: const Duration(milliseconds: 250),
      curve: Curves.easeOut,
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final user = widget.authService.currentUser ??
        UserProfile(name: 'Statos', email: 'contact@statos.ai');
    final messages = _activeConversation?.messages ?? [];

    return LayoutBuilder(
      builder: (context, constraints) {
        final showSidebar = constraints.maxWidth >= 980;
        return Scaffold(
          key: _scaffoldKey,
          backgroundColor: Colors.transparent,
          drawer: showSidebar
              ? null
              : Drawer(
                  child: ChatHistoryPanel(
                    conversations: _conversations,
                    activeConversationId: _activeConversationId,
                    onSelectConversation: _selectConversation,
                    onNewConversation: () {
                      _newConversation();
                      Navigator.of(context).pop();
                    },
                    onToggleArchive: _toggleArchive,
                    onClose: () => Navigator.of(context).pop(),
                    isLoading: _isLoadingConversations,
                    errorMessage: _loadError,
                  ),
                ),
          body: Stack(
            children: [
              const GradientBackground(),
              SafeArea(
                bottom: false,
                child: Row(
                  children: [
                    if (showSidebar)
                      ChatHistoryPanel(
                        conversations: _conversations,
                        activeConversationId: _activeConversationId,
                        onSelectConversation: _selectConversation,
                        onNewConversation: _newConversation,
                        onToggleArchive: _toggleArchive,
                        isLoading: _isLoadingConversations,
                        errorMessage: _loadError,
                      ),
                    Expanded(
                      child: Column(
                        children: [
                          ChatHeader(
                            showMenuButton: !showSidebar,
                            onMenuPressed: () =>
                                _scaffoldKey.currentState?.openDrawer(),
                            userInitials: user.initials,
                            onUserPressed: () => _openUserMenu(context, user),
                          ),
                          // Show conversation header only for existing conversations
                          if (_activeConversationId != null)
                            _ConversationHeader(
                              title: _activeConversation?.title ??
                                  l10n.t(AppTextKey.conversationPlaceholder),
                              subtitle: _activeConversation?.updatedAt,
                            ),

                          // Main content area
                          Expanded(
                            child: _activeConversationId == null
                                // New conversation: center the input bubble
                                ? Center(
                                    child: Padding(
                                      padding: const EdgeInsets.all(
                                          AppSpacing.lg),
                                      child: Column(
                                        mainAxisAlignment:
                                            MainAxisAlignment.center,
                                        children: [
                                          Text(
                                            'Sur quoi travaillez-vous ?',
                                            style: Theme.of(context)
                                                .textTheme
                                                .headlineMedium
                                                ?.copyWith(
                                                  fontWeight: FontWeight.w600,
                                                  color: AppPalette
                                                      .textPrimary(context),
                                                ),
                                            textAlign: TextAlign.center,
                                          ),
                                          const SizedBox(height: AppSpacing.xl),
                                          ChatInputBubble(
                                            controller: _controller,
                                            onSend: _handleSend,
                                            onContextChanged:
                                                _handleContextChanged,
                                            contextDisabled: false,
                                            onModelTypeChanged:
                                                _handleModelTypeChanged,
                                          ),
                                        ],
                                      ),
                                    ),
                                  )
                                // Existing conversation: messages + input at bottom
                                : Column(
                                    children: [
                                      // Messages area
                                      Expanded(
                                        child: messages.isEmpty
                                            ? Center(
                                                child: Text(
                                                  l10n.t(
                                                      AppTextKey.emptyChat),
                                                  style: Theme.of(context)
                                                      .textTheme
                                                      .bodySmall
                                                      ?.copyWith(
                                                        color: AppPalette
                                                            .textMuted(
                                                                context),
                                                      ),
                                                ),
                                              )
                                            : ListView.builder(
                                                controller: _scrollController,
                                                padding:
                                                    const EdgeInsets.symmetric(
                                                  horizontal: AppSpacing.lg,
                                                  vertical: AppSpacing.sm,
                                                ),
                                                itemCount: messages.length,
                                                itemBuilder: (context, index) {
                                                  return ChatMessageBubble(
                                                    message: messages[index],
                                                  );
                                                },
                                              ),
                                      ),
                                      // Status indicator
                                      if (_isSending && _currentStatus != null)
                                        Container(
                                          padding: const EdgeInsets.symmetric(
                                            horizontal: AppSpacing.lg,
                                            vertical: AppSpacing.sm,
                                          ),
                                          child: Row(
                                            children: [
                                              SizedBox(
                                                width: 16,
                                                height: 16,
                                                child: CircularProgressIndicator(
                                                  strokeWidth: 2,
                                                  valueColor:
                                                      AlwaysStoppedAnimation<Color>(
                                                    Theme.of(context)
                                                        .colorScheme
                                                        .primary,
                                                  ),
                                                ),
                                              ),
                                              const SizedBox(width: AppSpacing.sm),
                                              Expanded(
                                                child: Text(
                                                  _currentStatus!,
                                                  style: Theme.of(context)
                                                      .textTheme
                                                      .bodySmall
                                                      ?.copyWith(
                                                        color: AppPalette.textMuted(
                                                            context),
                                                      ),
                                                ),
                                              ),
                                            ],
                                          ),
                                        ),
                                      // Input bubble at bottom
                                      SafeArea(
                                        top: false,
                                        child: Padding(
                                          padding: const EdgeInsets.all(
                                              AppSpacing.lg),
                                          child: ChatInputBubble(
                                            controller: _controller,
                                            onSend: _handleSend,
                                            onContextChanged:
                                                _handleContextChanged,
                                            contextDisabled: true,
                                            onModelTypeChanged:
                                                _handleModelTypeChanged,
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  void _openUserMenu(BuildContext context, UserProfile profile) {
    UserMenuSheet.show(
      context,
      profile: profile,
      onProfile: () {
        Navigator.of(context).pop();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              AppLocalizations.of(context).t(AppTextKey.profileComingSoon),
            ),
          ),
        );
      },
      onSettings: () {
        Navigator.of(context).pop();
        SettingsSheet.show(context);
      },
      onLogout: () {
        Navigator.of(context).pop();
        widget.authService.logout();
      },
    );
  }
}

class _ConversationHeader extends StatelessWidget {
  const _ConversationHeader({required this.title, this.subtitle});

  final String title;
  final DateTime? subtitle;

  @override
  Widget build(BuildContext context) {
    final subtitleText = subtitle == null
        ? ''
        : '${subtitle!.day.toString().padLeft(2, '0')}/'
            '${subtitle!.month.toString().padLeft(2, '0')}/'
            '${subtitle!.year}';

    return Padding(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.lg,
        vertical: AppSpacing.sm,
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                ),
                if (subtitleText.isNotEmpty)
                  Text(
                    subtitleText,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: AppPalette.textMuted(context),
                        ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
