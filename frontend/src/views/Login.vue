<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useSession } from '../stores/session'
import { ApiError, message } from '../api'
const session = useSession(), router = useRouter()
const email = ref(''), password = ref(''), tenant = ref(''), busy = ref(false), error = ref('')
async function submit() {
  busy.value = true; error.value = ''
  try { await session.login(email.value.trim(), password.value, tenant.value.trim()); await router.replace('/') }
  catch (err) { error.value = err instanceof ApiError && err.status === 401 ? 'Confira email, senha e ID do espaço de trabalho.' : message(err) }
  finally { password.value = ''; busy.value = false }
}
</script>
<template>
  <div class="login-shell">
    <section class="login-story"><div class="brand"><span class="brand-mark">P</span>previum.</div><div><span class="eyebrow">SAÚDE E SEGURANÇA DO TRABALHO</span><h1>Pessoas no centro.<br>Gestão em dia.</h1><p>Um espaço para organizar suas empresas e acompanhar as pessoas que fazem parte delas.</p><div class="story-lines" aria-hidden="true"><i></i><i></i><i></i></div></div><small>Seu trabalho, com mais clareza.</small></section>
    <section class="login-panel"><form @submit.prevent="submit"><span class="eyebrow">BEM-VINDO AO PREVIUM</span><h2>Acesse seu espaço</h2><p class="muted">Entre com as credenciais do seu vínculo.</p>
      <div v-if="error || session.notice" class="error" role="alert">{{ error || session.notice }}</div>
      <label>Email<input v-model="email" type="email" autocomplete="username" required maxlength="254" placeholder="voce@empresa.com.br"></label>
      <label>Senha<input v-model="password" type="password" autocomplete="current-password" required maxlength="1024" placeholder="Sua senha"></label>
      <label>ID do espaço de trabalho<input v-model="tenant" required maxlength="36" placeholder="ID do tenant"><small>Use o ID informado no cadastro do seu vínculo.</small></label>
      <button class="primary w-full" :disabled="busy">{{ busy ? 'Entrando…' : 'Entrar no Previum →' }}</button>
      <p class="session-note">Por segurança, ao atualizar ou fechar a página você precisará entrar novamente.</p>
    </form></section>
  </div>
</template>
