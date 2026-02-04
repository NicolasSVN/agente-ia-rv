"""
Serviço de extração inteligente de metadados de documentos financeiros.
Usa GPT-4 Vision para analisar múltiplas páginas e extrair:
- Nome do fundo/produto
- Ticker (ex: MANA11, XPML11)
- Gestora (ex: TG Core, Manatí, XP)
- Tipo de documento
"""
import os
import re
import json
import base64
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
import unicodedata

import fitz
from openai import OpenAI


@dataclass
class ExtractionResult:
    """Resultado da extração de metadados."""
    fund_name: Optional[str] = None
    ticker: Optional[str] = None
    gestora: Optional[str] = None
    document_type: Optional[str] = None
    confidence: float = 0.0
    source_pages: List[int] = None
    raw_extraction: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.source_pages is None:
            self.source_pages = []
        if self.raw_extraction is None:
            self.raw_extraction = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


KNOWN_GESTORAS = [
    "TG Core", "TG Core Asset Management", "TGCORE",
    "Manatí", "Manati", "Manatí Gestora", "Manatí Capital",
    "XP Asset", "XP Investimentos", "XP Asset Management",
    "BTG Pactual", "BTG", "BTG Asset Management",
    "Kinea", "Kinea Investimentos",
    "Vinci Partners", "Vinci",
    "Brasil Plural", "Plural",
    "RBR Asset", "RBR",
    "HSI", "Hemisfério Sul",
    "Capitânia", "Capitania",
    "VBI Real Estate", "VBI",
    "CSHG", "Credit Suisse Hedging-Griffo",
    "Hedge Investments",
    "Patria Investimentos", "Patria",
    "Iridium", "Iridium Gestão",
    "Mérito", "Merito Investimentos",
    "Guardian", "Guardian Gestora",
    "Galapagos", "Galapagos Capital",
    "Valora", "Valora Gestão",
    "Sparta", "Sparta Gestão",
    "Rio Bravo", "Rio Bravo Investimentos",
    "Bluemacaw", "Blue Macaw",
    "More Invest", "More Gestora",
    "Alianza", "Alianza Trust",
]

TICKER_PATTERN = re.compile(r'\b([A-Z]{4})(11|12|13)\b')

DOCUMENT_TYPE_KEYWORDS = {
    "material_publicitario": ["material publicitário", "material de divulgação", "oferta pública"],
    "relatorio_gerencial": ["relatório gerencial", "report mensal", "informe mensal", "relatório mensal"],
    "prospecto": ["prospecto", "prospectus"],
    "lamina": ["lâmina", "lamina informativa", "informativo"],
    "regulamento": ["regulamento", "regulation"],
    "fato_relevante": ["fato relevante", "comunicado"],
    "apresentacao": ["apresentação institucional", "apresentação do fundo", "investor presentation"],
}


def normalize_text(text: str) -> str:
    """Remove acentos e normaliza texto para comparação."""
    if not text:
        return ""
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


def extract_pages_as_images(pdf_path: str, pages: List[int], max_size: int = 1024) -> List[Tuple[int, str]]:
    """Extrai páginas do PDF como imagens base64."""
    results = []
    
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        for page_num in pages:
            if page_num < 0 or page_num >= total_pages:
                continue
            
            page = doc[page_num]
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat)
            
            if pix.width > max_size or pix.height > max_size:
                scale = max_size / max(pix.width, pix.height)
                mat = fitz.Matrix(scale * 2.0, scale * 2.0)
                pix = page.get_pixmap(matrix=mat)
            
            img_bytes = pix.tobytes("jpeg")
            b64 = base64.b64encode(img_bytes).decode('utf-8')
            results.append((page_num + 1, b64))
        
        doc.close()
    except Exception as e:
        print(f"[MetadataExtractor] Erro ao extrair páginas: {e}")
    
    return results


def find_ticker_in_text(text: str) -> Optional[str]:
    """Busca ticker no texto usando regex."""
    matches = TICKER_PATTERN.findall(text)
    if matches:
        return f"{matches[0][0]}{matches[0][1]}"
    return None


def find_gestora_in_text(text: str) -> Optional[str]:
    """Busca gestora conhecida no texto."""
    text_normalized = normalize_text(text)
    
    for gestora in KNOWN_GESTORAS:
        gestora_normalized = normalize_text(gestora)
        if gestora_normalized in text_normalized:
            return gestora
    
    return None


def detect_document_type(text: str) -> Optional[str]:
    """Detecta tipo de documento baseado em palavras-chave."""
    text_normalized = normalize_text(text)
    
    for doc_type, keywords in DOCUMENT_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if normalize_text(keyword) in text_normalized:
                return doc_type
    
    return None


class DocumentMetadataExtractor:
    """Extrator de metadados de documentos financeiros usando GPT-4 Vision."""
    
    def __init__(self):
        api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY não configurada")
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o"
    
    def extract_metadata(
        self,
        pdf_path: str,
        pages_to_analyze: List[int] = None,
        existing_products: List[Dict[str, Any]] = None
    ) -> ExtractionResult:
        """
        Extrai metadados do documento analisando múltiplas páginas.
        
        Args:
            pdf_path: Caminho do PDF
            pages_to_analyze: Lista de páginas a analisar (0-indexed). Default: [0, 1, 2]
            existing_products: Lista de produtos existentes para matching
        
        Returns:
            ExtractionResult com dados extraídos e confiança
        """
        if pages_to_analyze is None:
            pages_to_analyze = [0, 1, 2]
        
        page_images = extract_pages_as_images(pdf_path, pages_to_analyze)
        
        if not page_images:
            return ExtractionResult(confidence=0.0)
        
        try:
            extraction = self._analyze_with_vision(page_images)
            
            result = ExtractionResult(
                fund_name=extraction.get("fund_name"),
                ticker=extraction.get("ticker"),
                gestora=extraction.get("gestora"),
                document_type=extraction.get("document_type"),
                confidence=extraction.get("confidence", 0.5),
                source_pages=[p[0] for p in page_images],
                raw_extraction=extraction
            )
            
            if not result.ticker or not result.gestora:
                try:
                    doc = fitz.open(pdf_path)
                    for page_num, _ in page_images:
                        if result.ticker and result.gestora:
                            break
                        text = doc[page_num - 1].get_text()
                        
                        if not result.ticker:
                            ticker = find_ticker_in_text(text)
                            if ticker:
                                result.ticker = ticker
                        
                        if not result.gestora:
                            gestora = find_gestora_in_text(text)
                            if gestora:
                                result.gestora = gestora
                    doc.close()
                except Exception as e:
                    print(f"[MetadataExtractor] Erro no fallback de texto: {e}")
            
            if existing_products and result.fund_name:
                matched = self._match_to_existing_product(result, existing_products)
                if matched:
                    result.fund_name = matched.get("name", result.fund_name)
                    if not result.ticker and matched.get("ticker"):
                        result.ticker = matched["ticker"]
                    result.confidence = min(result.confidence + 0.1, 1.0)
            
            return result
            
        except Exception as e:
            print(f"[MetadataExtractor] Erro na extração: {e}")
            return ExtractionResult(confidence=0.0, raw_extraction={"error": str(e)})
    
    def _analyze_with_vision(self, page_images: List[Tuple[int, str]]) -> Dict[str, Any]:
        """Analisa imagens das páginas com GPT-4 Vision."""
        
        content = [
            {
                "type": "text",
                "text": """Analise estas páginas de um documento financeiro brasileiro e extraia as seguintes informações:

1. **Nome do Fundo/Produto**: O nome completo do fundo de investimento (ex: "MANATÍ HEDGE FUND FII", "TG Renda Imobiliária Feeder Pré")
2. **Ticker**: O código de negociação na B3, geralmente 4 letras + 11/12/13 (ex: MANA11, XPML11, TGAR11)
3. **Gestora**: A empresa gestora do fundo (ex: "TG Core Asset Management", "Manatí", "XP Asset")
4. **Tipo de Documento**: Classifique como um dos tipos:
   - material_publicitario (oferta pública, divulgação)
   - relatorio_gerencial (report mensal, informe)
   - prospecto (prospectus)
   - lamina (lâmina informativa)
   - regulamento
   - fato_relevante (comunicado)
   - apresentacao (institucional, investor presentation)
   - outro

Procure por:
- Logos de gestoras (TG Core, XP, BTG, etc.)
- Nomes de fundos em destaque
- Códigos de ticker mencionados
- Cabeçalhos como "MATERIAL PUBLICITÁRIO", "RELATÓRIO GERENCIAL"
- Rodapés com informações de gestora

Responda APENAS em JSON válido com este formato:
{
  "fund_name": "nome completo do fundo ou null",
  "ticker": "XXXX11 ou null",
  "gestora": "nome da gestora ou null",
  "document_type": "tipo do documento",
  "confidence": 0.0 a 1.0,
  "reasoning": "explicação breve de como identificou"
}"""
            }
        ]
        
        for page_num, img_b64 in page_images:
            content.append({
                "type": "text",
                "text": f"\n--- Página {page_num} ---"
            })
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{img_b64}",
                    "detail": "high"
                }
            })
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um especialista em documentos financeiros brasileiros, especialmente FIIs (Fundos de Investimento Imobiliário) e fundos de investimento. Extraia informações precisas dos documentos."
                    },
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                max_tokens=1000,
                temperature=0.1
            )
            
            response_text = response.choices[0].message.content.strip()
            
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            return json.loads(response_text)
            
        except json.JSONDecodeError as e:
            print(f"[MetadataExtractor] Erro ao parsear JSON: {e}")
            print(f"[MetadataExtractor] Resposta: {response_text[:500]}")
            return {"error": "JSON parse error", "raw": response_text[:500], "confidence": 0.0}
        except Exception as e:
            print(f"[MetadataExtractor] Erro na chamada Vision: {e}")
            return {"error": str(e), "confidence": 0.0}
    
    def _match_to_existing_product(
        self,
        result: ExtractionResult,
        existing_products: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Tenta fazer match com produto existente."""
        
        if result.ticker:
            for product in existing_products:
                if product.get("ticker") and normalize_text(product["ticker"]) == normalize_text(result.ticker):
                    return product
        
        if result.fund_name:
            result_name_normalized = normalize_text(result.fund_name)
            result_name_normalized = result_name_normalized.replace("fii", "").replace("fundo", "").strip()
            
            best_match = None
            best_score = 0
            
            for product in existing_products:
                product_name = product.get("name", "")
                product_name_normalized = normalize_text(product_name)
                product_name_normalized = product_name_normalized.replace("fii", "").replace("fundo", "").strip()
                
                if not product_name_normalized:
                    continue
                
                if result_name_normalized in product_name_normalized or product_name_normalized in result_name_normalized:
                    score = len(set(result_name_normalized.split()) & set(product_name_normalized.split()))
                    if score > best_score:
                        best_score = score
                        best_match = product
            
            if best_match and best_score >= 2:
                return best_match
        
        return None


_extractor_instance = None

def get_metadata_extractor() -> DocumentMetadataExtractor:
    """Retorna instância singleton do extrator."""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = DocumentMetadataExtractor()
    return _extractor_instance
