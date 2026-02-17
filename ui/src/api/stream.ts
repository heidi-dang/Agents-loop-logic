/**
 * Heidi Stream Client
 * SSE (Server-Sent Events) streaming support for run updates
 */

import { RunEvent, StreamCallbacks, ToolEvent } from '../types';
import { getStreamUrl } from './heidi';

export interface StreamController {
  close: () => void;
  isActive: () => boolean;
}

/**
 * Subscribe to run stream updates via SSE
 * Falls back to polling if SSE is not supported or fails
 */
export const subscribeRunStream = (
  runId: string,
  callbacks: StreamCallbacks & { apiKey?: string }
): StreamController => {
  const { apiKey, onEvent, onError, onDone, onToolStart, onToolLog, onToolDone, onToolError, onStatusChange, onThinking } = callbacks;
  
  let eventSource: EventSource | null = null;
  let pollingInterval: NodeJS.Timeout | null = null;
  let isClosed = false;

  const close = () => {
    isClosed = true;
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }
    if (pollingInterval) {
      clearInterval(pollingInterval);
      pollingInterval = null;
    }
  };

  const isActive = () => !isClosed;

  // Try SSE first
  try {
    const streamUrl = getStreamUrl(runId, apiKey);
    eventSource = new EventSource(streamUrl);

    eventSource.onopen = () => {
      console.log('[Heidi Stream] SSE Connected');
    };

    eventSource.onmessage = (event) => {
      if (isClosed) return;

      try {
        // Try to parse as JSON first
        let data: any;
        try {
          data = JSON.parse(event.data);
        } catch {
          // If not JSON, treat as plain text message
          data = { type: 'message', message: event.data };
        }

        const runEvent: RunEvent = {
          type: data.type || 'message',
          message: data.message || data.data?.message || event.data,
          ts: data.ts || Date.now().toString(),
          data: data.data,
          details: data.details,
        };

        onEvent?.(runEvent);

        // Process specific event types
        switch (data.type) {
          case 'thinking':
            onThinking?.(data.data?.message || 'Thinking...');
            break;

          case 'tool_start':
            onToolStart?.({
              id: `${data.data?.tool}-${Date.now()}`,
              name: data.data?.tool || 'Unknown',
              status: 'started',
              input: data.data?.input,
              startedAt: new Date().toISOString(),
            });
            break;

          case 'tool_log':
            onToolLog?.(data.data?.tool, data.data?.log || '');
            break;

          case 'tool_done':
            onToolDone?.(data.data?.tool, data.data?.output || '');
            break;

          case 'tool_error':
            onToolError?.(data.data?.tool, data.data?.error || 'Unknown error');
            break;

          case 'run_state':
          case 'status':
            onStatusChange?.(data.data?.state || data.data?.status || 'running');
            break;

          case 'done':
          case 'completed':
            onStatusChange?.('completed');
            onDone?.();
            close();
            break;

          case 'error':
            onError?.(new Error(data.message || data.data?.error || 'Stream error'));
            close();
            break;
        }
      } catch (e) {
        console.warn('[Heidi Stream] Error parsing event:', event.data, e);
      }
    };

    eventSource.onerror = (err) => {
      if (isClosed) return;
      console.warn('[Heidi Stream] SSE Error, falling back to polling', err);
      eventSource?.close();
      eventSource = null;
      startPolling();
    };
  } catch (e) {
    console.warn('[Heidi Stream] Failed to setup SSE, using polling', e);
    startPolling();
  }

  // Polling fallback
  function startPolling() {
    if (pollingInterval || isClosed) return;

    const poll = async () => {
      if (isClosed) return;

      try {
        const { getRun } = await import('./heidi');
        const details = await getRun(runId);

        if (details.events) {
          // Send new events
          details.events.forEach((event, index) => {
            // Simple deduplication: only send last event if it's new
            if (index === details.events.length - 1) {
              onEvent?.(event);
            }
          });
        }

        const status = details.meta?.status || 'unknown';
        onStatusChange?.(status);

        const terminalStatuses = ['completed', 'failed', 'cancelled'];
        if (terminalStatuses.includes(status.toLowerCase())) {
          onDone?.();
          close();
        }
      } catch (err) {
        console.error('[Heidi Stream] Polling error:', err);
      }
    };

    poll();
    pollingInterval = setInterval(poll, 1000);
  }

  return { close, isActive };
};

/**
 * Legacy function for backward compatibility
 */
export const createEventStream = subscribeRunStream;
