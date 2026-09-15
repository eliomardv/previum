<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useSession } from '../stores/session'
import { allRecords } from '../data'
import { message } from '../api'
import type { Company, Worker } from '../types'
const session = useSession()
const companies = ref<Company[]>([]), workers = ref<Worker[]>([])
const loading = ref(true), error = ref('')
async function load() {
  loading.value = true; error.value = ''
  try {
    const [c, w] = await Promise.all([allRecords<Company>(session.api, '/companies'), allRecords<Worker>(session.api, '/workers')])
    companies.value = c; workers.value = w
  } catch (err) { error.value = message(err) }
  finally { loading.value = false }
}
onMounted(load)
</script>
<template>
  <div class="page-heading"><div><span class="eyebrow">SEU DIA, MAIS ORGANIZADO</span><h1>Visão geral</h1><p class="muted">Um olhar sobre as empresas e pessoas do seu espaço.</p></div><button class="secondary" :disabled="loading" @click="load">↻ Atualizar</button></div>
  <div v-if="error" class="error" role="alert">{{ error }}</div>
  <p v-else-if="loading" role="status" class="panel">Carregando informações…</p>
  <template v-else>
    <section class="stats-grid">
      <article class="stat"><span>Empresas cadastradas</span><strong>{{ companies.length }}</strong><small>{{ companies.filter(c => c.is_active).length }} ativas no espaço</small></article>
      <article class="stat"><span>Trabalhadores cadastrados</span><strong>{{ workers.length }}</strong><small>Distribuídos entre suas empresas</small></article>
      <article class="stat accent"><span>Trabalhadores ativos</span><strong>{{ workers.filter(w => w.is_active).length }}</strong><small>Cadastros com estado ativo</small></article>
    </section>
    <section class="panel"><div class="section-heading"><div><h2>Empresas do seu espaço</h2><p class="muted">Acesse os cadastros para manter sua base atualizada.</p></div><RouterLink class="text-link" to="/companies">Ver todas →</RouterLink></div>
      <div v-if="!companies.length" class="empty"><h3>Comece pela primeira empresa</h3><p>Depois, vincule os trabalhadores ao cadastro.</p><RouterLink class="primary" to="/companies">Cadastrar empresa</RouterLink></div>
      <div v-for="company in companies.slice(0, 5)" :key="company.id" class="company-summary"><span class="company-avatar">{{ company.name.slice(0, 1).toUpperCase() }}</span><div><strong>{{ company.name }}</strong><small>{{ workers.filter(w => w.company_id === company.id).length }} trabalhadores cadastrados</small></div><span class="badge" :class="{ inactive: !company.is_active }">{{ company.is_active ? 'Ativa' : 'Inativa' }}</span></div>
    </section>
    <section class="next-card"><div><span class="eyebrow">BASE ORGANIZADA</span><h2>Cada pessoa, na empresa certa.</h2><p>Mantenha nomes, matrículas e vínculos atualizados em um só lugar.</p></div><RouterLink class="secondary" to="/workers">Gerenciar trabalhadores →</RouterLink></section>
  </template>
</template>
