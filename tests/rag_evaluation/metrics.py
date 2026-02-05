"""
Métricas padrão para avaliação de sistemas RAG.

Métricas implementadas:
- Hit Rate: A resposta correta estava entre os chunks recuperados?
- Precision@K: Dos K chunks recuperados, quantos são relevantes?
- Recall@K: Dos chunks relevantes totais, quantos foram recuperados?
- MRR (Mean Reciprocal Rank): Quão alto na lista está o primeiro chunk correto?
"""

from typing import List, Set, Dict, Any
from dataclasses import dataclass, field


@dataclass
class EvaluationResult:
    """Resultado de avaliação para uma única pergunta."""
    question_id: str
    question_text: str
    question_type: str
    expected_chunk_ids: Set[str]
    retrieved_chunk_ids: List[str]
    is_hit: bool = False
    precision: float = 0.0
    recall: float = 0.0
    reciprocal_rank: float = 0.0
    first_relevant_position: int = -1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id,
            "question_text": self.question_text,
            "question_type": self.question_type,
            "expected_chunk_ids": list(self.expected_chunk_ids),
            "retrieved_chunk_ids": self.retrieved_chunk_ids,
            "is_hit": self.is_hit,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "reciprocal_rank": round(self.reciprocal_rank, 4),
            "first_relevant_position": self.first_relevant_position
        }


@dataclass
class AggregatedMetrics:
    """Métricas agregadas para todo o conjunto de avaliação."""
    total_questions: int = 0
    hit_rate: float = 0.0
    mean_precision: float = 0.0
    mean_recall: float = 0.0
    mrr: float = 0.0
    by_question_type: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_questions": self.total_questions,
            "hit_rate": round(self.hit_rate, 4),
            "mean_precision": round(self.mean_precision, 4),
            "mean_recall": round(self.mean_recall, 4),
            "mrr": round(self.mrr, 4),
            "by_question_type": self.by_question_type
        }


class RAGMetrics:
    """Calculadora de métricas RAG."""
    
    @staticmethod
    def calculate_hit(expected: Set[str], retrieved: List[str]) -> bool:
        """
        Verifica se pelo menos um chunk relevante foi recuperado.
        
        Args:
            expected: Set de chunk IDs esperados (gabarito)
            retrieved: Lista de chunk IDs recuperados
            
        Returns:
            True se há interseção entre expected e retrieved
        """
        return len(expected.intersection(set(retrieved))) > 0
    
    @staticmethod
    def calculate_precision_at_k(expected: Set[str], retrieved: List[str]) -> float:
        """
        Precision@K: Dos K chunks recuperados, quantos são relevantes?
        
        Args:
            expected: Set de chunk IDs esperados
            retrieved: Lista de chunk IDs recuperados (tamanho K)
            
        Returns:
            Proporção de chunks relevantes no resultado (0.0 a 1.0)
        """
        if not retrieved:
            return 0.0
        
        relevant_retrieved = expected.intersection(set(retrieved))
        return len(relevant_retrieved) / len(retrieved)
    
    @staticmethod
    def calculate_recall_at_k(expected: Set[str], retrieved: List[str]) -> float:
        """
        Recall@K: Dos chunks relevantes totais, quantos foram recuperados?
        
        Args:
            expected: Set de chunk IDs esperados
            retrieved: Lista de chunk IDs recuperados
            
        Returns:
            Proporção de chunks relevantes encontrados (0.0 a 1.0)
        """
        if not expected:
            return 0.0
        
        relevant_retrieved = expected.intersection(set(retrieved))
        return len(relevant_retrieved) / len(expected)
    
    @staticmethod
    def calculate_reciprocal_rank(expected: Set[str], retrieved: List[str]) -> tuple:
        """
        Reciprocal Rank: 1 / posição do primeiro chunk relevante.
        
        Args:
            expected: Set de chunk IDs esperados
            retrieved: Lista ordenada de chunk IDs recuperados
            
        Returns:
            Tuple (reciprocal_rank, first_position)
            - reciprocal_rank: 1.0 se o primeiro é relevante, 0.5 se é o segundo, etc.
            - first_position: Posição (1-indexed) do primeiro relevante, -1 se nenhum
        """
        for i, chunk_id in enumerate(retrieved):
            if chunk_id in expected:
                position = i + 1
                return 1.0 / position, position
        
        return 0.0, -1
    
    @classmethod
    def evaluate_single(
        cls,
        question_id: str,
        question_text: str,
        question_type: str,
        expected_chunk_ids: List[str],
        retrieved_chunk_ids: List[str]
    ) -> EvaluationResult:
        """
        Avalia uma única pergunta.
        
        Args:
            question_id: ID único da pergunta
            question_text: Texto da pergunta
            question_type: Tipo/categoria da pergunta
            expected_chunk_ids: Lista de chunk IDs esperados (gabarito)
            retrieved_chunk_ids: Lista de chunk IDs recuperados pelo sistema
            
        Returns:
            EvaluationResult com todas as métricas
        """
        expected_set = set(expected_chunk_ids)
        
        is_hit = cls.calculate_hit(expected_set, retrieved_chunk_ids)
        precision = cls.calculate_precision_at_k(expected_set, retrieved_chunk_ids)
        recall = cls.calculate_recall_at_k(expected_set, retrieved_chunk_ids)
        rr, first_pos = cls.calculate_reciprocal_rank(expected_set, retrieved_chunk_ids)
        
        return EvaluationResult(
            question_id=question_id,
            question_text=question_text,
            question_type=question_type,
            expected_chunk_ids=expected_set,
            retrieved_chunk_ids=retrieved_chunk_ids,
            is_hit=is_hit,
            precision=precision,
            recall=recall,
            reciprocal_rank=rr,
            first_relevant_position=first_pos
        )
    
    @classmethod
    def aggregate(cls, results: List[EvaluationResult]) -> AggregatedMetrics:
        """
        Agrega resultados de múltiplas avaliações.
        
        Args:
            results: Lista de EvaluationResult
            
        Returns:
            AggregatedMetrics com médias e breakdown por tipo
        """
        if not results:
            return AggregatedMetrics()
        
        total = len(results)
        
        hit_rate = sum(1 for r in results if r.is_hit) / total
        mean_precision = sum(r.precision for r in results) / total
        mean_recall = sum(r.recall for r in results) / total
        mrr = sum(r.reciprocal_rank for r in results) / total
        
        by_type = {}
        types = set(r.question_type for r in results)
        
        for qtype in types:
            type_results = [r for r in results if r.question_type == qtype]
            type_total = len(type_results)
            
            by_type[qtype] = {
                "count": type_total,
                "hit_rate": round(sum(1 for r in type_results if r.is_hit) / type_total, 4),
                "mean_precision": round(sum(r.precision for r in type_results) / type_total, 4),
                "mean_recall": round(sum(r.recall for r in type_results) / type_total, 4),
                "mrr": round(sum(r.reciprocal_rank for r in type_results) / type_total, 4)
            }
        
        return AggregatedMetrics(
            total_questions=total,
            hit_rate=hit_rate,
            mean_precision=mean_precision,
            mean_recall=mean_recall,
            mrr=mrr,
            by_question_type=by_type
        )
