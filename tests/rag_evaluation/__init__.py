"""
Sistema de Avaliação de RAG - Nível 2 (Testes de Cenário Offline)

Este módulo fornece ferramentas para avaliar a qualidade da busca semântica
de forma objetiva e mensurável.

Uso:
    python -m tests.rag_evaluation --product MANA11 --top-k 5
    python -m tests.rag_evaluation --discover MANA11
    python -m tests.rag_evaluation --compare baseline_v1.json baseline_v2.json
"""

from .metrics import RAGMetrics
from .evaluator import RAGEvaluator

__all__ = ['RAGMetrics', 'RAGEvaluator']
