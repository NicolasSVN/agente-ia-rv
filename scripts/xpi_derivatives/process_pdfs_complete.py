"""
Script completo para processar os 20 PDFs de derivativos XPI.

Etapas:
1. Extrair diagrama de payoff de cada PDF (página que contém o gráfico)
2. Re-processar com GPT-4 Vision para extrair conteúdo técnico completo
3. Atualizar o derivatives_dataset.py com informações enriquecidas
4. Re-indexar no ChromaDB
"""

import os
import sys
import json
import base64
import io
import time
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from openai import OpenAI
import fitz
from PIL import Image

from core.config import get_settings

settings = get_settings()

PDF_DIR = os.path.join(os.path.dirname(__file__), "pdfs")
DIAGRAMS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "static", "derivatives_diagrams")
VISION_CACHE_DIR = os.path.join(os.path.dirname(__file__), "vision_cache")
ENRICHED_CACHE_DIR = os.path.join(os.path.dirname(__file__), "enriched_cache")

os.makedirs(DIAGRAMS_DIR, exist_ok=True)
os.makedirs(ENRICHED_CACHE_DIR, exist_ok=True)


def extract_diagram_with_vision(pdf_path: str, structure_name: str, slug: str, client: OpenAI) -> Optional[str]:
    """Usa GPT-4 Vision para identificar qual página contém o gráfico de payoff e extrai."""
    try:
        doc = fitz.open(pdf_path)
        zoom = 200 / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        images = []
        for page in doc:
            pix = page.get_pixmap(matrix=matrix)
            images.append(Image.frombytes("RGB", [pix.width, pix.height], pix.samples))
        doc.close()
    except Exception as e:
        print(f"    ERRO ao converter PDF: {e}")
        return None

    diagram_path = os.path.join(DIAGRAMS_DIR, f"{slug}.png")
    
    if os.path.exists(diagram_path):
        print(f"    [SKIP] Diagrama já existe: {slug}.png")
        return diagram_path

    best_page_idx = None
    best_crop = None

    for i, image in enumerate(images):
        buffer = io.BytesIO()
        image.save(buffer, format="PNG", quality=80)
        b64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": (
                            f"Analise esta página {i+1} do PDF da estrutura de derivativos '{structure_name}'.\n\n"
                            "Responda em JSON exato:\n"
                            '{"has_payoff_chart": true/false, "chart_position": {"top_pct": 0-100, "bottom_pct": 0-100, "left_pct": 0-100, "right_pct": 0-100}}\n\n'
                            "has_payoff_chart: true se esta página contém um gráfico de payoff/resultado no vencimento.\n"
                            "chart_position: coordenadas aproximadas do gráfico em porcentagem da página (top=0 é topo).\n"
                            "Se não houver gráfico, use chart_position com valores zeros."
                        )},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_image}", "detail": "high"}}
                    ]
                }],
                max_tokens=200,
                temperature=0.0
            )
            
            result_text = response.choices[0].message.content.strip()
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(result_text)
            
            if result.get("has_payoff_chart"):
                pos = result.get("chart_position", {})
                top = max(0, pos.get("top_pct", 0) - 5)
                bottom = min(100, pos.get("bottom_pct", 100) + 5)
                left = max(0, pos.get("left_pct", 0) - 3)
                right = min(100, pos.get("right_pct", 100) + 3)
                
                w, h = image.size
                crop_box = (
                    int(w * left / 100),
                    int(h * top / 100),
                    int(w * right / 100),
                    int(h * bottom / 100)
                )
                best_page_idx = i
                best_crop = image.crop(crop_box)
                print(f"    Gráfico encontrado na página {i+1} ({top:.0f}%-{bottom:.0f}% vertical)")
                break
                
        except Exception as e:
            print(f"    Erro ao analisar página {i+1}: {e}")
            continue

    if best_crop:
        best_crop.save(diagram_path, "PNG", quality=95)
        print(f"    [OK] Diagrama salvo: {slug}.png")
        return diagram_path
    else:
        if images:
            images[0].save(diagram_path, "PNG", quality=95)
            print(f"    [FALLBACK] Página 1 salva como diagrama: {slug}.png")
            return diagram_path
    
    return None


def process_pdf_comprehensive(pdf_path: str, structure_name: str, slug: str, client: OpenAI) -> Optional[Dict]:
    """Processa PDF completo com GPT-4 Vision e extrai conteúdo técnico estruturado."""
    cache_path = os.path.join(ENRICHED_CACHE_DIR, f"{slug}.json")
    
    if os.path.exists(cache_path):
        print(f"    [CACHE] Conteúdo enriquecido já existe")
        with open(cache_path, "r") as f:
            return json.load(f)
    
    try:
        doc = fitz.open(pdf_path)
        zoom = 150 / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        images = []
        for pg in doc:
            pix = pg.get_pixmap(matrix=matrix)
            images.append(Image.frombytes("RGB", [pix.width, pix.height], pix.samples))
        doc.close()
    except Exception as e:
        print(f"    ERRO ao converter PDF: {e}")
        return None

    all_pages_b64 = []
    for image in images:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG", quality=80)
        all_pages_b64.append(base64.b64encode(buffer.getvalue()).decode("utf-8"))

    content_parts = [{"type": "text", "text": f"""Analise TODAS as páginas deste PDF da estrutura de derivativos "{structure_name}" da XPI.

Extraia TODA a informação e retorne um JSON estruturado com os seguintes campos:

{{
  "nome_completo": "nome oficial da estrutura",
  "descricao_detalhada": "descrição completa e detalhada do funcionamento (mínimo 300 palavras)",
  "objetivo": "qual o objetivo principal desta estrutura",
  "perfil_investidor": "para qual perfil de investidor é indicada",
  "cenario_ideal": "em qual cenário de mercado é mais adequada",
  "componentes": [
    {{"instrumento": "ex: Compra de Call ATM", "descricao": "descrição do componente"}}
  ],
  "como_funciona": "explicação passo a passo de como a estrutura funciona",
  "custo": "informação sobre o custo da operação (zero cost, prêmio, etc)",
  "riscos": "descrição dos riscos envolvidos",
  "ganho_maximo": "qual o ganho máximo possível",
  "perda_maxima": "qual a perda máxima possível",
  "breakeven": "onde está o ponto de equilíbrio",
  "exemplo_numerico": "exemplo com números reais se disponível no PDF",
  "payoff_descricao": "descrição textual detalhada do gráfico de payoff - eixos, zonas de lucro/perda, formato da curva, strikes, barreiras",
  "observacoes": "disclaimers, condições especiais, notas importantes",
  "palavras_chave": ["lista", "de", "termos", "relevantes"]
}}

IMPORTANTE:
- Extraia TUDO que estiver no PDF, cada detalhe conta
- Use português correto com acentuação
- Seja extremamente detalhado na descrição e no como_funciona
- O exemplo numérico deve incluir todos os cenários apresentados no PDF
- Na payoff_descricao, descreva exatamente o que o gráfico mostra"""}]

    for i, b64 in enumerate(all_pages_b64):
        content_parts.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{b64}", "detail": "high"}
        })

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": content_parts}],
            max_tokens=4096,
            temperature=0.1
        )
        
        result_text = response.choices[0].message.content.strip()
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(result_text)
        
        with open(cache_path, "w") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"    [OK] Conteúdo enriquecido extraído ({len(result.get('descricao_detalhada', ''))} chars)")
        return result
        
    except json.JSONDecodeError as e:
        text_cache_path = os.path.join(ENRICHED_CACHE_DIR, f"{slug}_raw.txt")
        with open(text_cache_path, "w") as f:
            f.write(result_text)
        print(f"    [WARN] JSON parse error, texto salvo: {e}")
        return None
    except Exception as e:
        print(f"    ERRO: {e}")
        return None


def main():
    from scripts.xpi_derivatives.derivatives_dataset import get_all_structures

    structures = get_all_structures()
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    print(f"\n{'='*60}")
    print(f"PROCESSAMENTO COMPLETO DOS PDFs DE DERIVATIVOS")
    print(f"{'='*60}")
    
    available_pdfs = {}
    for s in structures:
        pdf_path = os.path.join(PDF_DIR, f"{s['slug']}.pdf")
        if os.path.exists(pdf_path):
            available_pdfs[s['slug']] = pdf_path
    
    print(f"PDFs disponíveis: {len(available_pdfs)}/{len(structures)}")
    missing = [s['name'] for s in structures if s['slug'] not in available_pdfs]
    if missing:
        print(f"Faltando: {', '.join(missing)}")
    
    print(f"\n--- ETAPA 1: Extração de Diagramas de Payoff ---")
    diagram_results = {}
    for s in structures:
        slug = s['slug']
        if slug not in available_pdfs:
            continue
        print(f"\n  [{slug}] {s['name']}")
        diagram_path = extract_diagram_with_vision(
            available_pdfs[slug], s['name'], slug, client
        )
        if diagram_path:
            diagram_results[slug] = diagram_path
        time.sleep(0.5)
    
    print(f"\n  Diagramas extraídos: {len(diagram_results)}/{len(available_pdfs)}")
    
    print(f"\n--- ETAPA 2: Extração de Conteúdo Técnico Completo ---")
    enriched_results = {}
    for s in structures:
        slug = s['slug']
        if slug not in available_pdfs:
            continue
        print(f"\n  [{slug}] {s['name']}")
        enriched = process_pdf_comprehensive(
            available_pdfs[slug], s['name'], slug, client
        )
        if enriched:
            enriched_results[slug] = enriched
        time.sleep(1)
    
    print(f"\n  Conteúdos enriquecidos: {len(enriched_results)}/{len(available_pdfs)}")
    
    print(f"\n{'='*60}")
    print(f"PROCESSAMENTO CONCLUÍDO!")
    print(f"{'='*60}")
    print(f"Diagramas: {len(diagram_results)}")
    print(f"Conteúdos enriquecidos: {len(enriched_results)}")
    print(f"\nPróximos passos:")
    print(f"  1. Rodar: python scripts/xpi_derivatives/update_dataset.py")
    print(f"  2. Rodar: python scripts/xpi_derivatives/ingest_derivatives.py --skip-download")


if __name__ == "__main__":
    main()
