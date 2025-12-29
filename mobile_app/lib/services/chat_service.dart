import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import '../localization/app_language.dart';
import 'token_store.dart';

class ChatService {
  ChatService({
    required TokenStore tokenStore,
    http.Client? client,
  })  : _tokenStore = tokenStore,
        _client = client ?? http.Client();

  final TokenStore _tokenStore;
  final http.Client _client;

  Stream<ChatStreamEvent> sendMessageStream({
    required String message,
    String? sessionId,
    required AppLanguage language,
    Map<String, dynamic>? context,
    String? modelType,
  }) async* {
    final token = await _tokenStore.readAccessToken();
    if (token == null) {
      throw Exception('Not authenticated');
    }

    final uri = Uri.parse('${AppConfig.apiBaseUrl}/chat/stream');
    final request = http.Request('POST', uri);
    request.headers['Content-Type'] = 'application/json';
    request.headers['Authorization'] = 'Bearer $token';
    request.body = jsonEncode({
      'message': message,
      if (sessionId != null) 'session_id': sessionId,
      'model_type': modelType ?? 'deepseek',
      'language': language.code,
      if (context != null && context.isNotEmpty) 'context': context,
    });

    final response = await _client.send(request);

    if (response.statusCode != 200) {
      throw Exception('HTTP ${response.statusCode}');
    }

    String? receivedSessionId;
    String? receivedIntent;
    List<String>? receivedTools;
    String buffer = '';

    await for (final chunk in response.stream.transform(utf8.decoder)) {
      buffer += chunk;
      final lines = buffer.split('\n');

      // Keep the last incomplete line in the buffer
      buffer = lines.isNotEmpty && !chunk.endsWith('\n') ? lines.last : '';
      final completeLines = lines.isNotEmpty && !chunk.endsWith('\n')
          ? lines.sublist(0, lines.length - 1)
          : lines;

      for (final line in completeLines) {
        if (line.trim().isEmpty) continue;

        if (line.startsWith('data: ')) {
          try {
            final jsonStr = line.substring(6).trim();
            if (jsonStr.isEmpty) continue;

            final data = jsonDecode(jsonStr) as Map<String, dynamic>;

            if (data['type'] == 'status') {
              final step = data['step'] as String? ?? '';
              final message = data['message'] as String? ?? '';
              yield ChatStreamEvent.status(step: step, message: message);
            } else if (data['type'] == 'metadata') {
              receivedSessionId = data['session_id'] as String?;
              receivedIntent = data['intent'] as String?;
              receivedTools = (data['tools'] as List<dynamic>?)
                  ?.map((e) => e.toString())
                  .toList();

              yield ChatStreamEvent.metadata(
                sessionId: receivedSessionId,
                intent: receivedIntent,
                tools: receivedTools,
              );
            } else if (data['type'] == 'chunk') {
              final content = data['content'] as String? ?? '';
              if (content.isNotEmpty) {
                yield ChatStreamEvent.chunk(content: content);
              }
            } else if (data['type'] == 'error') {
              final errorMessage = data['message'] as String? ?? 'Unknown error';
              yield ChatStreamEvent.error(message: errorMessage);
              return;
            }
          } catch (e) {
            print('❌ Error parsing SSE line: $e');
            print('   Line was: $line');
          }
        }
      }
    }
  }
}

class ChatStreamEvent {
  ChatStreamEvent._({
    required this.type,
    this.content,
    this.sessionId,
    this.intent,
    this.tools,
    this.errorMessage,
    this.statusStep,
    this.statusMessage,
  });

  final ChatStreamEventType type;
  final String? content;
  final String? sessionId;
  final String? intent;
  final List<String>? tools;
  final String? errorMessage;
  final String? statusStep;
  final String? statusMessage;

  factory ChatStreamEvent.status({
    required String step,
    required String message,
  }) {
    return ChatStreamEvent._(
      type: ChatStreamEventType.status,
      statusStep: step,
      statusMessage: message,
    );
  }

  factory ChatStreamEvent.metadata({
    String? sessionId,
    String? intent,
    List<String>? tools,
  }) {
    return ChatStreamEvent._(
      type: ChatStreamEventType.metadata,
      sessionId: sessionId,
      intent: intent,
      tools: tools,
    );
  }

  factory ChatStreamEvent.chunk({required String content}) {
    return ChatStreamEvent._(
      type: ChatStreamEventType.chunk,
      content: content,
    );
  }

  factory ChatStreamEvent.error({required String message}) {
    return ChatStreamEvent._(
      type: ChatStreamEventType.error,
      errorMessage: message,
    );
  }
}

enum ChatStreamEventType {
  status,
  metadata,
  chunk,
  error,
}
