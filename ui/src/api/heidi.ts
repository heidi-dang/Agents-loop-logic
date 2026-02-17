/**
 * Heidi API Client
 * Thin typed client layer for Heidi backend API
 */

import {
  Agent,
  HealthStatus,
  LoopRequest,
  RunDetails,
  RunRequest,
  RunResponse,
  RunSummary,
  SettingsState,
} from '../types';

const DEFAULT_BASE_URL = '/api';

/**
 * Get current settings from localStorage
 */
export const getSettings = (): SettingsState => {
  return {
    baseUrl: localStorage.getItem('HEIDI_BASE_URL') || DEFAULT_BASE_URL,
    apiKey: localStorage.getItem('HEIDI_API_KEY') || '',
  };
};

/**
 * Save settings to localStorage
 */
export const saveSettings = (settings: SettingsState) => {
  localStorage.setItem('HEIDI_BASE_URL', settings.baseUrl);
  localStorage.setItem('HEIDI_API_KEY', settings.apiKey);
};

/**
 * Get request headers with optional API key
 */
const getHeaders = (customApiKey?: string): HeadersInit => {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  const { apiKey } = getSettings();
  const key = customApiKey !== undefined ? customApiKey : apiKey;
  if (key) {
    headers['X-Heidi-Key'] = key;
  }

  return headers;
};

/**
 * Get base URL with cleanup
 */
const getBaseUrl = (customUrl?: string): string => {
  let url = customUrl || getSettings().baseUrl;
  return url.replace(/\/$/, '');
};

/**
 * Check backend health
 */
export const health = async (
  customBaseUrl?: string,
  customApiKey?: string
): Promise<HealthStatus> => {
  const url = getBaseUrl(customBaseUrl);
  const headers = getHeaders(customApiKey);
  const res = await fetch(`${url}/health`, { headers });
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
};

/**
 * List available agents
 */
export const listAgents = async (): Promise<Agent[]> => {
  try {
    const res = await fetch(`${getBaseUrl()}/agents`, { headers: getHeaders() });
    if (!res.ok) return [];
    return res.json();
  } catch (e) {
    console.warn('Could not fetch agents', e);
    return [];
  }
};

/**
 * List recent runs
 */
export const listRuns = async (limit = 10): Promise<RunSummary[]> => {
  const res = await fetch(`${getBaseUrl()}/runs?limit=${limit}`, {
    headers: getHeaders(),
  });
  if (!res.ok) throw new Error('Failed to fetch runs');
  return res.json();
};

/**
 * Get run details by ID
 */
export const getRun = async (runId: string): Promise<RunDetails> => {
  const res = await fetch(`${getBaseUrl()}/runs/${runId}`, {
    headers: getHeaders(),
  });
  if (!res.ok) throw new Error('Failed to fetch run details');
  return res.json();
};

/**
 * Start a single run (non-looping)
 */
export const runOnce = async (payload: RunRequest): Promise<RunResponse> => {
  const body = {
    prompt: payload.prompt,
    executor: payload.executor || 'copilot',
    workdir: payload.workdir || null,
    ...(payload.dry_run ? { dry_run: true } : {}),
  };

  const res = await fetch(`${getBaseUrl()}/run`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Failed to start run: ${errText}`);
  }
  return res.json();
};

/**
 * Start a loop (multi-step agent mode)
 */
export const runLoop = async (payload: LoopRequest): Promise<RunResponse> => {
  const body = {
    task: payload.task,
    executor: payload.executor || 'copilot',
    max_retries: payload.max_retries ?? 2,
    workdir: payload.workdir || null,
    ...(payload.dry_run ? { dry_run: true } : {}),
  };

  const res = await fetch(`${getBaseUrl()}/loop`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Failed to start loop: ${errText}`);
  }
  return res.json();
};

/**
 * Send a chat message (non-persistent)
 */
export const chat = async (
  message: string,
  executor: string = 'copilot'
): Promise<{ response: string }> => {
  const res = await fetch(`${getBaseUrl()}/chat`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ message, executor }),
  });
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Chat failed: ${errText}`);
  }
  return res.json();
};

/**
 * Cancel a running run
 */
export const cancelRun = async (runId: string): Promise<void> => {
  try {
    await fetch(`${getBaseUrl()}/runs/${runId}/cancel`, {
      method: 'POST',
      headers: getHeaders(),
    });
  } catch (e) {
    console.warn('Failed to cancel run via backend', e);
  }
};

/**
 * Get SSE stream URL for a run
 */
export const getStreamUrl = (runId: string, apiKey?: string): string => {
  const baseUrl = getBaseUrl();
  const key = apiKey || getSettings().apiKey;
  const url = `${baseUrl}/runs/${runId}/stream`;
  return key ? `${url}?key=${encodeURIComponent(key)}` : url;
};

/**
 * Legacy API object for backward compatibility
 */
export const api = {
  health,
  getAgents: listAgents,
  getRuns: listRuns,
  getRun,
  startRun: runOnce,
  startLoop: runLoop,
  chat,
  cancelRun,
  getStreamUrl,
};
