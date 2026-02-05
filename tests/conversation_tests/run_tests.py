#!/usr/bin/env python3
"""
CLI para executar testes de conversa do agente Stevan.

Uso:
    python tests/conversation_tests/run_tests.py                    # Executar todos
    python tests/conversation_tests/run_tests.py --scenarios 1 3 5  # Cenários específicos
    python tests/conversation_tests/run_tests.py --list             # Listar cenários
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.conversation_tests.evaluator import ConversationEvaluator
from tests.conversation_tests.scenarios import SCENARIOS


def main():
    parser = argparse.ArgumentParser(
        description="Testes de conversa do agente Stevan"
    )
    parser.add_argument(
        '--scenarios', '-s',
        nargs='+',
        type=int,
        help='IDs dos cenários a executar (ex: --scenarios 1 3 5)'
    )
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='Listar todos os cenários disponíveis'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Nome do arquivo de saída (ex: report_v1.json)'
    )
    
    args = parser.parse_args()
    
    if args.list:
        print(f"\nCenários disponíveis ({len(SCENARIOS)}):")
        print(f"{'='*60}")
        for s in SCENARIOS:
            note = f" ⚠ {s['steps'][0]['evaluation'].get('note', '')}" if s['steps'][0]['evaluation'].get('note') else ""
            print(f"  [{s['id']:2d}] {s['name']}")
            print(f"       Categoria: {s['category']} | {s['description']}{note}")
        print()
        return
    
    evaluator = ConversationEvaluator()
    
    scenario_ids = args.scenarios if args.scenarios else None
    evaluator.run_all(scenario_ids=scenario_ids)
    
    report = evaluator.generate_report()
    
    evaluator.print_summary(report)
    
    filepath = evaluator.save_report(report, filename=args.output)
    print(f"Relatório salvo: {filepath}")


if __name__ == "__main__":
    main()
