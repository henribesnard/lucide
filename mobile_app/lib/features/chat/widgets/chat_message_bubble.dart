import 'package:flutter/material.dart';

import '../../../theme/app_colors.dart';
import '../../../theme/app_palette.dart';
import '../../../theme/app_spacing.dart';
import '../models/chat_message.dart';

class ChatMessageBubble extends StatelessWidget {
  const ChatMessageBubble({super.key, required this.message});

  final ChatMessage message;

  @override
  Widget build(BuildContext context) {
    final alignment = message.isUser ? Alignment.centerRight : Alignment.centerLeft;
    final bubbleColor = message.isUser
        ? AppColors.bubbleUser
        : AppPalette.bubbleAssistant(context);
    final textColor = message.isUser ? Colors.white : AppPalette.textPrimary(context);
    final borderSide = message.isUser
        ? BorderSide.none
        : BorderSide(color: AppPalette.bubbleAssistantBorder(context));

    return Align(
      alignment: alignment,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: AppSpacing.sm),
        padding: const EdgeInsets.all(AppSpacing.md),
        constraints: const BoxConstraints(maxWidth: 320),
        decoration: BoxDecoration(
          color: bubbleColor,
          borderRadius: BorderRadius.circular(18).copyWith(
            topLeft: Radius.circular(message.isUser ? 18 : 6),
            topRight: Radius.circular(message.isUser ? 6 : 18),
          ),
          border: Border.fromBorderSide(borderSide),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.05),
              blurRadius: 12,
              offset: const Offset(0, 6),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment:
              message.isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
          children: [
            if (!message.isUser)
              Padding(
                padding: const EdgeInsets.only(bottom: AppSpacing.xs),
                child: Text(
                  'STATOS',
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                        color: AppColors.brandTeal,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 1.2,
                      ),
                ),
              ),
            // Show content (status is handled separately in chat_screen.dart)
            if (message.content.isNotEmpty)
              Text(
                message.content,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: textColor,
                      height: 1.5,
                    ),
              ),
            const SizedBox(height: AppSpacing.sm),
            Text(
              _formatTimestamp(message.timestamp),
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: message.isUser
                        ? Colors.white.withOpacity(0.7)
                        : AppPalette.textMuted(context),
                  ),
            ),
          ],
        ),
      ),
    );
  }

  String _formatTimestamp(DateTime time) {
    final hour = time.hour.toString().padLeft(2, '0');
    final minute = time.minute.toString().padLeft(2, '0');
    return '$hour:$minute';
  }
}
