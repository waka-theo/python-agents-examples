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

  logo: '/logo-FranceCare.png',
  accent: '#1e3a5f',
  logoDark: '/logo-FranceCare.png',
  accentDark: '#ef4444',
  startButtonText: 'Démarrer l\'appel',

  // for LiveKit Cloud Sandbox
  sandboxId: undefined,
  agentName: undefined,
};
