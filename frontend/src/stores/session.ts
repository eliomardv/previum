import { defineStore } from 'pinia'
import { ref } from 'vue'
import { ApiError, request } from '../api'
import type { Identity, Tenant } from '../types'

export const useSession = defineStore('session', () => {
  const token = ref('')
  const identity = ref<Identity | null>(null)
  const tenant = ref<Tenant | null>(null)
  const notice = ref('')
  function logout() { token.value = ''; identity.value = null; tenant.value = null }
  async function api<T>(path: string, options: RequestInit = {}) {
    const activeToken = token.value
    if (!activeToken) throw new ApiError(401, 'Entre para continuar.')
    try { return await request<T>(path, activeToken, options) }
    catch (error) {
      if (error instanceof ApiError && error.status === 401 && token.value === activeToken) {
        logout(); notice.value = error.message
      }
      throw error
    }
  }
  async function login(email: string, password: string, tenantId: string) {
    logout(); notice.value = ''
    const response = await request<{ access_token: string }>('/auth/login', '', {
      method: 'POST', body: JSON.stringify({ email, password, tenant_id: tenantId }),
    })
    token.value = response.access_token
    try {
      identity.value = await api<Identity>('/auth/me')
      tenant.value = await api<Tenant>('/tenants/' + encodeURIComponent(identity.value.tenant_id))
    } catch (error) { logout(); throw error }
  }
  return { token, identity, tenant, notice, api, login, logout }
})
