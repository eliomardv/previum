<script setup lang="ts">
import { computed, onMounted, ref, watch, nextTick } from 'vue'
import { useSession } from '../stores/session'
import { message } from '../api'
import { allRecords } from '../data'
import type { Company, Worker } from '../types'
const dialog = ref<HTMLDialogElement | null>(null)
const props = defineProps<{ kind: 'companies' | 'workers' }>()
const session = useSession(), isWorker = computed(() => props.kind === 'workers')
const title = computed(() => isWorker.value ? 'Trabalhadores' : 'Empresas')
const singular = computed(() => isWorker.value ? 'trabalhador' : 'empresa')
const rows = ref<(Company | Worker)[]>([]), companies = ref<Company[]>([])
const loading = ref(false), saving = ref(false), error = ref(''), formError = ref(''), success = ref('')
const offset = ref(0), filter = ref(''), next = ref(false), editing = ref(false), editId = ref('')
watch(editing, async value => {
  await nextTick()
  if (value) dialog.value?.showModal()
  else dialog.value?.close()
})
const name = ref(''), registration = ref(''), companyId = ref(''), active = ref(true)
const base = computed(() => '/' + props.kind)
async function load() {
  loading.value = true; error.value = ''; rows.value = []
  try {
    const query = new URLSearchParams({ offset: String(offset.value), limit: '21' })
    if (isWorker.value && filter.value) query.set('company_id', filter.value)
    const result = await session.api<(Company | Worker)[]>(base.value + '?' + query)
    rows.value = result.slice(0, 20); next.value = result.length > 20
  } catch (err) { error.value = message(err); next.value = false }
  finally { loading.value = false }
}
async function initialize() {
  if (isWorker.value) {
    try { companies.value = await allRecords<Company>(session.api, '/companies') }
    catch (err) { error.value = message(err); return }
  }
  await load()
}
function create() {
  editId.value = ''; name.value = ''; registration.value = ''
  companyId.value = filter.value || companies.value[0]?.id || ''
  active.value = true; formError.value = ''; success.value = ''; editing.value = true
}
async function edit(row: Company | Worker) {
  error.value = ''; success.value = ''
  try {
    const record = await session.api<Company | Worker>(base.value + '/' + encodeURIComponent(row.id))
    editId.value = record.id; name.value = record.name; active.value = record.is_active
    if ('registration' in record) { registration.value = record.registration; companyId.value = record.company_id }
    formError.value = ''; editing.value = true
  } catch (err) { error.value = message(err) }
}
async function save() {
  saving.value = true; formError.value = ''
  const payload = { name: name.value.trim(), is_active: active.value,
    ...(isWorker.value ? { registration: registration.value.trim(), company_id: companyId.value } : {}) }
  try {
    await session.api(base.value + (editId.value ? '/' + encodeURIComponent(editId.value) : ''), {
      method: editId.value ? 'PATCH' : 'POST', body: JSON.stringify(payload),
    })
    editing.value = false; success.value = 'Cadastro salvo com sucesso.'; await load()
  } catch (err) { formError.value = message(err) }
  finally { saving.value = false }
}
function page(direction: number) { offset.value += direction * 20; void load() }
function filtered() { offset.value = 0; void load() }
function companyName(id: string) { return companies.value.find(c => c.id === id)?.name || 'Empresa não disponível' }
onMounted(initialize)
</script>
<template>
  <div class="page-heading"><div><span class="eyebrow">CADASTROS DO SEU ESPAÇO</span><h1>{{ title }}</h1><p class="muted">{{ isWorker ? 'Pessoas, matrículas e vínculos com suas empresas.' : 'Uma base organizada para acompanhar suas empresas.' }}</p></div><button class="primary" @click="create">+ {{ isWorker ? 'Novo trabalhador' : 'Nova empresa' }}</button></div>
  <div v-if="success" class="success" role="status">{{ success }}</div>
  <div v-if="error" class="error" role="alert">{{ error }} <button class="text-link" @click="initialize">Tentar novamente</button></div>
  <section class="panel records-panel">
    <div class="toolbar"><label v-if="isWorker" class="filter-label">Filtrar por empresa<select v-model="filter" :disabled="loading" @change="filtered"><option value="">Todas as empresas</option><option v-for="company in companies" :key="company.id" :value="company.id">{{ company.name }}{{ company.is_active ? '' : ' (inativa)' }}</option></select></label><p v-else class="muted">Empresas ativas e inativas</p><button class="secondary" :disabled="loading" @click="initialize">↻ Atualizar</button></div>
    <p v-if="loading" class="empty" role="status">Carregando cadastros…</p>
    <div v-else-if="!rows.length && !error" class="empty"><h2>Nenhum cadastro nesta página</h2><p>{{ isWorker ? 'Cadastre uma pessoa ou selecione outra empresa.' : 'Adicione uma empresa para começar.' }}</p></div>
    <div v-else-if="rows.length" class="table-wrap"><table><thead><tr><th>Nome</th><th v-if="isWorker">Empresa</th><th v-if="isWorker">Matrícula</th><th>Estado</th><th><span class="sr-only">Ações</span></th></tr></thead><tbody><tr v-for="row in rows" :key="row.id"><td data-label="Nome"><strong>{{ row.name }}</strong></td><td data-label="Empresa" v-if="'company_id' in row">{{ companyName(row.company_id) }}</td><td data-label="Matrícula" v-if="'registration' in row">{{ row.registration }}</td><td data-label="Estado"><span class="badge" :class="{ inactive: !row.is_active }">{{ row.is_active ? 'Ativo' : 'Inativo' }}</span></td><td><button class="text-link" :aria-label="'Editar ' + row.name" @click="edit(row)">Editar →</button></td></tr></tbody></table></div>
    <div class="pagination"><span>Página {{ offset / 20 + 1 }} · {{ rows.length }} registros</span><div><button class="secondary" :disabled="offset === 0 || loading" @click="page(-1)">Anterior</button><button class="secondary" :disabled="!next || loading" @click="page(1)">Próxima</button></div></div>
  </section>
  <dialog ref="dialog" class="editor" aria-labelledby="editor-title" @cancel.prevent="!saving && (editing = false)">
    <form @submit.prevent="save"><div class="section-heading"><h2 id="editor-title">{{ editId ? 'Editar' : 'Cadastrar' }} {{ singular }}</h2><button type="button" class="secondary" :disabled="saving" @click="editing = false">Fechar</button></div>
      <p v-if="formError" class="error" role="alert">{{ formError }}</p>
      <label>Nome<input v-model="name" required maxlength="200" :disabled="saving"></label>
      <template v-if="isWorker"><label>Empresa<select v-model="companyId" required :disabled="saving"><option value="" disabled>Selecione uma empresa</option><option v-for="company in companies" :key="company.id" :value="company.id">{{ company.name }}{{ company.is_active ? '' : ' (inativa)' }}</option></select></label><p v-if="!companies.length" class="muted">Cadastre uma empresa antes de adicionar trabalhadores.</p><label>Matrícula<input v-model="registration" required maxlength="100" :disabled="saving"></label></template>
      <label class="checkbox"><input v-model="active" type="checkbox" :disabled="saving"> Cadastro ativo</label><p class="muted">Ao desativar, o registro continua disponível para consulta.</p>
      <button class="primary w-full" :disabled="saving || (isWorker && !companies.length)">{{ saving ? 'Salvando…' : 'Salvar cadastro' }}</button>
    </form>
  </dialog>

</template>
