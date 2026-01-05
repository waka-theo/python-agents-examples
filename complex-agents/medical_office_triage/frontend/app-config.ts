export interface AppConfig {
  pageTitle: string;
  pageDescription: string;
  companyName: string;

  supportsChatInput: boolean;
  supportsVideoInput: boolean;
  supportsScreenShare: boolean;
  isPreConnectBufferEnabled: boolean;

  logo: string;
  startButtonText: string;
  accent?: string;
  logoDark?: string;
  accentDark?: string;

  // for LiveKit Cloud Sandbox
  sandboxId?: string;
  agentName?: string;
}

export const APP_CONFIG_DEFAULTS: AppConfig = {
  companyName: 'Cabinet Médical',
  pageTitle: 'Assistant Médical Virtuel',
  pageDescription: 'Système de triage médical intelligent avec agents spécialisés',

  supportsChatInput: true,
  supportsVideoInput: false,
  supportsScreenShare: false,
  isPreConnectBufferEnabled: true,

  logo: '/lk-logo.svg',
  accent: '#0891b2',
  logoDark: '/lk-logo-dark.svg',
  accentDark: '#22d3ee',
  startButtonText: 'Démarrer l\'appel',

  // for LiveKit Cloud Sandbox
  sandboxId: undefined,
  agentName: undefined,
};
