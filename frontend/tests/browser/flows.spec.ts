import { test, expect } from '@playwright/test'
test('login, cadastro, filtro, edição, expiração e sessão em memória', async ({ page }) => {
  let companies = [{ id: 'c1', tenant_id: 't1', name: 'Empresa Teste', is_active: true }]
  let workers: any[] = []
  let expired = false
  let writeError = 0
  await page.route('**/api/v1/**', async route => {
    const url = new URL(route.request().url()), path = url.pathname
    const method = route.request().method()
    const body = route.request().postDataJSON()
    let result: unknown = {}
    if (expired) return route.fulfill({ status: 401, json: {} })
    if (method === 'PATCH' && writeError) return route.fulfill({ status: writeError, json: {} })
    if (path.endsWith('/auth/login')) result = { access_token: 'synthetic-browser-test', expires_in: 90000 }
    else if (path.endsWith('/auth/me')) result = { user: { id: 'u1', email: 'test@example.com' }, tenant_id: 't1' }
    else if (path.endsWith('/tenants/t1')) result = { id: 't1', name: 'Espaço Teste' }
    else if (path.endsWith('/companies')) {
      if (method === 'POST') { const c = { id: 'c2', tenant_id: 't1', ...body }; companies.push(c); result = c }
      else result = companies
    } else if (path.endsWith('/workers')) {
      if (method === 'POST') { const w = { id: 'w1', tenant_id: 't1', ...body }; workers.push(w); result = w }
      else result = url.searchParams.get('company_id') ? workers.filter(w => w.company_id === url.searchParams.get('company_id')) : workers
    } else if (path.endsWith('/workers/w1')) {
      if (method === 'PATCH') workers[0] = { ...workers[0], ...body }
      result = workers[0]
    }
    await route.fulfill({ json: result })
  })
  await page.goto('/')
  await page.getByLabel('Email', { exact: true }).fill('test@example.com')
  await page.getByLabel('Senha', { exact: true }).fill('synthetic-password')
  await page.getByLabel('ID do espaço de trabalho').fill('t1')
  await page.getByRole('button', { name: 'Entrar no Previum' }).click()
  await expect(page.getByRole('heading', { name: 'Visão geral' })).toBeVisible()
  await page.getByRole('link', { name: 'Empresas', exact: true }).click()
  await page.getByRole('button', { name: 'Nova empresa' }).click()
  await page.getByLabel('Nome', { exact: true }).fill('Segunda empresa')
  await page.getByRole('button', { name: 'Salvar cadastro' }).click()
  await expect(page.getByRole('cell', { name: 'Segunda empresa', exact: true })).toBeVisible()
  await page.getByRole('link', { name: 'Trabalhadores', exact: true }).click()
  await page.getByRole('button', { name: 'Novo trabalhador' }).click()
  await page.getByLabel('Nome', { exact: true }).fill('Ana Teste')
  await page.getByLabel('Matrícula', { exact: true }).fill('001')
  await page.getByRole('button', { name: 'Salvar cadastro' }).click()
  await expect(page.getByRole('cell', { name: 'Ana Teste', exact: true })).toBeVisible()
  await page.getByLabel('Filtrar por empresa').selectOption('c2')
  await expect(page.getByText('Nenhum cadastro nesta página')).toBeVisible()
  await page.getByLabel('Filtrar por empresa').selectOption('c1')
  await page.getByRole('button', { name: 'Editar Ana Teste' }).click()
  await page.getByLabel('Cadastro ativo').uncheck()
  await page.getByRole('button', { name: 'Salvar cadastro' }).click()
  await expect(page.getByText('Inativo', { exact: true })).toBeVisible()
  for (const [status, text] of [[403, 'permissão'], [404, 'não encontrado'], [422, 'campos informados']] as const) {
    await page.getByRole('button', { name: 'Editar Ana Teste' }).click()
    writeError = status
    await page.getByRole('button', { name: 'Salvar cadastro' }).click()
    await expect(page.getByRole('alert')).toContainText(text)
    await page.getByRole('button', { name: 'Fechar', exact: true }).click()
    writeError = 0
  }
  expect(await page.evaluate(() => localStorage.length + sessionStorage.length)).toBe(0)
  expired = true
  await page.getByRole('button', { name: 'Atualizar' }).click()
  await expect(page.getByRole('heading', { name: 'Acesse seu espaço' })).toBeVisible()
  expired = false
  await page.getByLabel('Email', { exact: true }).fill('test@example.com')
  await page.getByLabel('Senha', { exact: true }).fill('synthetic-password')
  await page.getByLabel('ID do espaço de trabalho').fill('t1')
  await page.getByRole('button', { name: 'Entrar no Previum' }).click()
  await expect(page.getByRole('heading', { name: 'Visão geral' })).toBeVisible()
  await page.reload()
  await expect(page.getByRole('heading', { name: 'Acesse seu espaço' })).toBeVisible()
})
test('login informa indisponibilidade e limpa senha', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.route('**/api/v1/auth/login', route => route.fulfill({ status: 503, json: {} }))
  await page.goto('/')
  await page.getByLabel('Email', { exact: true }).fill('test@example.com')
  await page.getByLabel('Senha', { exact: true }).fill('synthetic-password')
  await page.getByLabel('ID do espaço de trabalho').fill('t1')
  await page.getByRole('button', { name: 'Entrar no Previum' }).click()
  await expect(page.getByRole('alert')).toContainText('indisponível')
  await expect(page.getByLabel('Senha', { exact: true })).toHaveValue('')
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
})
