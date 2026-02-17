// Original types from work UI
export enum AIProviderId {
  GEMINI = 'gemini',
  COPILOT = 'copilot',
  OPENAI = 'openai',
  GROK = 'grok',
  LOCAL = 'local',
  HEIDI = 'heidi' // Added Heidi as default provider
}

export enum AppView {
  CHAT = 'chat',
  TERMINAL = 'terminal',
  AGENT = 'agent',
  RUN = 'run',
  LOOP = 'loop',
  DASHBOARD = 'dashboard',
  SETTINGS = 'settings'
}

export interface User {
  id: string;
  name?: string | null;
  email?: string | null;
  image?: string | null;
}

export interface Session {
  user: User;
  expires: string;
}

export interface ToolCall {
  id: string;
  name: string;
  args: any;
  status: 'pending' | 'approved' | 'rejected' | 'executing' | 'completed' | 'error';
  result?: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  toolCalls?: ToolCall[];
  thought?: string;
}

export interface ChatSession {
  id: string;
  providerId: AIProviderId;
  title: string;
  messages: Message[];
  createdAt: Date;
  isAgentMode?: boolean;
}

export interface ProjectFile {
  id: string;
  name: string;
  size: string;
  type: string;
  content?: string;
}

export interface ProviderInfo {
  id: AIProviderId;
  name: string;
  description: string;
  models: string[];
  icon: string;
  isConnected: boolean;
}

export interface DeviceFlowResponse {
  device_code: string;
  user_code: string;
  verification_uri: string;
  expires_in: number;
  interval: number;
}

export interface SSHConfig {
  host: string;
  port: number;
  username: string;
  password?: string;
  privateKey?: string;
}

export interface LocalProviderConfig {
  baseUrl: string;
  model: string;
}

// Heidi API Types
export enum RunStatus {
  IDLE = 'idle',
  PLANNING = 'planning',
  EXECUTING = 'executing',
  REVIEWING = 'reviewing',
  AUDITING = 'auditing',
  RETRYING = 'retrying',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
  INITIATING = 'initiating',
  CANCELLING = 'cancelling',
}

export enum AppMode {
  CHAT = 'chat',
  RUN = 'run',
  LOOP = 'loop',
}

export interface Agent {
  name: string;
  description?: string;
}

export interface RunRequest {
  prompt: string;
  executor: string;
  workdir?: string | null;
  persona?: string;
  dry_run?: boolean;
}

export interface LoopRequest {
  task: string;
  executor: string;
  max_retries: number;
  workdir?: string | null;
  persona?: string;
  dry_run?: boolean;
  context_paths?: string[];
}

export interface RunResponse {
  run_id: string;
  status: string;
  result?: string | null;
  error?: string | null;
}

export interface RunEvent {
  type: string;
  message: string;
  ts: string;
  data?: any;
  details?: any;
}

export interface ToolEvent {
  id: string;
  name: string;
  status: 'started' | 'completed' | 'failed';
  input?: string;
  output?: string;
  error?: string;
  startedAt?: string;
  completedAt?: string;
}

export interface RunMeta {
  status: string;
  task?: string;
  prompt?: string;
  executor: string;
  created_at?: string;
  [key: string]: any;
}

export interface RunDetails {
  run_id: string;
  meta: RunMeta;
  events: RunEvent[];
  result?: string;
  error?: string;
}

export interface RunSummary {
  run_id: string;
  status: string;
  task?: string;
  executor?: string;
  created_at?: string;
}

export interface HealthStatus {
  status: string;
  version?: string;
  uptime?: string;
}

export interface SettingsState {
  baseUrl: string;
  apiKey: string;
}

export interface StreamCallbacks {
  onEvent?: (event: RunEvent) => void;
  onError?: (error: Error) => void;
  onDone?: () => void;
  onToolStart?: (tool: ToolEvent) => void;
  onToolLog?: (toolName: string, log: string) => void;
  onToolDone?: (toolName: string, output: string) => void;
  onToolError?: (toolName: string, error: string) => void;
  onStatusChange?: (status: string) => void;
  onThinking?: (message: string) => void;
}
