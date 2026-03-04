# INSTRUÇÕES PARA IA - REPLIT AGENT

## 🎯 OBJETIVO
Manter o repositório GitHub limpo, contendo apenas código recente e útil. O servidor Railway puxa diretamente do GitHub, então tudo que está lá deve estar funcional e necessário.

---

## ⚡ TAREFA IMEDIATA (EXECUTAR AGORA)

### FASE 1: LIMPEZA GERAL DO PROJETO

Execute estes comandos para limpar o projeto completamente:

```bash
# 1. Deletar arquivos legados
rm -f *.legacy *.old *.backup
rm -f migrate_chroma_to_pgvector.py.legacy
find . -type f \( -name "*.legacy" -o -name "*.old" -o -name "*.backup" \) -delete

# 2. Deletar arquivos temporários
rm -f sed* cookies.txt skills-lock.json *.tmp *.swp *.swo

# 3. Deletar DUPLICATA CRÍTICA
rm -rf static/react-conversations/

# 4. Deletar relatórios de teste
find tests/ -type d -name "reports" -exec rm -rf {} + 2>/dev/null || true
find tests/ -name "*.json" -path "*/reports/*" -delete 2>/dev/null || true

# 5. Verificar o que foi deletado
git status
```

### FASE 2: VERIFICAR BUILDS REACT

```bash
# Verificar se builds React estão no repo
git ls-files | grep "frontend.*dist"

# Se retornar VAZIO, executar:
cd frontend/react-conversations
npm install
npm run build
cd ../..
git add frontend/react-conversations/dist/
```

### FASE 3: CONFIGURAR .env.example

```bash
# Se .env.example NÃO existir, criar:
cp .env .env.example

# Abrir .env.example e substituir valores sensíveis por placeholders
# Exemplo:
# De:   OPENAI_API_KEY=sk-proj-abc123...
# Para: OPENAI_API_KEY=sk-proj-...
```

### FASE 4: ATUALIZAR .gitignore

Verificar se `.gitignore` tem estas linhas:

```gitignore
# Python
__pycache__/
*.py[cod]
.venv/
*.egg-info/

# Node
node_modules/
npm-debug.log*

# ⚠️ IMPORTANTE: NÃO incluir dist/ aqui!
# Os builds React DEVEM estar no repo

# Environment
.env
.env.local

# Database
*.db
*.sqlite
backup_*.sql

# Temporários
sed*
*.tmp
*.swp
cookies.txt
skills-lock.json

# Testes
tests/**/reports/
coverage/
.pytest_cache/
.coverage

# IDE/OS
.vscode/
.idea/
.DS_Store

# Replit
.replit
replit.nix
.config/
```

**ATENÇÃO:** Se `.gitignore` tiver linhas como `dist/`, `*/dist/`, ou `frontend/*/dist/`, DELETAR essas linhas!

### FASE 5: COMMIT E PUSH

```bash
# Adicionar todas as mudanças
git add .

# Verificar status final
git status

# Commit
git commit -m "clean: remove legacy code, duplicates, and temporary files"

# Push para GitHub
git push origin main
```

---

## 🔄 REGRAS PERMANENTES (SEGUIR SEMPRE)

### ❌ NUNCA FAÇA:

1. **Criar arquivos com extensões legadas:**
   - ❌ `.legacy`
   - ❌ `.old`
   - ❌ `.backup`
   - ❌ `.bak`

2. **Criar pastas de backup/duplicatas:**
   - ❌ `backup/`, `old/`, `deprecated/`
   - ❌ `static/react-conversations/` (duplicata de `frontend/react-conversations/dist/`)

3. **Deixar arquivos temporários:**
   - ❌ `sed*` (arquivos do comando sed)
   - ❌ `cookies.txt`
   - ❌ `skills-lock.json`
   - ❌ `*.tmp`, `*.swp`

4. **Versionar relatórios de teste:**
   - ❌ `tests/**/reports/*.json`
   - ❌ `coverage/`
   - ❌ `.coverage`

5. **Adicionar `dist/` ao .gitignore:**
   - ❌ Builds React DEVEM estar no repo
   - ❌ Docker é Python-only, não compila React

6. **Versionar .env:**
   - ❌ `.env` tem segredos, nunca commitar

### ✅ SEMPRE FAÇA:

1. **Ao modificar código existente:**
   - Delete a versão antiga completamente
   - NÃO renomeie para `.old` ou `.legacy`
   - Git guarda o histórico automaticamente

2. **Ao criar arquivos temporários (se necessário):**
   - Use `/tmp/` ou `*.tmp`
   - Delete IMEDIATAMENTE após uso
   - Nunca commite temporários

3. **Ao mudar frontend React:**
   ```bash
   cd frontend/react-conversations
   npm run build
   cd ../..
   git add frontend/react-conversations/dist/
   git commit -m "build: update React after UI changes"
   ```

4. **Ao adicionar nova variável de ambiente:**
   - Adicione em `.env` (valor real)
   - Adicione em `.env.example` (placeholder)
   - Exemplo: `NOVA_API_KEY=sua-chave-aqui`

5. **Antes de cada commit:**
   - Verifique que builds React estão trackeados: `git ls-files | grep "frontend.*dist"`
   - Verifique que não há duplicatas: `git ls-files | grep "static/react-conversations"` (deve retornar vazio)
   - Verifique que não há lixo: `git ls-files | grep -E "\.legacy|sed[0-9]|\.tmp"`

6. **Ao deletar código não usado:**
   - Delete o arquivo/pasta completamente
   - `git rm arquivo.py` ou `rm arquivo.py && git add .`
   - Commit com mensagem: `clean: remove unused XYZ`

---

## 🏗️ ARQUITETURA DO PROJETO (CONTEXTO)

**Stack:**
- Backend: Python 3.12 (Flask/FastAPI)
- Frontend: React (Vite)
- Deploy: Railway com Docker Python-only

**Fluxo de deploy:**
1. Código vai para GitHub
2. Railway clona o repo
3. Dockerfile Python copia builds React pré-compilados
4. Backend serve arquivos estáticos do `dist/`

**IMPORTANTE:**
- Docker NÃO tem Node.js instalado
- Builds React são compilados NO REPLIT, não no servidor
- Por isso `dist/` DEVE estar no repositório

---

## 🔍 VERIFICAÇÕES AUTOMÁTICAS

Antes de qualquer commit, execute mentalmente estas verificações:

```bash
# 1. Builds React no repo?
git ls-files | grep "frontend.*dist"
# ✅ Deve retornar arquivos! Se vazio = ERRO

# 2. Sem duplicatas?
git ls-files | grep "static/react-conversations"
# ✅ Deve retornar vazio!

# 3. Sem lixo?
git ls-files | grep -E "\.legacy|sed[0-9]|cookies\.txt"
# ✅ Deve retornar vazio!

# 4. .env protegido?
git ls-files | grep "^\.env$"
# ✅ Deve retornar vazio!

# 5. .env.example existe?
ls .env.example
# ✅ Deve existir!
```

---

## 🚨 SITUAÇÕES ESPECIAIS

### Se encontrar código duplicado:
```bash
# Identifique qual é a versão correta (mais recente)
# Delete a versão antiga
rm arquivo_antigo.py
git add .
git commit -m "clean: remove duplicate code"
```

### Se encontrar pasta `static/react-conversations/`:
```bash
# Esta é SEMPRE uma duplicata
rm -rf static/react-conversations/
git add .
git commit -m "fix: remove duplicate React build folder"
```

### Se precisar recompilar React:
```bash
cd frontend/react-conversations
npm run build
cd ../..
git add frontend/react-conversations/dist/
git commit -m "build: recompile React frontend"
```

### Se .gitignore estiver ignorando `dist/`:
```bash
# Edite .gitignore e remova linhas com dist/
# Depois:
git add -f frontend/react-conversations/dist/
git commit -m "fix: include React builds in repo"
```

---

## 📝 MENSAGENS DE COMMIT

Use mensagens claras seguindo este padrão:

```bash
# Limpeza
git commit -m "clean: remove legacy code and temporary files"
git commit -m "clean: remove duplicate static/react-conversations"

# Build
git commit -m "build: update React after UI changes"

# Correção
git commit -m "fix: include React builds in repository"
git commit -m "fix: correct .gitignore to allow dist/ folder"

# Documentação
git commit -m "docs: update .env.example with new variables"

# Feature
git commit -m "feat: add new API endpoint for XYZ"
```

---

## 💬 QUANDO PEDIR AJUDA HUMANA

Peça intervenção do humano se:

1. **Não conseguir determinar qual versão de código é a correta**
   - "Encontrei `app.py` e `app_v2.py`. Qual devo manter?"

2. **Encontrar arquivos grandes (>10MB) para deletar**
   - "Encontrei `database_backup.sql` (15MB). Posso deletar?"

3. **Mudanças afetam configuração de produção**
   - "Preciso mudar variável de ambiente X. Isso afeta produção?"

4. **Build React falhar**
   - "npm run build falhou com erro Y. Preciso de ajuda."

5. **Git conflitos complexos**
   - "Há conflitos de merge. Como resolver?"

---

## ✅ CHECKLIST DE SUCESSO

Após executar a limpeza inicial, o repositório deve estar assim:

```
✅ Sem arquivos .legacy, .old, .backup
✅ Sem sed*, cookies.txt, skills-lock.json
✅ Sem static/react-conversations/ (duplicata)
✅ Sem tests/**/reports/*.json
✅ frontend/react-conversations/dist/ EXISTE e está trackeado
✅ .env NÃO está trackeado
✅ .env.example EXISTE e está atualizado
✅ .gitignore NÃO ignora dist/
✅ git status mostra working tree limpo
```

---

## 🎯 RESUMO EXECUTIVO

**FAÇA AGORA (primeira vez):**
1. Delete lixo: `.legacy`, `sed*`, `static/react-conversations/`, reports
2. Verifique builds React estão no repo
3. Crie `.env.example`
4. Corrija `.gitignore` (não ignorar `dist/`)
5. Commit + push

**FAÇA SEMPRE (rotina):**
1. Ao mudar código: delete versão antiga, não renomeie
2. Ao mudar frontend: rebuild React + commit `dist/`
3. Antes de commit: verifique builds, duplicatas, lixo
4. Use mensagens de commit claras
5. Peça ajuda se incerto

**NUNCA FAÇA:**
1. Criar arquivos `.legacy/.old/.backup`
2. Deixar temporários (`sed*`, `*.tmp`)
3. Duplicar código/pastas
4. Adicionar `dist/` ao `.gitignore`
5. Commitar `.env`

---

**Versão:** 1.0 - Instruções para Replit Agent
**Data:** 2026-03-04
**Projeto:** Python Backend + React Frontend (builds pré-compilados)