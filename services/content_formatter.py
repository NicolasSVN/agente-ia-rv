import json
from typing import Optional


def format_tabular_content(raw_content: str) -> Optional[str]:
    """
    Converte conteúdo JSON tabular de content_blocks para texto legível.
    
    Input: '{"headers": ["Ativo", "Dív. Bruta"], "rows": [["60.414.500.000", "20.015.300.000"]]}'
    Output: 'Ativo: 60.414.500.000 | Dív. Bruta: 20.015.300.000'
    
    Retorna None se não for JSON tabular válido.
    """
    if not raw_content or not raw_content.strip().startswith("{"):
        return None
    
    try:
        data = json.loads(raw_content)
    except (json.JSONDecodeError, TypeError):
        return None
    
    if not isinstance(data, dict):
        return None
    
    headers = data.get("headers", [])
    rows = data.get("rows", [])
    
    if not rows:
        return None
    
    lines = []
    
    for row in rows:
        if not isinstance(row, list):
            continue
        
        if headers and len(headers) >= 1:
            pairs = []
            for j, val in enumerate(row):
                if val is None or str(val).strip() == "":
                    continue
                if j < len(headers):
                    pairs.append(f"{headers[j]}: {val}")
                else:
                    pairs.append(str(val))
            if pairs:
                lines.append(" | ".join(pairs))
        else:
            non_empty = [str(v) for v in row if v is not None and str(v).strip()]
            if non_empty:
                lines.append(" | ".join(non_empty))
    
    return "\n".join(lines) if lines else None


def get_rich_content(content_block_content: str, fallback_content: str, max_chars: int = 800) -> str:
    """
    Retorna conteúdo rico para o contexto do modelo.
    Se o content_block original for JSON tabular, converte para texto legível.
    Caso contrário, usa o fallback (conteúdo do embedding).
    """
    formatted = format_tabular_content(content_block_content)
    if formatted:
        return formatted[:max_chars]
    
    if content_block_content and not content_block_content.strip().startswith("[CONTEXTO GLOBAL]"):
        return content_block_content[:max_chars]
    
    return fallback_content[:max_chars]
