"""
Evaluator - Engine principal de avaliação RAG.

Este módulo executa avaliações usando golden sets e gera relatórios.
É agnóstico ao produto - funciona para qualquer ticker/produto indexado.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from .metrics import RAGMetrics, EvaluationResult, AggregatedMetrics


GOLDEN_SETS_DIR = Path(__file__).parent / "golden_sets"
REPORTS_DIR = Path(__file__).parent / "reports"


class RAGEvaluator:
    """
    Avaliador de sistemas RAG.
    
    Carrega golden sets, executa buscas e calcula métricas.
    """
    
    def __init__(self, vector_store=None):
        """
        Inicializa o avaliador.
        
        Args:
            vector_store: Instância do VectorStore. Se None, será criada.
        """
        if vector_store is None:
            from services.vector_store import VectorStore
            self.vector_store = VectorStore()
        else:
            self.vector_store = vector_store
    
    @staticmethod
    def list_available_golden_sets() -> List[str]:
        """Lista todos os golden sets disponíveis."""
        golden_sets = []
        for f in GOLDEN_SETS_DIR.glob("*.json"):
            if f.name != "template.json":
                golden_sets.append(f.stem)
        return golden_sets
    
    @staticmethod
    def load_golden_set(product_ticker: str) -> Dict[str, Any]:
        """
        Carrega um golden set para um produto.
        
        Args:
            product_ticker: Ticker do produto (ex: MANA11)
            
        Returns:
            Dicionário com metadata e questions
            
        Raises:
            FileNotFoundError: Se o golden set não existir
        """
        filepath = GOLDEN_SETS_DIR / f"{product_ticker.upper()}.json"
        
        if not filepath.exists():
            raise FileNotFoundError(
                f"Golden set não encontrado para {product_ticker}. "
                f"Crie o arquivo {filepath} usando o template.json como base. "
                f"Use --discover {product_ticker} para listar os chunk IDs disponíveis."
            )
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def _extract_chunk_id(doc: Dict[str, Any]) -> Optional[str]:
        """
        Normaliza o ID de um chunk para o formato usado nos golden sets
        (ex: ``product_block_47``).

        Ordem de preferência:
        1. ``doc_id`` (formato canônico armazenado em ``document_embeddings``).
        2. ``chroma_id`` (legado, mantido por compatibilidade).
        3. ``metadata.block_id`` — neste caso prefixamos com ``product_block_``
           para casar com o formato esperado pelos golden sets.
        """
        doc_id = doc.get('doc_id') or doc.get('chroma_id')
        if doc_id:
            return doc_id

        block_id = doc.get('metadata', {}).get('block_id')
        if block_id is not None:
            block_id_str = str(block_id)
            if block_id_str.startswith('product_block_'):
                return block_id_str
            return f"product_block_{block_id_str}"

        return None

    def discover_chunks(self, product_ticker: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Descobre todos os chunks indexados para um produto.
        Útil para criar o golden set.
        
        Args:
            product_ticker: Ticker do produto
            limit: Número máximo de chunks a retornar
            
        Returns:
            Lista de chunks com ID e preview do conteúdo
        """
        results = self.vector_store.search_by_ticker(product_ticker, n_results=limit)
        
        chunks = []
        for i, doc in enumerate(results):
            content = doc.get('content', '')
            if '---' in content:
                content = content.split('---', 1)[1]
            
            chunks.append({
                "index": i + 1,
                "chroma_id": self._extract_chunk_id(doc) or f'unknown_{i}',
                "content_preview": content[:200].strip(),
                "metadata": {
                    k: v for k, v in doc.get('metadata', {}).items() 
                    if k in ['product_ticker', 'product_name', 'material_type', 'block_type']
                }
            })
        
        return chunks
    
    def execute_search(self, query: str, top_k: int = 5) -> List[str]:
        """
        Executa uma busca e retorna os chunk IDs recuperados.
        
        Args:
            query: Texto da pergunta
            top_k: Número de resultados a retornar
            
        Returns:
            Lista de chunk IDs (chroma_id) recuperados
        """
        results = self.vector_store.search(query, n_results=top_k)
        
        chunk_ids = []
        for doc in results:
            chunk_id = self._extract_chunk_id(doc)
            if chunk_id:
                chunk_ids.append(chunk_id)
        
        return chunk_ids
    
    def evaluate_golden_set(
        self, 
        product_ticker: str, 
        top_k: int = 5,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Avalia um produto usando seu golden set.
        
        Args:
            product_ticker: Ticker do produto
            top_k: Número de resultados a recuperar por pergunta
            verbose: Se True, imprime progresso
            
        Returns:
            Dicionário com resultados individuais e agregados
        """
        golden_set = self.load_golden_set(product_ticker)
        questions = golden_set.get('questions', [])
        
        if not questions:
            raise ValueError(f"Golden set para {product_ticker} não contém perguntas")
        
        results = []
        
        for i, q in enumerate(questions):
            if verbose:
                print(f"  [{i+1}/{len(questions)}] {q['question_text'][:50]}...")
            
            retrieved_ids = self.execute_search(q['question_text'], top_k=top_k)
            
            result = RAGMetrics.evaluate_single(
                question_id=q['question_id'],
                question_text=q['question_text'],
                question_type=q['question_type'],
                expected_chunk_ids=q['expected_chunk_ids'],
                retrieved_chunk_ids=retrieved_ids
            )
            
            results.append(result)
        
        aggregated = RAGMetrics.aggregate(results)
        
        return {
            "metadata": {
                "product_ticker": product_ticker,
                "evaluated_at": datetime.now().isoformat(),
                "top_k": top_k,
                "total_questions": len(questions)
            },
            "aggregated_metrics": aggregated.to_dict(),
            "individual_results": [r.to_dict() for r in results]
        }
    
    def save_report(
        self, 
        evaluation_result: Dict[str, Any], 
        report_name: Optional[str] = None
    ) -> str:
        """
        Salva um relatório de avaliação.
        
        Args:
            evaluation_result: Resultado da avaliação
            report_name: Nome do arquivo (sem extensão). Se None, gera automaticamente.
            
        Returns:
            Caminho do arquivo salvo
        """
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        
        if report_name is None:
            ticker = evaluation_result['metadata']['product_ticker']
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_name = f"{ticker}_eval_{timestamp}"
        
        filepath = REPORTS_DIR / f"{report_name}.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(evaluation_result, f, indent=2, ensure_ascii=False)
        
        return str(filepath)
    
    @staticmethod
    def compare_reports(report1_path: str, report2_path: str) -> Dict[str, Any]:
        """
        Compara dois relatórios de avaliação.
        
        Args:
            report1_path: Caminho para o primeiro relatório (baseline)
            report2_path: Caminho para o segundo relatório (novo)
            
        Returns:
            Dicionário com diferenças entre as métricas
        """
        with open(report1_path, 'r', encoding='utf-8') as f:
            report1 = json.load(f)
        
        with open(report2_path, 'r', encoding='utf-8') as f:
            report2 = json.load(f)
        
        m1 = report1['aggregated_metrics']
        m2 = report2['aggregated_metrics']
        
        def diff(v1, v2):
            delta = v2 - v1
            pct = (delta / v1 * 100) if v1 != 0 else 0
            return {"old": v1, "new": v2, "delta": round(delta, 4), "pct_change": round(pct, 2)}
        
        comparison = {
            "baseline": report1_path,
            "compared_to": report2_path,
            "differences": {
                "hit_rate": diff(m1['hit_rate'], m2['hit_rate']),
                "mean_precision": diff(m1['mean_precision'], m2['mean_precision']),
                "mean_recall": diff(m1['mean_recall'], m2['mean_recall']),
                "mrr": diff(m1['mrr'], m2['mrr'])
            },
            "improved": [],
            "regressed": [],
            "unchanged": []
        }
        
        for metric, values in comparison['differences'].items():
            if values['delta'] > 0.01:
                comparison['improved'].append(metric)
            elif values['delta'] < -0.01:
                comparison['regressed'].append(metric)
            else:
                comparison['unchanged'].append(metric)
        
        return comparison
    
    def print_evaluation_summary(self, result: Dict[str, Any]) -> None:
        """Imprime um resumo formatado da avaliação."""
        meta = result['metadata']
        metrics = result['aggregated_metrics']
        
        print("\n" + "=" * 60)
        print(f"  AVALIAÇÃO RAG - {meta['product_ticker']}")
        print("=" * 60)
        print(f"  Data: {meta['evaluated_at'][:19]}")
        print(f"  Perguntas: {meta['total_questions']} | Top-K: {meta['top_k']}")
        print("-" * 60)
        print(f"  Hit Rate:        {metrics['hit_rate']:.1%}")
        print(f"  Mean Precision:  {metrics['mean_precision']:.1%}")
        print(f"  Mean Recall:     {metrics['mean_recall']:.1%}")
        print(f"  MRR:             {metrics['mrr']:.3f}")
        print("-" * 60)
        
        if metrics.get('by_question_type'):
            print("  Por tipo de pergunta:")
            for qtype, m in metrics['by_question_type'].items():
                print(f"    {qtype}: HR={m['hit_rate']:.0%} P={m['mean_precision']:.0%} R={m['mean_recall']:.0%}")
        
        print("=" * 60)
        
        failed = [r for r in result['individual_results'] if not r['is_hit']]
        if failed:
            print(f"\n  Perguntas com FALHA ({len(failed)}):")
            for f in failed[:5]:
                print(f"    - [{f['question_id']}] {f['question_text'][:50]}...")
            if len(failed) > 5:
                print(f"    ... e mais {len(failed) - 5}")
        
        print()
