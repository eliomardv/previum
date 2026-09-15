<script setup lang="ts">
import { watch } from 'vue'
import { useSession } from './stores/session'
import { router } from './router'
const session = useSession()
watch(() => session.token, token => { if (!token) void router.replace('/login') })
function leave() { session.logout(); void router.replace('/login') }
</script>

<template>
  <div v-if="session.token && $route.path !== '/login'" class="app-shell">
    <aside class="sidebar">
      <RouterLink class="brand" to="/"><span class="brand-mark">P</span>previum<span class="brand-dot">.</span></RouterLink>
      <p class="nav-label">ESPAÇO DE TRABALHO</p>
      <nav aria-label="Navegação principal">
        <RouterLink to="/" exact-active-class="selected"><span aria-hidden="true">◫</span> Visão geral</RouterLink>
        <RouterLink to="/companies" active-class="selected"><span aria-hidden="true">▦</span> Empresas</RouterLink>
        <RouterLink to="/workers" active-class="selected"><span aria-hidden="true">♙</span> Trabalhadores</RouterLink>
      </nav>
      <div class="sidebar-bottom"><span class="eyebrow">GESTÃO SST</span><p>Organização para cuidar<br>de quem trabalha.</p><small>Previum · Espaço conectado</small></div>
    </aside>
    <div class="workspace">
      <header class="topbar"><div><span class="status-dot"></span><strong>{{ session.tenant?.name || 'Carregando espaço…' }}</strong><small>Seu espaço de trabalho</small></div><div class="account"><span>{{ session.identity?.user.email }}</span><button class="secondary" @click="leave">Sair / trocar espaço</button></div></header>
      <main><RouterView :key="$route.path" /></main>
      <footer>Previum <span>Gestão de empresas e pessoas</span></footer>
    </div>
  </div>
  <RouterView v-else />
</template>
