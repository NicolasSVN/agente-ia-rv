"""
Serviço de busca na web para o agente de IA.
Integra com Tavily API para pesquisas seguras e controladas.
"""
import os
import json
import time
import httpx
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from services.cost_tracker import cost_tracker


class WebSearchService:
    """
    Serviço de busca na web com foco em fontes confiáveis.
    Usa Tavily API para pesquisas otimizadas para IA.
    """
    
    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")
        self.base_url = "https://api.tavily.com"
        self.default_sources = [
            "infomoney.com.br",
            "statusinvest.com.br",
            "fundsexplorer.com.br",
            "valorinveste.globo.com",
            "b3.com.br",
            "investing.com",
            "br.investing.com",
            "moneytimes.com.br",
            "suno.com.br",
            "google.com",
            "finance.yahoo.com",
        ]
    
    def is_configured(self) -> bool:
        """Verifica se a API está configurada."""
        return bool(self.api_key)
    
    def get_trusted_domains(self, db=None) -> List[str]:
        """
        Obtém lista de domínios confiáveis do banco.
        Se não houver banco, retorna lista padrão.
        """
        if db:
            try:
                from database.models import TrustedSource
                sources = db.query(TrustedSource).filter(
                    TrustedSource.is_active == True
                ).order_by(TrustedSource.priority.desc()).all()
                
                if sources:
                    return [s.domain for s in sources]
            except Exception as e:
                print(f"[WebSearch] Erro ao buscar fontes: {e}")
        
        return self.default_sources
    
    async def _do_search_async(
        self,
        query: str,
        include_domains: list = None,
        max_results: int = 5,
        search_depth: str = "advanced"
    ) -> Dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "api_key": self.api_key,
                "query": query,
                "search_depth": search_depth,
                "max_results": max_results,
                "include_answer": True,
                "include_raw_content": False,
            }
            if include_domains:
                payload["include_domains"] = include_domains

            response = await client.post(f"{self.base_url}/search", json=payload)

            if response.status_code != 200:
                error_detail = ""
                try:
                    error_detail = response.text[:300]
                except Exception:
                    pass
                print(f"[WebSearch] API error {response.status_code}: {error_detail}")
                return {
                    "success": False,
                    "error": f"Erro na API: {response.status_code} - {error_detail}",
                    "results": [],
                    "citations": []
                }

            data = response.json()

            results = []
            citations = []

            for result in data.get("results", []):
                fact = {
                    "title": result.get("title", ""),
                    "content": result.get("content", ""),
                    "url": result.get("url", ""),
                    "score": result.get("score", 0),
                    "published_date": result.get("published_date"),
                }
                results.append(fact)

                citation = self._format_citation(fact)
                if citation:
                    citations.append(citation)

            return {
                "success": True,
                "query": query,
                "answer": data.get("answer"),
                "results": results,
                "citations": citations,
            }

    async def search(
        self,
        query: str,
        db=None,
        max_results: int = 5,
        search_depth: str = "advanced"
    ) -> Dict:
        if not self.api_key:
            return {
                "success": False,
                "error": "TAVILY_API_KEY não configurada",
                "results": [],
                "citations": []
            }

        start_time = time.time()
        trusted_domains = self.get_trusted_domains(db)

        try:
            result = await self._do_search_async(query, include_domains=trusted_domains, max_results=max_results, search_depth=search_depth)

            if result.get("success") and not result.get("results"):
                print(f"[WebSearch] 0 resultados com domínios restritos, retentando sem filtro para: {query}")
                result = await self._do_search_async(query, include_domains=None, max_results=max_results, search_depth=search_depth)

            if not result.get("success"):
                print(f"[WebSearch] Busca com domínios restritos falhou ({result.get('error', '?')}), retentando sem filtro para: {query}")
                result = await self._do_search_async(query, include_domains=None, max_results=max_results, search_depth=search_depth)

            try:
                cost_tracker.track_tavily_search(query=query)
            except Exception:
                pass

            elapsed_ms = int((time.time() - start_time) * 1000)
            result["sources_searched"] = trusted_domains
            result["response_time_ms"] = elapsed_ms

            print(f"[WebSearch] query='{query}' | success={result.get('success')} | results={len(result.get('results', []))} | {elapsed_ms}ms")

            return result

        except Exception as e:
            print(f"[WebSearch] Exceção na busca: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "results": [],
                "citations": []
            }
    
    def _do_search_sync(
        self,
        query: str,
        include_domains: list = None,
        max_results: int = 5,
        search_depth: str = "advanced"
    ) -> Dict:
        with httpx.Client(timeout=30.0) as client:
            payload = {
                "api_key": self.api_key,
                "query": query,
                "search_depth": search_depth,
                "max_results": max_results,
                "include_answer": True,
                "include_raw_content": False,
            }
            if include_domains:
                payload["include_domains"] = include_domains

            response = client.post(f"{self.base_url}/search", json=payload)

            if response.status_code != 200:
                error_detail = ""
                try:
                    error_detail = response.text[:300]
                except Exception:
                    pass
                print(f"[WebSearch] API error {response.status_code}: {error_detail}")
                return {
                    "success": False,
                    "error": f"Erro na API: {response.status_code} - {error_detail}",
                    "results": [],
                    "citations": []
                }

            data = response.json()

            results = []
            citations = []

            for result in data.get("results", []):
                fact = {
                    "title": result.get("title", ""),
                    "content": result.get("content", ""),
                    "url": result.get("url", ""),
                    "score": result.get("score", 0),
                    "published_date": result.get("published_date"),
                }
                results.append(fact)

                citation = self._format_citation(fact)
                if citation:
                    citations.append(citation)

            return {
                "success": True,
                "query": query,
                "answer": data.get("answer"),
                "results": results,
                "citations": citations,
            }

    def search_sync(
        self,
        query: str,
        db=None,
        max_results: int = 5,
        search_depth: str = "advanced"
    ) -> Dict:
        if not self.api_key:
            return {
                "success": False,
                "error": "TAVILY_API_KEY não configurada",
                "results": [],
                "citations": []
            }

        start_time = time.time()
        trusted_domains = self.get_trusted_domains(db)

        try:
            result = self._do_search_sync(query, include_domains=trusted_domains, max_results=max_results, search_depth=search_depth)

            if result.get("success") and not result.get("results"):
                print(f"[WebSearch] 0 resultados com domínios restritos, retentando sem filtro para: {query}")
                result = self._do_search_sync(query, include_domains=None, max_results=max_results, search_depth=search_depth)

            if not result.get("success"):
                print(f"[WebSearch] Busca com domínios restritos falhou ({result.get('error', '?')}), retentando sem filtro para: {query}")
                result = self._do_search_sync(query, include_domains=None, max_results=max_results, search_depth=search_depth)

            try:
                cost_tracker.track_tavily_search(query=query)
            except Exception:
                pass

            elapsed_ms = int((time.time() - start_time) * 1000)
            result["sources_searched"] = trusted_domains
            result["response_time_ms"] = elapsed_ms

            print(f"[WebSearch] query='{query}' | success={result.get('success')} | results={len(result.get('results', []))} | {elapsed_ms}ms")

            return result

        except Exception as e:
            print(f"[WebSearch] Exceção na busca: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "results": [],
                "citations": []
            }
    
    def _format_citation(self, fact: Dict) -> Optional[str]:
        """
        Formata uma citação no padrão exigido.
        Inclui fonte, data e link.
        """
        if not fact.get("url"):
            return None
        
        title = fact.get("title", "Sem título")
        url = fact["url"]
        
        domain = url.split("/")[2] if "/" in url else url
        domain = domain.replace("www.", "")
        
        date_str = ""
        if fact.get("published_date"):
            try:
                date = datetime.fromisoformat(fact["published_date"].replace("Z", "+00:00"))
                date_str = f" ({date.strftime('%d/%m/%Y')})"
            except:
                pass
        
        return f"Fonte: {domain}{date_str} - {title}\nLink: {url}"
    
    def extract_facts(self, results: List[Dict], query: str) -> str:
        """
        Extrai fatos relevantes dos resultados.
        Foca em dados numéricos e factuais, ignora opiniões.
        """
        if not results:
            return ""
        
        facts = []
        for result in results[:5]:
            content = result.get("content", "")
            if content:
                content = content[:500]
                facts.append(f"• {content}")
        
        return "\n\n".join(facts)
    
    def log_search(
        self,
        db,
        query: str,
        results: Dict,
        fallback_reason: str = None,
        conversation_id: str = None,
        user_id: int = None
    ) -> None:
        """
        Registra a busca para auditoria.
        """
        try:
            from database.models import WebSearchLog
            
            log_entry = WebSearchLog(
                query=query[:1000],
                sources_searched=json.dumps(results.get("sources_searched", [])),
                results_count=len(results.get("results", [])),
                facts_extracted=json.dumps([r.get("content", "")[:200] for r in results.get("results", [])]),
                citations=json.dumps(results.get("citations", [])),
                fallback_reason=fallback_reason,
                response_time_ms=results.get("response_time_ms"),
                conversation_id=conversation_id,
                user_id=user_id
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            print(f"[WebSearch] Erro ao logar busca: {e}")


_web_search_service = None

def get_web_search_service() -> WebSearchService:
    """Retorna instância singleton do serviço."""
    global _web_search_service
    if _web_search_service is None:
        _web_search_service = WebSearchService()
    return _web_search_service
