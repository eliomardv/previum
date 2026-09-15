import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, request } from '../src/api'
import { createPinia, setActivePinia } from 'pinia'
import { useSession } from '../src/stores/session'
afterEach(() => vi.unstubAllGlobals())
describe('API e sessão', () => {
  it.each([401,403,404,422,503])('traduz HTTP %s', async status => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}', { status })))
    await expect(request('/companies')).rejects.toMatchObject({ status })
  })
  it('traduz falha de conexão', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('network')))
    await expect(request('/companies')).rejects.toBeInstanceOf(ApiError)
  })
  it('limpa sessão quando o vínculo é revogado', async () => {
    setActivePinia(createPinia())
    const store = useSession(); store.token = 'synthetic'
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}', { status: 401 })))
    await expect(store.api('/workers')).rejects.toMatchObject({ status: 401 })
    expect(store.token).toBe('')
    expect(store.notice).toContain('expirada')
  })
  it('não encerra a sessão por indisponibilidade', async () => {
    setActivePinia(createPinia())
    const store = useSession(); store.token = 'synthetic'
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}', { status: 503 })))
    await expect(store.api('/workers')).rejects.toMatchObject({ status: 503 })
    expect(store.token).toBe('synthetic')
  })
})
