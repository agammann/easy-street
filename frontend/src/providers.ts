import type { Config, Course, ProviderName } from './types'

export function providerLabel(mode: string) { return mode === 'nebius' ? 'Nebius Token Factory' : mode === 'demo' ? 'Offline demo' : 'OpenAI' }
export function configuredProvider(config: Config | null | undefined, mode: Course['mode']) {
  const provider = config?.providers?.find(item => item.name === mode)
  return provider ?? { name: mode === 'nebius' ? 'nebius' as const : 'openai' as const, model: config?.model ?? 'Unavailable', key_configured: config?.provider === mode && !!config.key_configured, pricing: config?.pricing }
}
export function defaultProvider(config: Config | null): ProviderName { return config?.hosting_mode === 'judging' || config?.provider === 'nebius' ? 'nebius' : 'openai' }

export function maxUploadMiB(config: Config | null | undefined) { return config?.hosting_mode === 'judging' ? Math.max(1, Math.min(15, config.demo?.max_upload_mib ?? 5)) : 15 }
