# Sessão — decisão da Etapa 3

Aprovado pelo proprietário: JWT apenas na memória do Pinia. Nenhum token,
senha ou dado de sessão em localStorage, sessionStorage, cookies ou IndexedDB.
Recarregar/fechar a página exige novo login. A senha é limpa após a tentativa.

O login recebe email, senha e ID do tenant. Após autenticar, o frontend consulta
/auth/me e /tenants/{id}. Trocar tenant exige sair e autenticar novamente.
401 limpa a sessão e redireciona para login; 403, 404, 422 e falhas de conexão
têm mensagens específicas. O prazo do token continua em 1500 minutos/90000 segundos.
Não há renovação automática nem revogação individual: sair remove o token local.

Em produção local, HTML e API compartilham origem (porta 8001). No desenvolvimento,
Vite usa proxy /api para 127.0.0.1:8001. Nenhum segredo do backend vai para o bundle.
