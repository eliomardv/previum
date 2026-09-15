import { test, expect } from '@playwright/test'
import { execFileSync } from 'node:child_process'

function python(code: string, input?: string) {
  return execFileSync('docker', ['compose', 'exec', '-T', 'api', 'python', '-c', code], {
    cwd: '..', encoding: 'utf8', input,
  })
}
test('frontend compilado com API e PostgreSQL reais', async ({ page }, testInfo) => {
  const fixture = JSON.parse(python(`
import json, secrets
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User, Membership
from app.models.tenant import Tenant
with SessionLocal() as db:
    password = secrets.token_urlsafe(32)
    tenant = Tenant(name="Validação temporária frontend")
    user = User(email=secrets.token_hex(12)+"@example.invalid", password_hash=hash_password(password))
    db.add_all([tenant, user]); db.flush()
    db.add(Membership(user_id=user.id, tenant_id=tenant.id))
    result = {"tenant":tenant.id, "user":user.id, "email":user.email, "password":password}
    db.commit()
    print(json.dumps(result))
`))
  try {
    await page.goto('/')
    await page.getByLabel('Email', { exact: true }).fill(fixture.email)
    await page.getByLabel('Senha', { exact: true }).fill(fixture.password)
    await page.getByLabel('ID do espaço de trabalho').fill(fixture.tenant)
    await page.getByRole('button', { name: 'Entrar no Previum' }).click()
    await expect(page.getByRole('heading', { name: 'Visão geral' })).toBeVisible()
    await page.getByRole('link', { name: 'Empresas', exact: true }).click()
    await page.getByRole('button', { name: 'Nova empresa' }).click()
    await page.getByLabel('Nome', { exact: true }).fill('Empresa temporária E2E')
    await page.getByRole('button', { name: 'Salvar cadastro' }).click()
    await expect(page.getByRole('cell', { name: 'Empresa temporária E2E', exact: true })).toBeVisible()
    await page.getByRole('button', { name: 'Editar Empresa temporária E2E' }).click()
    await page.getByLabel('Nome', { exact: true }).fill('Empresa validada E2E')
    await page.getByRole('button', { name: 'Salvar cadastro' }).click()
    await expect(page.getByRole('cell', { name: 'Empresa validada E2E', exact: true })).toBeVisible()
    await page.getByRole('link', { name: 'Trabalhadores', exact: true }).click()
    await page.getByRole('button', { name: 'Novo trabalhador' }).click()
    await page.getByLabel('Nome', { exact: true }).fill('Pessoa temporária E2E')
    await page.getByLabel('Matrícula', { exact: true }).fill('001')
    await page.getByRole('button', { name: 'Salvar cadastro' }).click()
    await expect(page.getByRole('cell', { name: 'Pessoa temporária E2E', exact: true })).toBeVisible()
    await page.getByRole('button', { name: 'Editar Pessoa temporária E2E' }).click()
    await page.getByLabel('Cadastro ativo').uncheck()
    await page.getByRole('button', { name: 'Salvar cadastro' }).click()
    await expect(page.getByText('Inativo', { exact: true })).toBeVisible()
    await page.screenshot({ path: testInfo.outputPath('workers-desktop.png'), fullPage: true })
    await page.setViewportSize({ width: 390, height: 844 })
    await page.screenshot({ path: testInfo.outputPath('workers-mobile.png'), fullPage: true })
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
    await page.reload()
    await expect(page.getByRole('heading', { name: 'Acesse seu espaço' })).toBeVisible()
  } finally {
    python(`
import json, sys
from sqlalchemy import delete
from app.core.database import SessionLocal
from app.models.worker import Worker
from app.models.company import Company
from app.models.user import User, Membership
from app.models.tenant import Tenant
fixture = json.load(sys.stdin)
with SessionLocal() as db:
    for model in (Worker, Company, Membership):
        db.execute(delete(model).where(model.tenant_id == fixture["tenant"]))
    db.execute(delete(User).where(User.id == fixture["user"]))
    db.execute(delete(Tenant).where(Tenant.id == fixture["tenant"]))
    db.commit()
`, JSON.stringify({ tenant: fixture.tenant, user: fixture.user }))
  }
})
