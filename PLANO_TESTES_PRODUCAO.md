# Plano de Testes QA — Agente IA Stevan (Produção)

**URL de Produção:** `https://agente-ia-rv-svn.replit.app`  
**Data:** 26/02/2026  
**Versão:** 1.0 — Entrega Final

---

## Como usar este plano

1. Acesse a URL de produção no browser (Chrome recomendado)
2. Execute cada cenário na ordem sugerida
3. Ao lado de cada teste, anote:
   - **OK** — funcionou como esperado
   - **FALHA** — descreva o que viu de diferente
   - **N/A** — não se aplica (ex: sem dados para testar)
4. Após completar uma seção inteira, me envie os resultados para validação técnica

**Ordem de execução:** Login → Health Check → Insights → Conversas → Testar Agente → Base de Conhecimento → Campanhas → Personalidade IA → Assessores → Usuários → Integrações → Central de Custos → Segurança e Permissões → Testes Transversais

### Dados necessários para testes

Antes de começar, certifique-se de ter:
- **Conta Microsoft corporativa** autorizada no sistema (para login)
- **Um arquivo PDF** de relatório de fundo (para teste de upload na Base de Conhecimento)
- **Um arquivo CSV/Excel** com colunas nome, email, telefone, unidade (para teste de importação de assessores)
- **Um arquivo que NÃO é PDF** (ex: um .txt qualquer) para testar rejeição de upload
- Se possível: **acesso com 2 perfis diferentes** (Admin + Gestão ou Broker) para testar permissões

---

## 1. LOGIN

**Propósito:** Garantir que apenas usuários autorizados via SSO Microsoft acessem o sistema.  
**Pré-condição:** Ter uma conta Microsoft corporativa autorizada.

---

### Teste 1.1 — Tela de login carrega corretamente
**Passo 1:** Abra o browser e acesse `https://agente-ia-rv-svn.replit.app`  
**Passo 2:** Observe a tela que aparece  
**Esperado:** Você vê um card centralizado com:
- Logos SVN e XP no topo
- Título "Agente IA - RV"
- Subtítulo "Painel Administrativo"
- Botão "Entrar com Microsoft" com ícone colorido da Microsoft
- Texto "Acesso restrito a administradores e assessores" abaixo do botão
- Fundo na cor creme/bege (#FFF8F3)

**Resultado:** _______________

---

### Teste 1.2 — Login via SSO Microsoft funciona
**Passo 1:** Na tela de login, clique no botão "Entrar com Microsoft"  
**Passo 2:** Na tela da Microsoft que abrir, faça login com seu email e senha corporativos  
**Passo 3:** Complete a verificação MFA (código no celular) se solicitada  
**Passo 4:** Aguarde o redirecionamento de volta para a aplicação  
**Esperado:** Após autenticar, você é redirecionado automaticamente para a página principal (Insights ou Conversas). A sidebar aparece à esquerda com as opções de menu.

**Resultado:** _______________

---

### Teste 1.3 — Sidebar mostra opções corretas para seu perfil
**Passo 1:** Após o login, observe a sidebar à esquerda  
**Passo 2:** Verifique quais itens de menu aparecem  
**Esperado (se você é Admin):** Vê todas as opções:
- Seção "Operação": Insights, Conversas, Campanhas, Testar Agente
- Seção "Configurações": Assessores, Usuários, Personalidade IA, sub-menu Conhecimento (Produtos, Upload Inteligente, Fila de Revisão, Documentos), Integrações, Custos
- Botão "Sair" no rodapé

**Esperado (se você é Gestão):** Mesmas opções EXCETO "Usuários" e "Integrações"

**Esperado (se você é Broker/Assessor):** Vê apenas "Conversas" e "Sair"

**Resultado:** _______________

---

### Teste 1.4 — Acesso direto sem login é bloqueado
**Passo 1:** Abra uma janela anônima/privada no browser  
**Passo 2:** Cole na barra de endereço: `https://agente-ia-rv-svn.replit.app/conversas`  
**Passo 3:** Pressione Enter  
**Esperado:** Você é redirecionado para a tela de login. NÃO consegue ver a página de Conversas sem estar logado.

**Resultado:** _______________

---

### Teste 1.5 — Logout funciona
**Passo 1:** Estando logado, clique em "Sair" na parte inferior da sidebar  
**Passo 2:** Observe para onde você é redirecionado  
**Esperado:** Você volta para a tela de login. Se tentar acessar qualquer página (ex: `/insights`), é redirecionado de volta ao login.

**Resultado:** _______________

---

### Teste 1.6 — Relogin após logout
**Passo 1:** Após o logout (teste 1.5), clique em "Entrar com Microsoft" novamente  
**Passo 2:** Faça o login  
**Esperado:** Login funciona normalmente, você volta para a página principal. A sessão anterior foi encerrada corretamente.

**Resultado:** _______________

---

## 2. HEALTH CHECK

**Propósito:** Confirmar que todos os serviços críticos (banco de dados, IA, WhatsApp) estão funcionando antes de testar o resto.  
**Pré-condição:** Estar logado.

---

### Teste 2.1 — Health check básico
**Passo 1:** Na barra de endereço do browser, acesse `https://agente-ia-rv-svn.replit.app/health`  
**Esperado:** A página mostra um texto simples: `{"status":"ok"}`. Isso confirma que o servidor está respondendo.

**Resultado:** _______________

---

### Teste 2.2 — Health check detalhado
**Passo 1:** Na barra de endereço, acesse `https://agente-ia-rv-svn.replit.app/api/health/detailed`  
**Passo 2:** Observe o JSON retornado  
**Esperado:** Você vê um JSON com status de cada serviço:
- `database`: deve mostrar "ok" ou "connected"
- `vector_store`: status do pgvector
- `openai`: status da conexão com OpenAI
- `zapi`: status da conexão com Z-API (WhatsApp)
- `pdf_processing`: status do processamento de PDFs

**Resultado:** _______________

---

### Teste 2.3 — Nenhum serviço crítico está falhando
**Passo 1:** No resultado do teste 2.2, verifique se algum serviço mostra "error" ou "disconnected"  
**Esperado:** Todos os serviços mostram status positivo. Se algum mostrar erro, anote QUAL serviço falhou.

**Resultado:** _______________

---

## 3. INSIGHTS (Dashboard Analítico)

**Propósito:** Visão gerencial de performance — volume de interações, taxa de resolução do bot, assessores mais ativos, categorias de dúvidas e tendências. Permite à gestão tomar decisões baseadas em dados.  
**Pré-condição:** Estar logado como Admin ou Gestão.

---

### Teste 3.1 — Página carrega sem erros
**Passo 1:** Na sidebar, clique em "Insights"  
**Passo 2:** Aguarde a página carregar completamente  
**Esperado:** Dashboard carrega mostrando cards de KPI no topo, gráficos abaixo e rankings. Nenhum erro visual ou mensagem de erro aparece. Se não houver dados, os valores aparecem como zero (não como erro).

**Resultado:** _______________

---

### Teste 3.2 — KPIs principais estão visíveis
**Passo 1:** Na página de Insights, observe os cards no topo  
**Passo 2:** Verifique se cada card tem um título e um valor numérico  
**Esperado:** Você vê cards mostrando métricas como: total de interações, assessores ativos, taxa de resolução por IA, tempo médio de resposta. Cada card tem um número (mesmo que zero) e um rótulo descritivo.

**Resultado:** _______________

---

### Teste 3.3 — Gráfico de atividade diária
**Passo 1:** Role a página para baixo até encontrar o gráfico de atividade  
**Passo 2:** Observe se o gráfico renderiza corretamente  
**Esperado:** Gráfico de linha ou barras mostrando o volume de interações ao longo dos dias. Se não há dados, o gráfico aparece vazio mas renderizado (eixos visíveis, sem erro).

**Resultado:** _______________

---

### Teste 3.4 — Rankings de unidades e assessores
**Passo 1:** Na página de Insights, localize as seções de ranking  
**Passo 2:** Verifique se há duas listas: uma de unidades e uma de assessores  
**Esperado:** Lista de unidades mais ativas (com número de interações ao lado) e lista de assessores mais ativos. Se não há dados, aparece estado vazio sem erro.

**Resultado:** _______________

---

### Teste 3.5 — Distribuição de tickets
**Passo 1:** Localize o gráfico tipo donut/pizza de tickets  
**Esperado:** Gráfico mostrando proporção de tickets por status (Novo, Aberto, Resolvido) com cores distintas e legenda.

**Resultado:** _______________

---

### Teste 3.6 — Produtos em tendência
**Passo 1:** Localize a seção de produtos/tickers mais mencionados  
**Esperado:** Lista dos tickers ou produtos mais perguntados nas conversas, com contador de menções. Se nenhum dado, estado vazio sem erro.

**Resultado:** _______________

---

### Teste 3.7 — Feedbacks
**Passo 1:** Localize a seção de feedbacks  
**Esperado:** Lista de feedbacks recebidos sobre respostas do agente, ou estado vazio se não houver.

**Resultado:** _______________

---

### Teste 3.8 — Resumo de campanhas
**Passo 1:** Localize a seção de campanhas no dashboard  
**Esperado:** Resumo de campanhas ativas/recentes com métricas básicas (enviadas, falhas), ou estado vazio.

**Resultado:** _______________

---

## 4. CONVERSAS (Central de Mensagens WhatsApp)

**Propósito:** Interface estilo Zendesk para monitorar e intervir nas conversas do agente via WhatsApp. Permite ver histórico, assumir conversas do bot, filtrar por status/assessor e enviar mensagens.  
**Pré-condição:** Estar logado. Idealmente ter algumas conversas registradas (vindas do WhatsApp).

---

### Teste 4.1 — Página carrega com lista de conversas
**Passo 1:** Na sidebar, clique em "Conversas"  
**Passo 2:** Aguarde o carregamento  
**Esperado:** Painel dividido em duas partes: lista de conversas à esquerda, área de chat à direita. A lista mostra conversas com nome do contato, última mensagem e horário. Se não há conversas, aparece estado vazio.

**Resultado:** _______________

---

### Teste 4.2 — Filtros de status funcionam
**Passo 1:** Na parte superior da lista de conversas, localize os filtros de status  
**Passo 2:** Clique em "Bot Ativo" (ou filtro equivalente)  
**Passo 3:** Depois clique em "Humano"  
**Passo 4:** Depois clique em "Todos" para voltar  
**Esperado:** A lista filtra corretamente — mostrando apenas conversas do status selecionado. Os contadores atualizam.

**Resultado:** _______________

---

### Teste 4.3 — Busca por assessor/contato
**Passo 1:** No campo de busca da lista de conversas, digite o nome de um assessor ou contato  
**Passo 2:** Observe a lista filtrar  
**Esperado:** A lista mostra apenas conversas que correspondem à busca. Ao limpar o campo, todas voltam.

**Resultado:** _______________

---

### Teste 4.4 — Abrir uma conversa e ver histórico
**Passo 1:** Clique em uma conversa na lista à esquerda  
**Passo 2:** Observe o painel direito  
**Esperado:** O histórico de mensagens carrega no painel direito. As mensagens aparecem como bolhas de chat com:
- Mensagens do Bot: estilo visual distinto (ex: fundo diferente)
- Mensagens do Contato: alinhadas de um lado
- Mensagens do Operador Humano: estilo diferenciado
- Cada mensagem tem horário

**Resultado:** _______________

---

### Teste 4.5 — Identificação visual de tipo de mensagem
**Passo 1:** Em uma conversa aberta, observe as bolhas  
**Passo 2:** Identifique mensagens do Bot, do Contato e do Operador (se houver)  
**Esperado:** Cada tipo tem cor/posicionamento diferente, permitindo distinguir facilmente quem enviou cada mensagem.

**Resultado:** _______________

---

### Teste 4.6 — Human takeover (assumir conversa)
**Passo 1:** Abra uma conversa que esteja com status "Bot Ativo"  
**Passo 2:** Localize e clique no botão de assumir/transferir para humano  
**Passo 3:** Observe a mudança de status  
**Esperado:** O status da conversa muda para "Humano". O campo de resposta fica habilitado para digitar. O bot para de responder automaticamente nesta conversa.

**Resultado:** _______________

---

### Teste 4.7 — Enviar mensagem como operador
**Passo 1:** Em uma conversa que você assumiu (teste 4.6), digite uma mensagem no campo de texto  
**Passo 2:** Clique em enviar (ou pressione Enter)  
**Esperado:** A mensagem aparece no chat como mensagem do operador. A mensagem é enviada via WhatsApp ao contato. Toast de confirmação pode aparecer.

**Resultado:** _______________

---

### Teste 4.8 — Badges de status e escalação
**Passo 1:** Na lista de conversas, observe os badges/indicadores  
**Esperado:** Cada conversa mostra:
- Status do ticket: Novo, Aberto ou Resolvido (com cores distintas)
- Nível de escalação: T0 (normal) ou T1 (escalado) com destaque visual para T1

**Resultado:** _______________

---

### Teste 4.9 — Nova conversa
**Passo 1:** Localize o botão de "Nova Conversa" (geralmente no topo ou em destaque)  
**Passo 2:** Clique nele  
**Passo 3:** No modal que abrir, insira um número de telefone válido  
**Passo 4:** Confirme  
**Esperado:** Modal abre solicitando número de telefone. Após confirmar, uma nova conversa é iniciada e aparece na lista.

**Resultado:** _______________

---

### Teste 4.10 — Conversa sem mensagens
**Passo 1:** Se houver uma conversa recém-criada ou vazia, clique nela  
**Esperado:** O painel de chat abre mostrando estado vazio com mensagem orientadora, sem erros.

**Resultado:** _______________

---

## 5. TESTAR AGENTE (Sandbox de Chat)

**Propósito:** Ambiente seguro para testar o comportamento da IA antes de usar no WhatsApp real. Permite validar personalidade, consultas ao RAG, respostas fora do escopo e desambiguação de produtos.  
**Pré-condição:** Estar logado como Admin ou Gestão.

---

### Teste 5.1 — Página carrega com interface de chat
**Passo 1:** Na sidebar, clique em "Testar Agente"  
**Passo 2:** Observe a interface  
**Esperado:** Tela dividida com:
- Chat principal à esquerda: nome "SteVaN" no topo com indicador "Online" (bolinha verde), campo de texto embaixo para digitar
- Sidebar informativa à direita: cards de "Assessor Identificado", "Última Resposta" e "Documentos Consultados"
- Mensagem inicial convidando a testar: "Inicie uma conversa..."

**Resultado:** _______________

---

### Teste 5.2 — Saudação simples
**Passo 1:** No campo de texto do chat, digite: `Olá, tudo bem?`  
**Passo 2:** Clique no botão de enviar (ícone de seta) ou pressione Enter  
**Passo 3:** Aguarde a resposta (indicador de "digitando..." deve aparecer)  
**Esperado:** O agente responde com uma saudação personalizada e amigável, mantendo o tom definido na personalidade. Sua mensagem aparece à direita (verde), a resposta do agente à esquerda (branca). A sidebar direita atualiza mostrando dados da análise (intent, tipo de query).

**Resultado:** _______________

---

### Teste 5.3 — Consulta sobre produto da base (RAG)
**Passo 1:** Digite uma pergunta sobre um produto que você sabe que está na base. Exemplo: `Me fala sobre o [nome de um FII que foi indexado]`  
**Passo 2:** Envie e aguarde a resposta  
**Esperado:** O agente responde com informações específicas do produto, extraídas da base de conhecimento. Na sidebar direita, a seção "Documentos Consultados" mostra os blocos de conteúdo utilizados, com título, score de relevância e preview.

**Resultado:** _______________

---

### Teste 5.4 — Pergunta fora do escopo
**Passo 1:** Digite: `Qual a receita de bolo de chocolate?`  
**Passo 2:** Envie e aguarde  
**Esperado:** O agente responde educadamente que isso está fora do seu escopo de atuação (investimentos/renda variável) e se oferece para ajudar com temas relacionados. NÃO deve inventar uma receita.

**Resultado:** _______________

---

### Teste 5.5 — Consulta de mercado (tempo real)
**Passo 1:** Digite: `Como está o IFIX hoje?` ou `Qual a cotação de HGLG11?`  
**Passo 2:** Envie e aguarde  
**Esperado:** O agente tenta buscar informação em tempo real (via Tavily) ou informa que não tem acesso a cotações em tempo real, sugerindo fontes. NÃO deve inventar números.

**Resultado:** _______________

---

### Teste 5.6 — Sidebar mostra análise da resposta
**Passo 1:** Após enviar qualquer mensagem (testes anteriores), observe a sidebar direita  
**Passo 2:** Verifique o card "Última Resposta"  
**Esperado:** Mostra informações técnicas como:
- Intent detectado (ex: "question", "greeting")
- Tipo de query
- Entidades detectadas
- Criaria ticket? (Sim/Não)
- Mensagens na sessão (contador)

**Resultado:** _______________

---

### Teste 5.7 — Limpar histórico
**Passo 1:** No topo do chat, clique no botão "Limpar" (ícone de lixeira)  
**Passo 2:** Uma confirmação deve aparecer — confirme  
**Esperado:** Todas as mensagens são apagadas. O chat volta ao estado inicial com a mensagem de boas-vindas. A sidebar reseta.

**Resultado:** _______________

---

### Teste 5.8 — Resposta longa e formatada
**Passo 1:** Digite: `Explique detalhadamente o que são FIIs, como funcionam, vantagens e desvantagens`  
**Passo 2:** Envie e aguarde  
**Esperado:** O agente responde com uma explicação completa, bem formatada (parágrafos, possivelmente tópicos). A resposta não é truncada e é legível dentro da bolha de chat.

**Resultado:** _______________

---

## 6. BASE DE CONHECIMENTO (CMS de Produtos)

**Propósito:** Gerenciar a base de dados que alimenta a IA. Aqui se cadastram produtos financeiros, fazem upload de documentos PDF, revisam blocos extraídos pela IA e indexam conteúdo para busca semântica.  
**Pré-condição:** Estar logado como Admin ou Gestão.

---

### 6A — Dashboard de Produtos

### Teste 6A.1 — Dashboard carrega com lista de produtos
**Passo 1:** Na sidebar, dentro de "Conhecimento", clique em "Produtos"  
**Passo 2:** Aguarde o carregamento  
**Esperado:** Dashboard carrega mostrando uma lista/grid de produtos financeiros (FIIs, fundos, etc.) com nome, ticker e status. Campo de busca global visível no topo.

**Resultado:** _______________

---

### Teste 6A.2 — Busca global funciona
**Passo 1:** No campo de busca, digite o nome ou ticker de um produto que existe na base  
**Passo 2:** Observe os resultados  
**Esperado:** A lista filtra mostrando apenas produtos que correspondem à busca. Ao limpar o campo, todos os produtos voltam a aparecer.

**Resultado:** _______________

---

### Teste 6A.3 — Abrir detalhes de um produto
**Passo 1:** Clique em um produto da lista  
**Passo 2:** Observe a página de detalhes  
**Esperado:** Abre uma página com informações detalhadas do produto: nome, ticker, gestora, materiais associados, blocos de conteúdo indexados. Se o produto tem documentos, eles aparecem listados.

**Resultado:** _______________

---

### 6B — Upload Inteligente

### Teste 6B.1 — Tela de upload carrega
**Passo 1:** Na sidebar, dentro de "Conhecimento", clique em "Upload Inteligente"  
**Passo 2:** Observe a interface  
**Esperado:** Área de upload com zona de arrastar e soltar (drag & drop). Instruções sobre tipos de arquivo aceitos (PDF). Possivelmente uma fila de processamento visível abaixo.

**Resultado:** _______________

---

### Teste 6B.2 — Upload de PDF funciona
**Passo 1:** Arraste um arquivo PDF de um relatório de fundo/produto para a zona de upload (ou clique para selecionar)  
**Passo 2:** Selecione o arquivo  
**Passo 3:** Aguarde o upload e início do processamento  
**Esperado:** O arquivo é aceito. Uma barra de progresso ou indicador de status aparece. O processamento inicia em background (extração de metadados via IA). Você pode ver o status na fila de processamento.

**Resultado:** _______________

---

### Teste 6B.3 — Extração automática de metadados
**Passo 1:** Após o upload do teste 6B.2, aguarde o processamento completar (pode levar 1-3 minutos)  
**Passo 2:** Verifique os metadados extraídos  
**Esperado:** O sistema extraiu automaticamente: nome do fundo, ticker, gestora, tipo de documento. Esses dados aparecem associados ao material processado.

**Resultado:** _______________

---

### Teste 6B.4 — Arquivo duplicado é bloqueado
**Passo 1:** Tente subir o MESMO arquivo PDF que já foi processado com sucesso  
**Esperado:** O sistema bloqueia o upload com mensagem indicando que o arquivo já foi processado (detecção por hash do arquivo). NÃO deve aceitar silenciosamente.

**Resultado:** _______________

---

### Teste 6B.5 — Arquivo inválido é rejeitado
**Passo 1:** Tente subir um arquivo que NÃO é PDF (ex: um .txt, .exe, ou um arquivo muito grande >50MB)  
**Esperado:** O sistema rejeita com mensagem de erro clara indicando o motivo (tipo inválido ou tamanho excedido).

**Resultado:** _______________

---

### 6C — Fila de Revisão

### Teste 6C.1 — Fila carrega com blocos pendentes
**Passo 1:** Na sidebar, dentro de "Conhecimento", clique em "Fila de Revisão"  
**Passo 2:** Observe a lista  
**Esperado:** Lista de blocos de conteúdo extraídos pela IA que aguardam revisão humana. Cada bloco mostra: título, conteúdo preview, score de confiança, produto associado. Se não há blocos pendentes, estado vazio sem erro.

**Resultado:** _______________

---

### Teste 6C.2 — Revisar e aprovar um bloco
**Passo 1:** Clique em um bloco pendente para abri-lo  
**Passo 2:** Observe o conteúdo extraído (possivelmente lado a lado com o PDF original)  
**Passo 3:** Se o conteúdo está correto, clique em "Aprovar"  
**Esperado:** O bloco é aprovado. Ele sai da fila de revisão e é indexado automaticamente no RAG (busca semântica). Toast de sucesso aparece.

**Resultado:** _______________

---

### Teste 6C.3 — Editar um bloco antes de aprovar
**Passo 1:** Abra um bloco pendente  
**Passo 2:** Modifique o texto extraído (corrija um erro de OCR, por exemplo)  
**Passo 3:** Clique em "Aprovar" (ou "Salvar e Aprovar")  
**Esperado:** A edição é salva e o bloco aprovado com o conteúdo corrigido.

**Resultado:** _______________

---

### Teste 6C.4 — Rejeitar um bloco
**Passo 1:** Abra um bloco pendente que não presta (conteúdo inútil ou errado)  
**Passo 2:** Clique em "Rejeitar" ou "Excluir"  
**Esperado:** O bloco é removido da fila. Não é indexado no RAG.

**Resultado:** _______________

---

### 6D — Documentos

### Teste 6D.1 — Lista de documentos carrega
**Passo 1:** Na sidebar, dentro de "Conhecimento", clique em "Documentos"  
**Passo 2:** Observe a lista  
**Esperado:** Lista de todos os documentos com: nome, status de processamento (processando, sucesso, erro), data de upload, produto associado.

**Resultado:** _______________

---

### Teste 6D.2 — Re-indexar um documento
**Passo 1:** Localize um documento com status "sucesso"  
**Passo 2:** Clique no botão de re-indexar (ícone de refresh/setas circulares)  
**Esperado:** O reprocessamento inicia. O status muda temporariamente para "processando". Após completar, volta para "sucesso".

**Resultado:** _______________

---

## 7. CAMPANHAS

**Propósito:** Enviar mensagens em massa para assessores via WhatsApp — relatórios, recomendações, materiais de investimento. Usa um wizard de 3 etapas: destinatários → mensagem → revisão e envio.  
**Pré-condição:** Estar logado como Admin ou Gestão. Ter assessores cadastrados. Z-API conectada.

---

### Teste 7.1 — Página carrega com status do Z-API
**Passo 1:** Na sidebar, clique em "Campanhas"  
**Passo 2:** Observe o topo da página  
**Esperado:** Página "Campanhas Ativas" carrega com:
- Título e subtítulo explicativo
- Badge de status do Z-API (mostrando se a conexão WhatsApp está ativa)
- Wizard de 3 etapas visível

**Resultado:** _______________

---

### Teste 7.2 — Etapa 1: Selecionar destinatários da base
**Passo 1:** No campo "Nome da Campanha", digite um nome (ex: "Teste QA")  
**Passo 2:** Selecione a opção "Para uma lista de assessores que vou selecionar"  
**Passo 3:** Na tabela que aparece, marque 2-3 assessores usando os checkboxes  
**Passo 4:** Observe o contador de seleção  
**Esperado:** A tabela de assessores carrega com: checkbox, código, nome, email, WhatsApp, unidade, equipe. O campo de busca e filtros (Unidade, Equipe) funcionam. O contador mostra "X assessores selecionados".

**Resultado:** _______________

---

### Teste 7.3 — Etapa 1 (alternativa): Upload de lista
**Passo 1:** Selecione a opção "Para destinatários em uma base de dados que vou enviar"  
**Passo 2:** Arraste ou selecione um arquivo CSV/Excel com dados de destinatários  
**Esperado:** Arquivo é aceito. Preview mostra o nome do arquivo e quantidade de linhas. Botão "Remover arquivo" disponível.

**Resultado:** _______________

---

### Teste 7.4 — Etapa 2: Construir mensagem
**Passo 1:** Clique em "Próximo" para ir à etapa 2  
**Passo 2:** Preencha o Bloco 1 (Cabeçalho) com um texto de saudação (ex: "Olá {{nome_assessor}}, segue material de hoje:")  
**Passo 3:** Preencha o Bloco 2 (Conteúdo) com o corpo da mensagem  
**Passo 4:** Preencha o Bloco 3 (Rodapé) com assinatura  
**Passo 5:** Clique no botão `{x}` para inserir variáveis  
**Esperado:** Os 3 blocos de texto aceitam digitação. O botão `{x}` abre dropdown com variáveis disponíveis ({{nome_assessor}}, {{unidade}}, etc.). As variáveis são inseridas no texto.

**Resultado:** _______________

---

### Teste 7.5 — Etapa 2: Anexar arquivo
**Passo 1:** Clique em "Anexar Arquivo à Campanha"  
**Passo 2:** Selecione uma imagem ou PDF  
**Esperado:** Arquivo aparece como preview com ícone, nome e tipo. Botão "Remover" disponível.

**Resultado:** _______________

---

### Teste 7.6 — Etapa 3: Revisar e visualizar
**Passo 1:** Clique em "Próximo" para ir à etapa 3  
**Passo 2:** Observe o resumo e a prévia da mensagem  
**Esperado:** Resumo mostra: nome da campanha, quantidade de destinatários. Preview estilo WhatsApp com os 3 blocos coloridos (cabeçalho verde, conteúdo laranja, rodapé azul).

**Resultado:** _______________

---

### Teste 7.7 — Disparar campanha (CUIDADO: envia mensagens reais)
**Passo 1:** Se estiver testando com destinatários reais, confirme que estão cientes  
**Passo 2:** Clique em "Disparar Campanha"  
**Passo 3:** Observe o progresso  
**Esperado:** Barra de progresso aparece com percentual, contadores de enviadas/falhas, e log em tempo real mostrando cada envio. Ao completar, status final é exibido.

**Resultado:** _______________

---

### Teste 7.8 — Histórico de campanhas
**Passo 1:** Role a página até a seção "Histórico" (parte inferior)  
**Esperado:** Tabela com campanhas anteriores mostrando: nome, data, total de assessores, enviadas, falhas, status (badge colorido: verde=Enviada, vermelho=Falha).

**Resultado:** _______________

---

## 8. PERSONALIDADE IA (Agent Brain)

**Propósito:** Configurar dinamicamente o comportamento da IA — personalidade, tom de voz, modelo, criatividade e regras — sem alterar código. Mudanças refletem imediatamente nas conversas WhatsApp.  
**Pré-condição:** Estar logado como Admin ou Gestão.

---

### Teste 8.1 — Página carrega com configuração atual
**Passo 1:** Na sidebar, dentro de "Configurações", clique em "Personalidade IA"  
**Passo 2:** Aguarde o carregamento (pode mostrar spinner brevemente)  
**Esperado:** Página "Painel de Controle do Cérebro do Agente" carrega com cards de configuração:
- "A Alma do Agente" (textarea com personalidade atual)
- "Restrições e Proibições" (textarea com regras)
- "O Motor da Inteligência" (dropdown de modelo)
- "O Termostato da Criatividade" (slider de temperatura)
- "O Limite de Palavras" (campo numérico)
- "Filtro de Números" (dropdown de modo)
- Aviso azul: "Alterações são aplicadas imediatamente"

**Resultado:** _______________

---

### Teste 8.2 — Verificar valores atuais
**Passo 1:** Observe cada campo preenchido  
**Esperado:** Todos os campos mostram os valores configurados atualmente (não estão vazios). O modelo mostra o GPT selecionado, a temperatura mostra um valor entre 0 e 2, o limite de tokens mostra um número.

**Resultado:** _______________

---

### Teste 8.3 — Alterar personalidade e salvar
**Passo 1:** No campo "Personalidade e Regras", adicione uma frase no final (ex: "Sempre termine com 'Conte comigo!'")  
**Passo 2:** Observe que o botão "Salvar Configurações" muda para "Salvar Configurações *" (indica mudança não salva)  
**Passo 3:** Clique em "Salvar Configurações"  
**Esperado:** Toast de sucesso aparece. Ao recarregar a página (F5), a alteração persiste.  
**Passo 4:** Volte e remova a frase adicionada para não afetar o comportamento real.

**Resultado:** _______________

---

### Teste 8.4 — Alterar modelo de IA
**Passo 1:** No dropdown "Modelo de IA", mude de GPT-4o para outro modelo (ex: GPT-4 Turbo)  
**Passo 2:** Salve  
**Passo 3:** Verifique se a mudança persiste após reload  
**Passo 4:** IMPORTANTE: volte o modelo para o original após o teste  
**Esperado:** Modelo alterado e salvo com sucesso.

**Resultado:** _______________

---

### Teste 8.5 — Slider de temperatura funciona
**Passo 1:** Arraste o slider de temperatura para um valor diferente  
**Passo 2:** Observe o valor numérico ao lado atualizando  
**Esperado:** O valor muda conforme arrasta (ex: 0.0 a 2.0). Os rótulos "Objetivo e Previsível" vs. "Criativo e Variado" ajudam a entender o significado.

**Resultado:** _______________

---

### Teste 8.6 — Restaurar padrão
**Passo 1:** Clique no botão "Restaurar Padrão"  
**Esperado:** Os campos voltam aos valores originais/padrão definidos no sistema.

**Resultado:** _______________

---

## 9. ASSESSORES

**Propósito:** Cadastro e gestão dos assessores financeiros que interagem com o agente via WhatsApp. Vincula nome, telefone, unidade e equipe para identificação automática nas conversas.  
**Pré-condição:** Estar logado como Admin ou Gestão.

---

### Teste 9.1 — Lista de assessores carrega
**Passo 1:** Na sidebar, clique em "Assessores"  
**Passo 2:** Observe a tabela  
**Esperado:** Página "Base de Assessores" carrega com:
- Contador total de assessores no subtítulo
- Tabela com colunas: Código, Nome, E-mail, WhatsApp, Unidade, Equipe, Broker, Ações
- Botões no topo: "Campos", "Importar", "Novo Assessor"
- Campo de busca e filtros (Unidade, Equipe, Broker)

**Resultado:** _______________

---

### Teste 9.2 — Busca e filtros funcionam
**Passo 1:** No campo de busca, digite parte do nome de um assessor  
**Passo 2:** A lista filtra em tempo real  
**Passo 3:** Limpe a busca e use o filtro de "Unidade" — selecione uma unidade  
**Passo 4:** A lista mostra apenas assessores daquela unidade  
**Passo 5:** Clique em "Limpar Filtros"  
**Esperado:** Busca por texto e filtros por dropdown funcionam corretamente. "Limpar Filtros" reseta tudo.

**Resultado:** _______________

---

### Teste 9.3 — Criar novo assessor
**Passo 1:** Clique no botão "Novo Assessor"  
**Passo 2:** No formulário que abre, preencha:
- Nome: "Teste QA"
- E-mail: "teste@qa.com"
- Telefone: "5511999999999"
- Unidade: qualquer valor
**Passo 3:** Clique em "Salvar"  
**Esperado:** Modal fecha, toast de sucesso aparece, o assessor "Teste QA" aparece na tabela.

**Resultado:** _______________

---

### Teste 9.4 — Editar assessor
**Passo 1:** Na tabela, localize o assessor "Teste QA" criado no teste anterior  
**Passo 2:** Clique no botão de editar (ícone de lápis na coluna Ações)  
**Passo 3:** Altere o nome para "Teste QA Editado"  
**Passo 4:** Clique em "Salvar"  
**Esperado:** Modal fecha, toast de sucesso, o nome na tabela atualiza para "Teste QA Editado".

**Resultado:** _______________

---

### Teste 9.5 — Excluir assessor
**Passo 1:** Na tabela, localize o assessor "Teste QA Editado"  
**Passo 2:** Clique no botão de excluir (ícone de lixeira na coluna Ações)  
**Passo 3:** Uma confirmação deve aparecer — confirme  
**Esperado:** O assessor é removido da tabela. Toast de confirmação aparece.

**Resultado:** _______________

---

### Teste 9.6 — Importação via planilha
**Passo 1:** Clique no botão "Importar"  
**Passo 2:** No modal, selecione uma planilha Excel/CSV com dados de assessores (colunas: nome, email, telefone, unidade)  
**Passo 3:** O sistema mostra um preview dos dados e mapeamento de colunas  
**Passo 4:** Configure o mapeamento se necessário  
**Passo 5:** Escolha as opções de importação (substituir base ou atualizar existentes)  
**Passo 6:** Confirme a importação  
**Esperado:** Preview mostra os dados corretamente. Após confirmar, os assessores são importados e aparecem na tabela. Toast de sucesso com resumo (X importados, Y atualizados).

**Resultado:** _______________

---

### Teste 9.7 — Campos customizados
**Passo 1:** Clique no botão "Campos" no topo  
**Passo 2:** Observe o que aparece  
**Esperado:** Interface para gerenciar campos extras/customizados que aparecem no formulário de assessores.

**Resultado:** _______________

---

### Teste 9.8 — Mais filtros
**Passo 1:** Clique em "Mais Filtros"  
**Esperado:** Filtros adicionais aparecem (ex: por equipe, broker responsável).

**Resultado:** _______________

---

## 10. USUÁRIOS (Admin)

**Propósito:** Gestão de usuários internos da plataforma. Controla quem acessa o painel e com quais permissões (Admin, Gestão, Broker).  
**Pré-condição:** Estar logado como Admin (esta página é exclusiva para admins).

---

### Teste 10.1 — Página carrega para admin
**Passo 1:** Na sidebar, clique em "Usuários"  
**Passo 2:** Observe a tabela  
**Esperado:** Página "Usuários" carrega com tabela mostrando: Primeiro Nome, Nome Completo, E-mail, Telefone WhatsApp, Função (com badge colorido: Admin=vermelho, Gestão=âmbar, Broker=azul), Ações.

**Resultado:** _______________

---

### Teste 10.2 — Criar novo usuário
**Passo 1:** Clique em "+ Novo Usuário"  
**Passo 2:** Preencha:
- Primeiro Nome: "Teste"
- Nome Completo: "Teste QA Usuario"
- E-mail: "teste.qa@svn.com"
- Telefone: "5511888888888"
- Função: "Broker"
- Nome de Usuário: "testeqa"
- Senha: uma senha qualquer
**Passo 3:** Clique em "Salvar"  
**Esperado:** Modal fecha, toast de sucesso, usuário aparece na tabela com badge "Broker" azul.

**Resultado:** _______________

---

### Teste 10.3 — Editar role de um usuário
**Passo 1:** Localize o usuário "Teste QA Usuario" na tabela  
**Passo 2:** Clique em editar  
**Passo 3:** Mude a Função de "Broker" para "Gestor"  
**Passo 4:** Salve  
**Esperado:** O badge na tabela muda de azul (Broker) para âmbar (Gestão).

**Resultado:** _______________

---

### Teste 10.4 — Excluir usuário de teste
**Passo 1:** Localize o usuário "Teste QA Usuario"  
**Passo 2:** Clique em excluir  
**Passo 3:** Confirme  
**Esperado:** Usuário removido da tabela.

**Resultado:** _______________

---

### Teste 10.5 — Importação em massa
**Passo 1:** Clique em "Importar Base"  
**Passo 2:** Observe o modal de importação  
**Esperado:** Modal com zona de upload, mapeamento de colunas (Primeiro Nome, Nome Completo, E-mail, Telefone, Função), opção "Atualizar registros existentes", e botão de confirmação.

**Resultado:** _______________

---

### Teste 10.6 — Acesso negado para não-admin
**Passo 1:** Se possível, faça login com um usuário de role "Gestão" ou "Broker"  
**Passo 2:** Tente acessar diretamente `https://agente-ia-rv-svn.replit.app/admin`  
**Esperado:** Mensagem "Acesso Negado" com texto "Apenas administradores podem acessar esta página" e link "Voltar ao Início".

**Resultado:** _______________

---

## 11. INTEGRAÇÕES

**Propósito:** Configurar e monitorar conexões com serviços externos (OpenAI para IA, Z-API para WhatsApp, Fontes confiáveis para busca web).  
**Pré-condição:** Estar logado como Admin.

---

### Teste 11.1 — Página lista integrações
**Passo 1:** Na sidebar, clique em "Integrações"  
**Passo 2:** Observe os cards de integração  
**Esperado:** Página mostra cards para:
- **OpenAI**: com campos de configuração e toggle ativo/inativo
- **Z-API**: com campos de instância e token e toggle ativo/inativo
- **Fontes Confiáveis da Web**: lista de domínios permitidos para busca

**Resultado:** _______________

---

### Teste 11.2 — Testar conexão OpenAI
**Passo 1:** No card da OpenAI, clique em "Testar Conexão"  
**Passo 2:** Aguarde (botão muda para "Testando..." com spinner)  
**Esperado:** Resultado aparece abaixo do botão:
- Se conectado: caixa verde com "Sucesso!" e mensagem de confirmação
- Se falhou: caixa vermelha com "Falha:" e o motivo

**Resultado:** _______________

---

### Teste 11.3 — Testar conexão Z-API
**Passo 1:** No card da Z-API, clique em "Testar Conexão"  
**Passo 2:** Aguarde o resultado  
**Esperado:** Mesmo padrão do teste 11.2 — resultado verde (sucesso) ou vermelho (falha) com mensagem.

**Resultado:** _______________

---

### Teste 11.4 — Fontes confiáveis da web
**Passo 1:** Na seção "Fontes Confiáveis", observe a lista de domínios  
**Passo 2:** No campo "Domínio", digite: `exemplo.com.br`  
**Passo 3:** No campo "Nome", digite: "Exemplo Teste"  
**Passo 4:** Clique em "Adicionar"  
**Esperado:** O domínio aparece na lista. Depois, remova-o para não poluir a configuração real.

**Resultado:** _______________

---

## 12. CENTRAL DE CUSTOS

**Propósito:** Monitoramento financeiro de APIs (OpenAI, Tavily) e custos fixos de infraestrutura (Z-API, Replit). Essencial para controle orçamentário e projeção de gastos.  
**Pré-condição:** Estar logado como Admin ou Gestão.

---

### Teste 12.1 — Visão geral carrega
**Passo 1:** Na sidebar, clique em "Custos"  
**Passo 2:** Observe a aba "Visão Geral" (deve ser a aba padrão)  
**Esperado:** KPI cards no topo mostrando:
- Custo total (em BRL e/ou USD)
- Número de chamadas API
- Projeção mensal
Gráfico de evolução de custos abaixo.

**Resultado:** _______________

---

### Teste 12.2 — Filtro por período
**Passo 1:** Localize os botões de período (7 dias, 30 dias, 90 dias, 365 dias)  
**Passo 2:** Clique em "30 dias"  
**Passo 3:** Depois clique em "7 dias"  
**Esperado:** O gráfico e os KPIs atualizam para refletir o período selecionado. O botão ativo fica visualmente destacado.

**Resultado:** _______________

---

### Teste 12.3 — Gráfico de evolução
**Passo 1:** Observe o gráfico de custos diários  
**Esperado:** Gráfico de linha/barra mostrando custos por dia. Se não há dados, gráfico aparece vazio mas renderizado.

**Resultado:** _______________

---

### Teste 12.4 — Detalhamento por serviço
**Passo 1:** Navegue para a aba "Detalhamento" (ou seção de breakdown)  
**Esperado:** Custos separados por tipo de operação: Chat (conversas), Embeddings (indexação), Extração de Documentos (GPT-4V), Busca Web (Tavily). Cada tipo com valor e quantidade de chamadas.

**Resultado:** _______________

---

### Teste 12.5 — Custos fixos
**Passo 1:** Navegue para a aba "Custos Fixos"  
**Esperado:** Lista de custos mensais recorrentes (ex: Z-API, Replit VM) com nome, valor e frequência.

**Resultado:** _______________

---

### Teste 12.6 — Adicionar custo fixo
**Passo 1:** Clique no botão de adicionar custo fixo  
**Passo 2:** Preencha: Nome "Teste QA", Valor "100"  
**Passo 3:** Salve  
**Passo 4:** Verifique que aparece na lista  
**Passo 5:** Remova o custo de teste  
**Esperado:** Custo adicionado e visível na lista. Após remover, desaparece.

**Resultado:** _______________

---

### Teste 12.7 — Tabela de preços
**Passo 1:** Navegue para a aba "Tabela de Preços"  
**Esperado:** Lista de preços unitários por modelo/serviço (ex: GPT-4o input/output por 1K tokens, Whisper por minuto, etc.).

**Resultado:** _______________

---

## 13. TESTES TRANSVERSAIS

**Propósito:** Validar aspectos que afetam TODAS as abas — navegação, identidade visual, notificações e experiência geral.  
**Pré-condição:** Executar estes testes AO LONGO dos demais (observar enquanto testa as outras abas).

---

### Teste 13.1 — Todas as páginas da sidebar carregam
**Passo 1:** Clique em cada item da sidebar, um por um  
**Passo 2:** Para cada item, anote se a página carregou sem erro  
**Esperado:** Todas as páginas carregam sem tela branca, erro 500, ou mensagem "Page not found". Cada página mostra seu conteúdo esperado.

**Resultado (anote falhas):** _______________

---

### Teste 13.2 — Sidebar minimiza e expande
**Passo 1:** Localize o botão de minimizar a sidebar (geralmente um ícone de setas ou hambúrguer)  
**Passo 2:** Clique para minimizar  
**Passo 3:** Observe que a sidebar fica estreita (64px), mostrando apenas ícones  
**Passo 4:** Clique novamente para expandir  
**Passo 5:** A sidebar volta ao tamanho normal (260px) com ícones e textos  
**Passo 6:** Recarregue a página (F5)  
**Esperado:** O estado da sidebar (minimizada ou expandida) persiste após o reload.

**Resultado:** _______________

---

### Teste 13.3 — Identidade visual consistente
**Passo 1:** Ao navegar entre as páginas, observe:
- As cores estão consistentes? (marrom primário #772B21, fundo creme #FFF8F3)
- A fonte é a mesma em todas as páginas? (Inter)
- Os cards têm bordas arredondadas?
- Os botões seguem o mesmo estilo?
**Esperado:** Visual uniforme em todas as abas. Não há páginas com cores, fontes ou estilos destoantes.

**Resultado:** _______________

---

### Teste 13.4 — Toast de sucesso
**Passo 1:** Execute qualquer ação que resulte em sucesso (ex: salvar configuração no Agent Brain, criar assessor)  
**Passo 2:** Observe a notificação que aparece  
**Esperado:** Toast aparece no topo-centro da tela com:
- Fundo branco
- Borda esquerda verde (4px)
- Mensagem de sucesso
- Desaparece automaticamente após alguns segundos
- Cantos arredondados e sombra

**Resultado:** _______________

---

### Teste 13.5 — Toast de erro
**Passo 1:** Tente provocar um erro (ex: tentar salvar formulário sem preencher campo obrigatório, enviar arquivo inválido)  
**Passo 2:** Observe a notificação  
**Esperado:** Toast aparece no topo-centro com borda esquerda vermelha e mensagem de erro clara.

**Resultado:** _______________

---

### Teste 13.6 — URL direta funciona
**Passo 1:** Estando logado, copie a URL de qualquer página (ex: a URL da página de Insights)  
**Passo 2:** Abra uma nova aba  
**Passo 3:** Cole a URL e pressione Enter  
**Esperado:** A página carrega diretamente sem precisar passar pela sidebar. O login é mantido.

**Resultado:** _______________

---

### Teste 13.7 — Botões voltar/avançar do browser
**Passo 1:** Navegue: Insights → Conversas → Campanhas (clicando na sidebar)  
**Passo 2:** Clique no botão "Voltar" do browser  
**Passo 3:** Clique no botão "Avançar" do browser  
**Esperado:** A navegação funciona corretamente — Voltar leva à página anterior, Avançar leva à página seguinte.

**Resultado:** _______________

---

### Teste 13.8 — Performance geral
**Passo 1:** Observe durante todos os testes:
- As páginas carregam em menos de 5 segundos?
- Há travamentos ou delays longos?
- Os gráficos e tabelas renderizam sem atraso perceptível?
**Esperado:** Navegação fluida. Nenhuma página leva mais de 5s para carregar (após o cold start inicial que pode ser mais lento).

**Resultado:** _______________

---

## 14. SEGURANÇA E PERMISSÕES (RBAC)

**Propósito:** Validar que cada perfil de usuário só acessa o que deve. Fundamental para segurança em produção.  
**Pré-condição:** Ter acesso a pelo menos 2 perfis diferentes (Admin + outro). Se só tiver Admin, execute apenas os testes marcados como "Admin only".

---

### Teste 14.1 — Gestão não acessa Usuários
**Passo 1:** Faça login com um usuário de perfil "Gestão"  
**Passo 2:** Na barra de endereço, digite: `https://agente-ia-rv-svn.replit.app/admin`  
**Passo 3:** Pressione Enter  
**Esperado:** Mensagem "Acesso Negado — Apenas administradores podem acessar esta página" com link para voltar ao início. O item "Usuários" NÃO aparece na sidebar para este perfil.

**Resultado:** _______________

---

### Teste 14.2 — Gestão não acessa Integrações
**Passo 1:** Com perfil "Gestão", na barra de endereço digite: `https://agente-ia-rv-svn.replit.app/integrations`  
**Esperado:** Acesso negado ou redirecionamento. O item "Integrações" NÃO aparece na sidebar para este perfil.

**Resultado:** _______________

---

### Teste 14.3 — Broker só vê Conversas
**Passo 1:** Faça login com um usuário de perfil "Broker"  
**Passo 2:** Observe a sidebar  
**Esperado:** Sidebar mostra APENAS "Conversas" e "Sair". Nenhuma outra opção é visível.

**Resultado:** _______________

---

### Teste 14.4 — Broker não acessa páginas restritas via URL
**Passo 1:** Com perfil "Broker", tente acessar diretamente:
- `https://agente-ia-rv-svn.replit.app/insights`
- `https://agente-ia-rv-svn.replit.app/campanhas`
- `https://agente-ia-rv-svn.replit.app/base-conhecimento`
- `https://agente-ia-rv-svn.replit.app/custos`
**Esperado:** Todas as URLs são bloqueadas (acesso negado ou redirecionamento).

**Resultado:** _______________

---

### Teste 14.5 — Sessão expira após inatividade
**Passo 1:** Faça login normalmente  
**Passo 2:** Deixe o browser aberto SEM interagir por pelo menos 60 minutos  
**Passo 3:** Após 60+ minutos, tente clicar em qualquer item da sidebar  
**Esperado:** Você é redirecionado para a tela de login (a sessão expirou). Se der N/A por falta de tempo, anote.

**Resultado:** _______________

---

### Teste 14.6 — Criar assessor com email duplicado
**Passo 1:** Na página de Assessores, crie um assessor com email "teste@duplicado.com"  
**Passo 2:** Após criar com sucesso, tente criar OUTRO assessor com o mesmo email "teste@duplicado.com"  
**Esperado:** O sistema rejeita a duplicata com mensagem de erro clara. NÃO cria dois registros com o mesmo email.  
**Passo 3:** Exclua o assessor de teste após o teste.

**Resultado:** _______________

---

## Resumo Final

| Seção | Qtd | Status |
|-------|-----|--------|
| 1. Login | 6 | ___ |
| 2. Health Check | 3 | ___ |
| 3. Insights | 8 | ___ |
| 4. Conversas | 10 | ___ |
| 5. Testar Agente | 8 | ___ |
| 6. Base de Conhecimento | 12 | ___ |
| 7. Campanhas | 8 | ___ |
| 8. Personalidade IA | 6 | ___ |
| 9. Assessores | 8 | ___ |
| 10. Usuários | 6 | ___ |
| 11. Integrações | 4 | ___ |
| 12. Central de Custos | 7 | ___ |
| 13. Transversais | 8 | ___ |
| 14. Segurança e Permissões | 6 | ___ |
| **TOTAL** | **100** | ___ |

**Após completar cada seção, envie os resultados para validação técnica.**
