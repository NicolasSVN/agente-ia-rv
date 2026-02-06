"""
Script para re-ingerir as estruturas de derivativos XPI com conteúdo enriquecido dos PDFs.

Combina:
- Dados do derivatives_dataset.py (estrutura base)
- Conteúdo do vision_cache/ (texto extraído via GPT-4 Vision)
- Conteúdo do enriched_cache/ (JSON estruturado com informações detalhadas)
- Diagramas de static/derivatives_diagrams/

O resultado é uma base de conhecimento completa e detalhada sobre cada estrutura.
"""

import os
import sys
import json
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.vector_store import get_vector_store
from services.chunk_enrichment import enrich_metadata
from scripts.xpi_derivatives.derivatives_dataset import GENERAL_CONTENT, TABS, get_all_structures

BASE_DIR = os.path.dirname(__file__)
VISION_CACHE_DIR = os.path.join(BASE_DIR, "vision_cache")
ENRICHED_CACHE_DIR = os.path.join(BASE_DIR, "enriched_cache")
DIAGRAMS_DIR = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), "static", "derivatives_diagrams")

SKIP_ENRICHMENT = True


def safe_enrich(metadata: dict, content: str, product_name: str) -> dict:
    if SKIP_ENRICHMENT:
        metadata["topic"] = "derivativos"
        metadata["concepts"] = json.dumps(["derivativos", "opcoes", "hedge", "estruturas"])
        return metadata
    try:
        return enrich_metadata(
            metadata=metadata, content=content,
            product_name=product_name, product_ticker="",
            block_type="texto", material_type="lamina_tecnica"
        )
    except Exception as e:
        metadata["topic"] = "derivativos"
        metadata["concepts"] = json.dumps(["derivativos", "opcoes", "hedge"])
        return metadata


def build_global_context(structure: dict) -> str:
    parts = ["[CONTEXTO GLOBAL]"]
    parts.append(f"Produto: {structure['name']}")
    parts.append(f"Categoria: Produtos Estruturados - Derivativos")
    parts.append(f"Aba: {structure['tab']} - {structure['tab_description']}")
    parts.append(f"Estratégia: {structure['strategy']}")
    parts.append(f"Tipo: lâmina técnica de derivativos")
    parts.append(f"Fonte: XPI Investimentos")
    return "\n".join(parts)


def split_content(text: str, max_chars: int = 3000) -> list:
    if len(text) <= max_chars:
        return [text]
    chunks = []
    current = ""
    for para in text.split("\n\n"):
        if len(current) + len(para) + 2 > max_chars and current:
            chunks.append(current.strip())
            current = para
        else:
            current += ("\n\n" if current else "") + para
    if current.strip():
        chunks.append(current.strip())
    return chunks if chunks else [text]


def load_enriched_content(slug: str) -> dict:
    path = os.path.join(ENRICHED_CACHE_DIR, f"{slug}.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}


def load_vision_content(slug: str) -> str:
    path = os.path.join(VISION_CACHE_DIR, f"{slug}.txt")
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read()
    return ""


def build_enriched_text(structure: dict, enriched: dict, vision_text: str) -> str:
    parts = []
    
    parts.append(f"# {enriched.get('nome_completo', structure['name'])}")
    parts.append(f"\n## Descrição Detalhada")
    desc = enriched.get("descricao_detalhada", structure["description"])
    parts.append(desc)
    
    if enriched.get("objetivo"):
        parts.append(f"\n## Objetivo")
        parts.append(enriched["objetivo"])
    
    if enriched.get("como_funciona"):
        parts.append(f"\n## Como Funciona")
        parts.append(enriched["como_funciona"])
    
    if enriched.get("componentes"):
        parts.append(f"\n## Componentes da Estrutura")
        for comp in enriched["componentes"]:
            if isinstance(comp, dict):
                parts.append(f"- {comp.get('instrumento', '')}: {comp.get('descricao', '')}")
            elif isinstance(comp, str):
                parts.append(f"- {comp}")
    
    if enriched.get("custo"):
        parts.append(f"\n## Custo")
        parts.append(enriched["custo"])
    
    if enriched.get("cenario_ideal"):
        parts.append(f"\n## Cenário Ideal")
        parts.append(enriched["cenario_ideal"])
    
    if enriched.get("perfil_investidor"):
        parts.append(f"\n## Perfil do Investidor")
        parts.append(enriched["perfil_investidor"])
    
    if enriched.get("riscos"):
        parts.append(f"\n## Riscos")
        parts.append(enriched["riscos"])
    
    if enriched.get("ganho_maximo"):
        parts.append(f"\n## Ganho Máximo")
        parts.append(enriched["ganho_maximo"])
    
    if enriched.get("perda_maxima"):
        parts.append(f"\n## Perda Máxima")
        parts.append(enriched["perda_maxima"])
    
    if enriched.get("breakeven"):
        parts.append(f"\n## Breakeven (Ponto de Equilíbrio)")
        parts.append(enriched["breakeven"])
    
    if enriched.get("exemplo_numerico"):
        parts.append(f"\n## Exemplo Numérico")
        parts.append(enriched["exemplo_numerico"])
    
    if enriched.get("payoff_descricao"):
        parts.append(f"\n## Gráfico de Payoff")
        parts.append(enriched["payoff_descricao"])
    
    if enriched.get("observacoes"):
        parts.append(f"\n## Observações")
        parts.append(enriched["observacoes"])
    
    enriched_text = "\n".join(parts)
    
    if vision_text and len(vision_text) > 200:
        enriched_text += f"\n\n## Conteúdo Técnico Adicional (Lâmina Original)\n{vision_text}"
    
    return enriched_text


def main():
    structures = get_all_structures()
    vector_store = get_vector_store()
    
    print(f"\n{'='*60}")
    print(f"RE-INGESTÃO COMPLETA - DERIVATIVOS XPI")
    print(f"{'='*60}")
    
    print(f"\n--- Limpando chunks antigos de derivativos ---")
    try:
        collection = vector_store.collection
        existing = collection.get(where={"category": "Derivativos"})
        if existing and existing["ids"]:
            old_count = len(existing["ids"])
            for i in range(0, len(existing["ids"]), 100):
                batch = existing["ids"][i:i+100]
                collection.delete(ids=batch)
            print(f"  Removidos {old_count} chunks antigos")
        else:
            print(f"  Nenhum chunk antigo encontrado")
    except Exception as e:
        print(f"  Aviso ao limpar: {e}")
    
    total_indexed = 0
    
    print(f"\n--- Ingerindo conteúdo geral ---")
    for section in GENERAL_CONTENT["sections"]:
        chunk_id = f"derivatives_general_{uuid.uuid4().hex[:8]}"
        context = "[CONTEXTO GLOBAL]\nCategoria: Produtos Estruturados - Derivativos\nTipo: conteúdo geral introdutório\nFonte: XPI Investimentos"
        text = f"{context}\n\n{section['title']}\n\n{section['content']}"
        metadata = {
            "source": "XPI - Produtos Estruturados",
            "title": section["title"],
            "type": "derivatives_general",
            "block_type": "texto",
            "product_name": "Produtos Estruturados XPI",
            "product_ticker": "",
            "gestora": "XPI",
            "category": "Derivativos",
            "material_type": "lamina_tecnica",
            "publish_status": "publicado"
        }
        metadata = safe_enrich(metadata, section["content"], "Produtos Estruturados XPI")
        vector_store.add_document(doc_id=chunk_id, text=text, metadata=metadata)
        total_indexed += 1
    print(f"  {len(GENERAL_CONTENT['sections'])} chunks gerais indexados")
    
    print(f"\n--- Ingerindo conteúdo por aba ---")
    for tab in TABS:
        chunk_id = f"derivatives_tab_{tab['name'].lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}"
        strategies_text = "\n".join([f"- {s['name']}: {s['description']}" for s in tab["strategies"]])
        structures_in_tab = []
        for s in tab["strategies"]:
            for struct in s["structures"]:
                structures_in_tab.append(f"  • {struct['name']}: {struct['description'][:200]}")
        
        text = (
            f"[CONTEXTO GLOBAL]\nCategoria: Produtos Estruturados - Derivativos\n"
            f"Aba: {tab['name']}\nTipo: visão geral da categoria\nFonte: XPI Investimentos\n\n"
            f"Aba: {tab['name']} - Estratégias Disponíveis\n\n"
            f"{tab['description']}\n\nEstratégias:\n{strategies_text}\n\n"
            f"Estruturas:\n" + "\n".join(structures_in_tab)
        )
        metadata = {
            "source": f"XPI - {tab['name']}", "title": f"Derivativos - Aba {tab['name']}",
            "type": "derivatives_tab", "block_type": "texto",
            "product_name": f"Derivativos - {tab['name']}", "product_ticker": "",
            "gestora": "XPI", "category": "Derivativos",
            "material_type": "lamina_tecnica", "publish_status": "publicado", "tab": tab["name"]
        }
        metadata = safe_enrich(metadata, text, f"Derivativos - {tab['name']}")
        vector_store.add_document(doc_id=chunk_id, text=text, metadata=metadata)
        total_indexed += 1
    print(f"  {len(TABS)} chunks de abas indexados")
    
    print(f"\n--- Ingerindo estruturas individuais (enriquecidas) ---")
    for s in structures:
        slug = s["slug"]
        enriched = load_enriched_content(slug)
        vision_text = load_vision_content(slug)
        diagram_path = os.path.join(DIAGRAMS_DIR, f"{slug}.png")
        has_diagram = os.path.exists(diagram_path)
        
        global_context = build_global_context(s)
        enriched_text = build_enriched_text(s, enriched, vision_text)
        full_text = f"{global_context}\n\n{enriched_text}"
        
        chunks = split_content(full_text, max_chars=3000)
        
        for i, chunk_text in enumerate(chunks):
            chunk_id = f"derivatives_{slug}_{i}_{uuid.uuid4().hex[:8]}"
            
            chunk_title = f"{s['name']}"
            if len(chunks) > 1:
                chunk_title += f" (Parte {i+1}/{len(chunks)})"
            
            metadata = {
                "source": f"XPI - {s['name']}",
                "title": chunk_title,
                "type": "derivatives_structure",
                "block_type": "texto",
                "product_name": s["name"],
                "product_ticker": "",
                "gestora": "XPI",
                "category": "Derivativos",
                "material_type": "lamina_tecnica",
                "publish_status": "publicado",
                "tab": s["tab"],
                "strategy": s["strategy"],
                "structure_slug": slug
            }
            
            if has_diagram:
                metadata["diagram_image_path"] = diagram_path
                metadata["has_diagram"] = "true"
            
            if enriched.get("palavras_chave"):
                metadata["keywords"] = json.dumps(enriched["palavras_chave"])
            
            metadata = safe_enrich(metadata, chunk_text, s["name"])
            vector_store.add_document(doc_id=chunk_id, text=chunk_text, metadata=metadata)
            total_indexed += 1
        
        status = "ENRICHED" if enriched else "BASE"
        diag_status = "📊" if has_diagram else "  "
        print(f"  {diag_status} [{status}] {s['name']} - {len(chunks)} chunks")
    
    print(f"\n{'='*60}")
    print(f"RE-INGESTÃO CONCLUÍDA!")
    print(f"{'='*60}")
    print(f"Total de chunks indexados: {total_indexed}")
    
    enriched_count = len([f for f in os.listdir(ENRICHED_CACHE_DIR) if f.endswith('.json')])
    diagram_count = len([f for f in os.listdir(DIAGRAMS_DIR) if f.endswith('.png')])
    print(f"Estruturas com conteúdo enriquecido: {enriched_count}/27")
    print(f"Estruturas com diagrama: {diagram_count}/27")


if __name__ == "__main__":
    main()
