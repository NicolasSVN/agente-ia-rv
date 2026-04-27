#!/usr/bin/env bash
# =============================================================================
# scripts/preflight.sh — checagens obrigatórias antes de `git push`
#
# O que faz:
#   1. Roda a suite anti-captura de estrutura (test_structure_guard.py).
#      Essa suite garante que materiais POP/Collar/Fence/COE NÃO sejam
#      vinculados aos produtos-ação cadastrados (bug histórico #164/#167).
#   2. Roda a suite de unificação de keywords de estrutura
#      (test_structure_keywords_unification.py).
#
# Por que NÃO está no Dockerfile (Task #179, 27/04/2026):
#   - Antes essa suite rodava como `RUN pytest ...` no build do Docker.
#   - Build-time tests são frágeis: travaram a fila de deploys do Railway
#     por 4 dias (15+ commits empilhados sem deploy verde).
#   - Mover para preflight local mantém a garantia sem o risco do build.
#
# Como usar:
#   $ bash scripts/preflight.sh
#
# Configurar como git pre-push hook (recomendado):
#   $ ln -s ../../scripts/preflight.sh .git/hooks/pre-push
#   $ chmod +x .git/hooks/pre-push
# =============================================================================

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> Preflight: rodando suíte de estrutura anti-captura..."
python -m pytest tests/test_structure_guard.py -q

if [ -f tests/test_structure_keywords_unification.py ]; then
  echo "==> Preflight: rodando suíte de unificação de keywords..."
  python -m pytest tests/test_structure_keywords_unification.py -q
fi

echo ""
echo "OK — preflight passou. Pode dar git push com segurança."
