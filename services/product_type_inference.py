"""
Helper centralizado para inferência e normalização de `Product.product_type`.

Compartilhado entre:
- `api/endpoints/products.py` (criação manual e fluxos de auto-criação)
- `scripts/backfill_product_types.py` (migração de dados)
- `scripts/audit_product_types.py` (auditoria)

Mantém uma única fonte de verdade para a heurística, evitando que o conjunto
canônico ou as regras divirjam entre o endpoint e os scripts.

Valores canônicos (sempre em minúsculas, tal como saem do banco/vector store):
  Renda Variável:  acao | etf | bdr | fii
  Fundos:          fundo | fidc
  Renda Fixa:      debenture  (CRI/CRA agrupados aqui para fins de exibição)
  Estruturadas:    estruturada | swap | long & short
  Bolsa/Balcão:    mercado futuro | mercado a termo
  Outros:          joint venture | outro
"""

from __future__ import annotations

import re
from typing import Optional

VALID_PRODUCT_TYPES: set[str] = {
    # Renda Variável — ativos básicos
    "acao",
    "etf",
    "bdr",
    "fii",
    # Fundos
    "fundo",
    "fidc",
    # Renda Fixa / Crédito
    "debenture",
    # Derivativos de opções / estruturadas
    "estruturada",
    # Operações táticas
    "swap",
    "long & short",
    # Derivativos de bolsa / balcão
    "mercado futuro",
    "mercado a termo",
    # Outros veículos
    "joint venture",
    "outro",
}

PRODUCT_TYPE_ALIASES: dict[str, str] = {
    # Ação
    "ação": "acao",
    "acao": "acao",
    "ações": "acao",
    "acoes": "acao",
    "stock": "acao",
    "equity": "acao",
    # ETF
    "etf": "etf",
    "index": "etf",
    # BDR
    "bdr": "bdr",
    "bdrs": "bdr",
    # FII
    "fii": "fii",
    "fundo imobiliário": "fii",
    "fundo imobiliario": "fii",
    "imobiliário": "fii",
    "imobiliario": "fii",
    # Fundos genéricos
    "fundo": "fundo",
    "fundo de investimento": "fundo",
    "multimercado": "fundo",
    "fundo multimercado": "fundo",
    "fundo de renda fixa": "fundo",
    "fia": "fundo",
    "fic-fia": "fundo",
    "fic fia": "fundo",
    # FIDC
    "fidc": "fidc",
    "fundo de direitos creditórios": "fidc",
    "fundo de direitos creditorios": "fidc",
    "direitos creditórios": "fidc",
    "direitos creditorios": "fidc",
    # Renda Fixa / Crédito
    "debênture": "debenture",
    "debenture": "debenture",
    "cri": "debenture",
    "cra": "debenture",
    "lci": "debenture",
    "lca": "debenture",
    # Estruturadas (derivativos de opções)
    "estruturada": "estruturada",
    "estrutura": "estruturada",
    "estruturado": "estruturada",
    "derivativo": "estruturada",
    "pop": "estruturada",
    "collar": "estruturada",
    "coe": "estruturada",
    # Swap / Troca / Rotação — operação de SUBSTITUIÇÃO de ativo (não estratégia simultânea)
    "swap": "swap",
    "troca": "swap",
    "trocar": "swap",
    "rotação": "swap",
    "rotacao": "swap",
    "substituição": "swap",
    "substituicao": "swap",
    "substituir": "swap",
    "rebalanceamento": "swap",
    # Long & Short — estratégia simultânea (comprado num ativo, vendido em outro)
    "long & short": "long & short",
    "long&short": "long & short",
    "long short": "long & short",
    "long-short": "long & short",
    "pair trade": "long & short",
    "pairs trade": "long & short",
    "pairs trading": "long & short",
    "pair trading": "long & short",
    # Mercado Futuro
    "mercado futuro": "mercado futuro",
    "futuro": "mercado futuro",
    "futuros": "mercado futuro",
    # Mercado a Termo
    "mercado a termo": "mercado a termo",
    "a termo": "mercado a termo",
    "termo": "mercado a termo",
    # Joint Venture
    "joint venture": "joint venture",
    "join venture": "joint venture",
    "joint ventures": "joint venture",
    "join ventures": "joint venture",
    # Genérico
    "outro": "outro",
    "outros": "outro",
}

_TICKER_FII_RE = re.compile(r"^[A-Z]{4}1[12]$")
_TICKER_ACAO_RE = re.compile(r"^[A-Z]{4}[3-6]$")
_TICKER_BDR_RE = re.compile(r"^[A-Z]{4}3[45]$")  # ex: AAPL34, MSFT35


def normalize_product_type(value: Optional[str]) -> Optional[str]:
    """Mapeia um valor livre para o conjunto canônico, ou retorna None se não reconhecido."""
    if not value:
        return None
    v = str(value).strip().lower()
    if not v:
        return None
    if v in VALID_PRODUCT_TYPES:
        return v
    return PRODUCT_TYPE_ALIASES.get(v)


def infer_product_type(
    ticker: Optional[str] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> str:
    """
    Infere o `product_type` canônico a partir de ticker/nome/descrição.

    Sempre retorna um valor de `VALID_PRODUCT_TYPES` — recorre a 'outro' como
    fallback explícito quando nenhuma heurística casa.
    """
    t = (ticker or "").strip().upper()
    n = (name or "").strip().lower()
    d = (description or "").strip().lower()
    blob = f"{n} {d}"

    # Override óbvio por nome/descrição antes do padrão de ticker:
    # tickers terminando em 11/12 normalmente são FIIs, mas alguns ETFs
    # também usam esse sufixo (ex.: BOVA11). Confiamos no nome quando há
    # indicação explícita de ETF/Index.
    if re.search(r"\b(etf|index)\b", blob):
        return "etf"

    if t:
        if _TICKER_FII_RE.match(t):
            return "fii"
        if _TICKER_BDR_RE.match(t):
            return "bdr"
        if _TICKER_ACAO_RE.match(t):
            return "acao"

    # FIDC antes de FII: "FIDC Imobiliário" contém "imobiliário" (FII) mas é FIDC.
    if re.search(r"\b(fidc|fundo de direitos credit[oó]rios)\b", blob):
        return "fidc"
    if re.search(r"\b(fii|fundo imobili[áa]rio|imobili[áa]rio)\b", blob):
        return "fii"
    if re.search(r"\b(bdr|bdrs)\b", blob):
        return "bdr"
    if re.search(r"\b(deb[êe]nture|cra|cri|lci|lca)\b", blob):
        return "debenture"

    # Long & Short — checar ANTES de swap para diferenciar estratégia simultânea
    # de recomendação de substituição.
    if re.search(
        r"\b(long[- ]?short|long\s*&\s*short|pair[- ]?trad\w*)\b",
        blob,
    ):
        return "long & short"

    # Swap / Troca / Rotação — operação de substituição de ativo
    if re.search(
        r"\b(swap|troca|trocar|rota[çc][ãa]o|substitui[çc][ãa]o|substituir|"
        r"rebalanceamento)\b",
        blob,
    ):
        return "swap"

    if re.search(r"\b(mercado futuro|contratos? futuros?|dolar futuro|ibov futuro)\b", blob):
        return "mercado futuro"
    if re.search(r"\b(mercado a termo|contrato a termo|termo de ações)\b", blob):
        return "mercado a termo"
    if re.search(r"\b(joint venture|join venture)\b", blob):
        return "joint venture"
    if re.search(r"\b(pop|collar|coe|estruturad\w*|derivativo)\b", blob):
        return "estruturada"
    if re.search(r"\b(fundo|multimercado)\b", blob):
        return "fundo"

    return "outro"


def coerce_product_type(
    raw: Optional[str] = None,
    *,
    ticker: Optional[str] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> str:
    """
    Garante um `product_type` canônico para fluxos de auto-criação.

    1. Se `raw` já for válido (após normalização de alias), usa esse valor.
    2. Caso contrário, infere a partir de ticker/nome/descrição (fallback 'outro').
    """
    norm = normalize_product_type(raw)
    if norm:
        return norm
    return infer_product_type(ticker=ticker, name=name, description=description)
