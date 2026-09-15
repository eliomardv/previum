export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message) }
}
export function errorMessage(status: number): string {
  return ({
    401: 'Sessão inválida ou expirada. Entre novamente.',
    403: 'Você não tem permissão para esta operação.',
    404: 'Registro não encontrado neste espaço de trabalho.',
    422: 'Confira os campos informados e tente novamente.',
  } as Record<number, string>)[status] ?? 'Serviço indisponível. Tente novamente em instantes.'
}
export async function request<T>(path: string, token = '', options: RequestInit = {}): Promise<T> {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 15000)
  try {
    const response = await fetch('/api/v1' + path, {
      ...options, signal: controller.signal,
      headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: 'Bearer ' + token } : {}) },
    })
    if (!response.ok) throw new ApiError(response.status, errorMessage(response.status))
    return await response.json() as T
  } catch (error) {
    if (error instanceof ApiError) throw error
    throw new ApiError(0, 'Não foi possível conectar à API. Verifique a conexão e tente novamente.')
  } finally { clearTimeout(timeout) }
}
export function message(error: unknown) {
  return error instanceof Error ? error.message : 'Não foi possível concluir a operação.'
}
