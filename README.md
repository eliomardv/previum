# Previum

Base FastAPI de autenticação multiempresa. Usuários podem ter vínculos com vários tenants; o login seleciona um vínculo ativo. Senhas são armazenadas somente como `password_hash` Argon2id. JWTs HS256 duram 1500 minutos por padrão e incluem `sub`, `tenant_id`, `iat`, `exp`, `jti`, emissor e audiência.

## Executar com Docker Compose

Copie `.env.example` para `.env` apenas se ainda não existir. Preencha `POSTGRES_PASSWORD` e gere `JWT_SECRET_KEY` com `python -c "import secrets; print(secrets.token_urlsafe(48))"`.

```bash
docker compose up -d --build
docker compose exec api alembic current
docker compose exec api python -m app.bootstrap
```

O PostgreSQL 18 cria o usuário e o banco na primeira inicialização do volume. A API aguarda o banco ficar disponível e executa `alembic upgrade head` antes de iniciar. O volume persistente é montado em `/var/lib/postgresql`, conforme a [documentação do PostgreSQL no Docker](https://docs.docker.com/guides/postgresql/). Alterar credenciais no `.env` não altera usuários de um volume já inicializado.

No Windows (Swagger ou pgAdmin), acesse a API em http://localhost:8001/docs e o PostgreSQL em `localhost:5434`. No pgAdmin, informe banco `previum`, usuário `previum_user` (ou os valores configurados) e a senha local, sem compartilhá-la. No WSL, use os mesmos endereços publicados.

Entre containers do Compose, a API acessa `db:5432` e atende em `api:8000`. `localhost` dentro de um container aponta para ele próprio. As portas publicadas padrão são 8001/5434; o volume `postgres_data` foi preservado. Não execute `docker compose down -v`.

### Precedência da conexão

Na execução local, `DATABASE_URL` explícita tem precedência sobre os campos `POSTGRES_*`. Variáveis do processo têm precedência sobre o arquivo `backend/.env`, lido pelo Settings. O `.env` da raiz é usado pelo Compose para interpolação; ele não é carregado automaticamente pelo Settings local. Exporte as variáveis necessárias ou configure um `backend/.env` ignorado pelo Git.

Sem `DATABASE_URL` explícita, havendo `POSTGRES_PASSWORD`, a aplicação usa `SQLAlchemy.URL.create` para escapar caracteres especiais da senha. Sem ambos, usa SQLite de desenvolvimento. No Compose, a API recebe campos separados, com host `db` e porta 5432, e não recebe `DATABASE_URL` do `.env` da raiz. Em uma URL definida manualmente, escape os componentes corretamente e nunca a publique com credenciais.

## Executar a API localmente

Requer Python 3.11+ com venv/pip. Instale `backend/requirements-dev.txt` em um ambiente virtual. Nas variáveis locais, use `POSTGRES_HOST=localhost` e `POSTGRES_PORT=5434`, ou defina `DATABASE_URL` explicitamente (ela tem precedência na execução local). Para SQLite de desenvolvimento, use `DATABASE_URL=sqlite:///./previum.db`.

```bash
cd backend
alembic upgrade head
python -m app.bootstrap
uvicorn app.main:app --reload --port 8001
```

O bootstrap solicita email, nome do tenant e senha sem eco no terminal, e insere o usuário e seu vínculo no banco já migrado. Guarde o ID de tenant exibido. Não existe cadastro público.

## Migrações

A revisão inicial `0001` cria `tenants`, `companies`, `users` e `memberships`, preservando o modelo de usuários com múltiplos vínculos. Cada empresa pertence a um tenant. Os IDs são UUIDs representados como strings, gerados pelos modelos SQLAlchemy.

```bash
docker compose exec api alembic check
docker compose exec api alembic revision --autogenerate -m "descricao"
docker compose exec api alembic upgrade head
```

Crie revisões preferencialmente no ambiente local em `backend`, para que o arquivo fique no repositório; arquivos gerados dentro do container precisam ser copiados para o host. Revise sempre as migrations antes de aplicá-las. Bancos antigos criados por `create_all` precisam de reconciliação do esquema antes de usar esta migration; não marque a revisão como aplicada sem verificar todas as tabelas. A configuração segue o [Alembic](https://alembic.sqlalchemy.org/en/latest/tutorial.html).

## Login e acesso

```bash
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"usuario@example.com","password":"sua-senha","tenant_id":"ID-DO-TENANT"}'

curl http://localhost:8001/api/v1/auth/me \
  -H 'Authorization: Bearer TOKEN-RECEBIDO'

curl http://localhost:8001/api/v1/tenants/ID-DO-TENANT \
  -H 'Authorization: Bearer TOKEN-RECEBIDO'
```

O login recebe JSON e retorna `access_token`, `token_type` e `expires_in` em segundos. Use o botão Authorize em `/docs` para informar o token. `/api/v1/health` é público. `/auth/me` e `/tenants/{tenant_id}` exigem Bearer válido. Falhas de autenticação retornam 401; tenant diferente do selecionado retorna 404.

Cada requisição valida assinatura, algoritmo fixo, claims obrigatórias, expiração, usuário ativo, tenant ativo e vínculo ativo no banco. Desativar ou remover o vínculo bloqueia tokens já emitidos. Novos endpoints de negócio devem usar `CurrentUser` e filtrar consultas por `context.tenant_id`; nunca usar apenas IDs fornecidos pelo cliente. O módulo de trabalhadores oferece cadastro, consulta, atualização e desativação por tenant. Perfis e permissões granulares ainda não foram implementados.

Não há refresh token, logout com revogação individual por `jti` ou recuperação de senha. Após expirar, é necessário novo login. Para implantação pública, configure HTTPS e limitação de tentativas de login no serviço de entrada.

## Testes

Na pasta `backend`, com o ambiente ativado:

```bash
python -m pytest -q
```

Os testes usam SQLite em memória e segredo exclusivo de teste. Cobrem login, hashes, token ausente/inválido/expirado, assinatura e algoritmo incorretos, claims inválidas, acesso cruzado e desativação de vínculos/usuários/tenants.

## Segurança do repositório

`.env` e variantes locais são ignorados; somente `.env.example` deve ser versionado. O Dependabot está configurado em `.github/dependabot.yml` para atualizações semanais das dependências Python após publicação do arquivo na branch padrão.

Secret Scanning, push protection e alertas/atualizações de segurança do Dependabot devem ser conferidos em Settings → Security no GitHub por um administrador. A configuração local não confirma nem altera esses controles remotos.

Referências: [autenticação FastAPI](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/) e [configurações de segurança do GitHub](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-security-and-analysis-settings-for-your-repository).

## Empresas

As rotas exigem Bearer válido e usam exclusivamente o tenant da autenticação.

- `POST /api/v1/companies`: cria uma empresa (201). Corpo: `{"name": "Minha empresa", "is_active": true}`; `is_active` é opcional.
- `GET /api/v1/companies?offset=0&limit=50`: lista somente empresas do tenant, incluindo inativas; limite máximo 100, ordenação por nome e ID.
- `GET /api/v1/companies/{company_id}`: consulta por ID e tenant autenticado; inexistente ou de outro tenant retorna 404. Empresas inativas continuam consultáveis.
- `PATCH /api/v1/companies/{company_id}`: atualiza `name` e/ou `is_active`. Empresa inexistente ou de outro tenant retorna 404.

Nomes devem ter de 1 a 200 caracteres após remover espaços das extremidades. Campos extras, como `tenant_id` e `id`, são rejeitados (422), assim como atualizações vazias ou valores nulos. Qualquer usuário com vínculo ativo pode gerenciar as empresas de seu tenant; não há distinção de perfis administrativos nesta etapa. Nenhuma nova migration é necessária.

## Validação da Etapa 1

- `ACCESS_TOKEN_EXPIRE_MINUTES=1500` permanece no default, Compose e exemplo. A validação exige valor positivo. O token dura 90.000 segundos e o login retorna `expires_in=90000`.
- `GET /api/v1/health` permanece público e retorna `{"status":"ok"}`.
- `GET /api/v1/ready` é público, executa `SELECT 1` e retorna 200 com `{"status":"ok"}` ou 503 com `{"status":"unavailable"}`, sem detalhes da conexão.
- Empresas seguem endpoints → service → repository → SQLAlchemy síncrono. O service controla commit/rollback; erros de negócio são traduzidos em HTTP pelo handler central.
- Desative usando PATCH com `{"is_active":false}`. A listagem continua sendo um array com empresas ativas e inativas. Não há exclusão física nem alteração de schema nesta etapa.

No Swagger, faça login com um vínculo existente, confirme `expires_in`, copie o token em Authorize, crie uma empresa, consulte pelo ID e desative por PATCH. Confirme que continua na listagem. Com um token de outro tenant, a consulta e atualização devem retornar 404.

No pgAdmin conectado pelo Windows a `localhost:5434`, confira o schema `public` e execute somente consultas:

```sql
SELECT 1;
SELECT version_num FROM public.alembic_version;
SELECT id, tenant_id, name, is_active FROM public.companies;
```

Verificação real de migrations (SQLite nos testes não substitui PostgreSQL):

```bash
docker compose exec api alembic current
docker compose exec api alembic check
curl -f http://localhost:8001/api/v1/health
curl -f http://localhost:8001/api/v1/ready
```

A Etapa 2 implementa trabalhadores conforme a seção abaixo.

### Resultado registrado em 15/09/2026

- Baseline: execução em `backend` com `/tmp/previum-venv/bin/python -m pytest -q` interrompida por dois erros de coleta: limite de 60 rejeitava 1500.
- Após as alterações: `cd backend && timeout 120 /tmp/previum-venv/bin/python -m pytest -q`, fora do sandbox: **50 passed, 3 warnings em 19,29 s**. Avisos de depreciação do TestClient/AnyIO e chave sintética do teste de algoritmo inválido.
- Uma tentativa na raiz falhou por importação de `app`; a execução correta é em `backend`. A tentativa no sandbox ficou sem progresso e foi interrompida.
- `docker compose up -d --build --no-deps api`: API local reconstruída; banco e volume preservados.
- `docker compose exec -T api alembic current`: `0001 (head)`.
- `docker compose exec -T api alembic check`: `No new upgrade operations detected.`
- PostgreSQL real: `SELECT 1` retornou 1; `public.alembic_version` retornou 0001.
- HTTP real: health e ready retornaram 200 com status ok na porta 8001.
- Indisponibilidade e rollback foram testados por falhas simuladas na suíte; o banco real não foi parado. A suíte funcional usa SQLite; a validação PostgreSQL realizada cobre conexão e consistência das migrations.

## Etapa 2 — Trabalhadores

A migration `0002` adiciona `public.workers`, com chaves estrangeiras para tenants e empresas e índice por tenant/empresa. Não altera os registros existentes. A API valida o pertencimento da empresa ao tenant antes de criar ou atualizar; os repositórios filtram trabalhadores pelo tenant autenticado.

- `POST /api/v1/workers`: cria (201).
- `GET /api/v1/workers?company_id=ID&offset=0&limit=50`: lista em array, ordenado por nome/ID, incluindo inativos. Filtro de empresa opcional; limite máximo 100.
- `GET /api/v1/workers/{worker_id}`: consulta individual.
- `PATCH /api/v1/workers/{worker_id}`: altera nome, matrícula, empresa e/ou estado ativo. Use `{"is_active":false}` para desativar. Não há exclusão física.

Corpo de criação:

```json
{
  "company_id": "ID-DA-EMPRESA-DO-TENANT",
  "name": "Ana Exemplo",
  "registration": "001",
  "is_active": true
}
```

Nome, matrícula (`registration`) e empresa são obrigatórios na criação. Nome tem até 200 caracteres e matrícula até 100, ambos sem espaços nas extremidades. A matrícula é texto, preservando zeros iniciais; não há regra de unicidade nesta etapa. O estado ativo é independente do estado da empresa: empresas inativas permanecem válidas para vínculo e consulta. Desativar a empresa não desativa trabalhadores automaticamente.

Campos extras, PATCH vazio e valores nulos são rejeitados com 422. Trabalhador ou empresa inexistente/de outro tenant retorna 404, inclusive no filtro da listagem. Sem autenticação ou com vínculo revogado, retorna 401. Qualquer vínculo ativo continua podendo gerenciar registros do próprio tenant. CPF e dados médicos não foram adicionados.

### Validar no Swagger e pgAdmin

1. Abra http://localhost:8001/docs, faça login e use Authorize.
2. Consulte empresas e copie um ID do tenant selecionado.
3. Crie um trabalhador, consulte por ID e filtre a listagem pela empresa.
4. Atualize nome/matrícula ou desative via PATCH. Confirme que permanece consultável.
5. Com token de outro tenant, confirme 404 ao consultar/alterar o trabalhador.
6. No pgAdmin em `localhost:5434`, atualize a árvore de tabelas do schema `public` e consulte:

```sql
SELECT version_num FROM public.alembic_version;
SELECT id, tenant_id, company_id, name, registration, is_active
FROM public.workers ORDER BY name, id;
```

O upgrade é executado ao iniciar a API no Compose. O downgrade de 0002 remove a tabela workers e seus dados; foi reservado aos testes isolados e não deve ser usado no banco com cadastros reais.

Próxima etapa: frontend original Vue 3 com login, tenant, empresas e trabalhadores. Antes de implementá-lo, definir a estratégia de armazenamento do token.

### Resultado da Etapa 2 em 15/09/2026

- Baseline: 50 testes aprovados.
- `cd backend && timeout 120 /tmp/previum-venv/bin/python -m pytest -q`: **80 passed, 3 warnings em 23,68 s**, fora do sandbox. Permanecem os avisos de depreciação e do teste de algoritmo inválido registrados na Etapa 1.
- Migration isolada: upgrade 0001 → 0002, downgrade → 0001 e novo upgrade preservam a empresa de teste. Roundtrip até base e verificação do metadata também passaram.
- `docker compose up -d --build --no-deps api`: API atualizada, mantendo banco, volume e portas 8001/5434.
- `docker compose exec -T api alembic current`: **0002 (head)**.
- `docker compose exec -T api alembic check`: nenhuma operação pendente.
- Service no PostgreSQL real: criação, consulta, filtro por empresa, isolamento entre tenants e desativação aprovados dentro de transação externa revertida. Nenhum trabalhador temporário permaneceu; as duas empresas existentes foram preservadas.
- Readiness real retornou 200 e as quatro operações de workers foram confirmadas no OpenAPI servido pela API.
- `git diff --check`: aprovado. Nenhum commit ou push realizado.

## Etapa 3 — Frontend operacional

Interface original em Vue 3 + TypeScript + Vite + Tailwind + Pinia + Vue Router.
Inclui login, identificação do tenant, dashboard com totais reais, empresas e
trabalhadores com criação, consulta para edição, atualização e desativação.
A listagem tem páginas de 20 registros; trabalhadores podem ser filtrados por empresa.

### Abrir o sistema

Com Docker, execute na raiz:

```bash
docker compose up -d --build --no-deps api
```

Acesse **http://localhost:8001/** no Windows ou WSL. Swagger continua em
http://localhost:8001/docs e PostgreSQL em localhost:5434. Informe email, senha e
ID do tenant do seu vínculo. O botão “Sair / trocar espaço” permite autenticar
outro vínculo. Não há descoberta pública de tenants ou cadastro de usuário.

O build usa Node apenas numa etapa de compilação; a imagem final contém Python
e os arquivos estáticos. Não foi adicionado container permanente. O contexto de
build agora é a raiz, com exclusão de .env, .git, ambientes virtuais e dependências
locais via .dockerignore. A navegação usa URLs com #, preservando /api e /docs.
Nenhuma migration foi necessária; a revisão continua 0002.

### Sessão e erros

Decisão aprovada: token somente na memória, conforme [frontend/SESSION.md](frontend/SESSION.md).
Recarregar ou fechar a página exige novo login. Senha não é persistida e é limpa
após a tentativa. Não são usados localStorage, sessionStorage ou cookies de sessão.
ACCESS_TOKEN_EXPIRE_MINUTES permanece **1500** (90.000 segundos).

401 encerra a sessão local; 403 informa falta de permissão, 404 informa registro
não encontrado, 422 pede correção dos campos. Falhas de conexão e indisponibilidade
mostram erro e permitem nova tentativa. Requisições têm timeout de 15 segundos.
“Sair” não revoga JWT já emitido no servidor, conforme a fundação existente.

### Desenvolvimento e testes

Requer Node.js 22.12+ da série 22 no WSL (ou Node compatível com as dependências).
Na pasta frontend:

```bash
npm ci
npm run dev
npm run build
npm test
npx playwright install chromium
npm run test:e2e
```

Abra http://localhost:5173 no modo dev. O proxy /api encaminha para a API real em
127.0.0.1:8001. O frontend usa apenas caminhos relativos; não precisa de segredos
ou de liberar CORS. Em Linux, Chromium pode exigir bibliotecas do sistema.

`npm run test:e2e` usa respostas controladas exclusivamente nos testes.
`npm run test:live` exige Docker e API atualizada em 8001: cria usuário e tenant
temporários, testa cadastros no PostgreSQL real e remove somente os dados dessa
fixture em finally. Não interrompa esse teste à força, pois a limpeza depende de
sua finalização. Os testes não alteram credenciais dos usuários existentes.

As ferramentas seguem as instalações oficiais de [Vite](https://vite.dev/guide/)
e [Tailwind com Vite](https://tailwindcss.com/docs/installation/using-vite).

### Limites desta etapa

- Dashboard e seletor de empresa percorrem as páginas da API para calcular totais
  e listar opções; bases grandes poderão exigir endpoints de agregação/busca.
- Login continua exigindo o ID do tenant e não possui refresh token.
- Não há perfis administrativos, funcionalidades de cursos ou operações SST nesta interface.
- A estratégia em memória troca persistência de sessão por menor exposição em armazenamento.

Próxima etapa: área de cursos por tenant. Antes de permitir autoria/publicação,
definir papéis e migration que preserve os vínculos sem promover todos a administradores.

### Validação da Etapa 3

- Backend antes/depois da integração: **80 testes aprovados**, com os três avisos já registrados.
- Build TypeScript + Vite no Docker: aprovado. Bundle JavaScript de aproximadamente 113 kB (43 kB gzip).
- `npm ci`: lockfile instalado; auditoria com **0 vulnerabilidades**.
- `npm test`: **8 testes aprovados** (HTTP 401/403/404/422/503, conexão e sessão).
- `npm run test:e2e`: **2 cenários aprovados** no Chromium, cobrindo login, criação,
  filtro, edição/desativação, erros 403/404/422, revogação, reload e login mobile.
- As primeiras tentativas de navegador identificaram bibliotecas faltantes no WSL
  e seletores ambíguos nos testes. As bibliotecas foram extraídas em /tmp e os
  seletores corrigidos; o resultado acima corresponde à reexecução final.
- No ambiente desta execução, Node 22 foi disponibilizado em /tmp e Chromium usou
  `LD_LIBRARY_PATH=/tmp/previum-browser-libs/extracted/usr/lib/x86_64-linux-gnu`.
  Isso é configuração temporária da máquina de validação, não requisito do app.
- Frontend, Swagger, health e readiness reais: HTTP 200.
- Alembic real: `0002 (head)`; `alembic check` sem alterações pendentes.
- `npm run test:live`: **1 cenário aprovado** contra API e PostgreSQL reais,
  com login, criação/edição de empresa, criação/desativação de trabalhador e reload.
  Fixture removida; contagem conferida em **2 empresas e 4 trabalhadores**, sem
  tenant temporário remanescente.
- Conferência visual desktop/mobile realizada; em telas pequenas os registros
  são apresentados como cartões para evitar comprimir nomes e ações.
- Arquivos desta etapa: `frontend/`, `backend/app/main.py`,
  `backend/Dockerfile`, `docker-compose.yml`, `.dockerignore`, `.gitignore`
  e este README. Nenhum commit, push ou publicação externa.
