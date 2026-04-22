"""
CLI para o sistema de avaliação RAG.

Uso:
    python -m tests.rag_evaluation --discover MANA11
    python -m tests.rag_evaluation --evaluate MANA11 --top-k 5
    python -m tests.rag_evaluation --compare report1.json report2.json
    python -m tests.rag_evaluation --list
"""

import argparse
import json
import sys
from pathlib import Path

from .evaluator import RAGEvaluator, GOLDEN_SETS_DIR, REPORTS_DIR


def main():
    parser = argparse.ArgumentParser(
        description="Sistema de Avaliação RAG - Nível 2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python -m tests.rag_evaluation --discover MANA11
      Lista todos os chunks indexados para MANA11 (útil para criar golden set)
  
  python -m tests.rag_evaluation --evaluate MANA11 --top-k 5
      Avalia o sistema RAG usando o golden set do MANA11
  
  python -m tests.rag_evaluation --compare baseline.json new.json
      Compara dois relatórios de avaliação
  
  python -m tests.rag_evaluation --list
      Lista todos os golden sets e relatórios disponíveis
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--discover', 
        metavar='TICKER',
        help='Descobre chunks indexados para um produto (ex: MANA11)'
    )
    group.add_argument(
        '--evaluate', 
        metavar='TICKER',
        help='Avalia o sistema RAG usando o golden set do produto'
    )
    group.add_argument(
        '--compare',
        nargs=2,
        metavar=('BASELINE', 'NEW'),
        help='Compara dois relatórios de avaliação'
    )
    group.add_argument(
        '--list',
        action='store_true',
        help='Lista golden sets e relatórios disponíveis'
    )
    
    parser.add_argument(
        '--top-k',
        type=int,
        default=5,
        help='Número de chunks a recuperar por pergunta (default: 5)'
    )
    parser.add_argument(
        '--save',
        metavar='NAME',
        help='Nome do arquivo para salvar o relatório (sem extensão)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Mostra progresso detalhado'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Saída em formato JSON'
    )
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Não pergunta interativamente se quer salvar o relatório (útil em CI/scripts)'
    )
    
    args = parser.parse_args()
    
    try:
        evaluator = RAGEvaluator()
        
        if args.discover:
            ticker = args.discover.upper()
            print(f"\nDescoberta de chunks para {ticker}...")
            print("-" * 60)
            
            chunks = evaluator.discover_chunks(ticker, limit=100)
            
            if not chunks:
                print(f"Nenhum chunk encontrado para {ticker}")
                print("Verifique se o produto está indexado no ChromaDB.")
                sys.exit(1)
            
            if args.json:
                print(json.dumps(chunks, indent=2, ensure_ascii=False))
            else:
                print(f"Encontrados {len(chunks)} chunks:\n")
                for chunk in chunks:
                    print(f"[{chunk['index']:2d}] ID: {chunk['chroma_id']}")
                    print(f"     Preview: {chunk['content_preview'][:100]}...")
                    print()
                
                print("-" * 60)
                print(f"Use esses IDs para criar o golden set em:")
                print(f"  {GOLDEN_SETS_DIR / f'{ticker}.json'}")
                print(f"Copie o template.json e preencha os expected_chunk_ids.")
        
        elif args.evaluate:
            ticker = args.evaluate.upper()
            print(f"\nAvaliando RAG para {ticker} (top-k={args.top_k})...")
            
            result = evaluator.evaluate_golden_set(
                ticker, 
                top_k=args.top_k,
                verbose=args.verbose
            )
            
            if args.json:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                evaluator.print_evaluation_summary(result)
            
            if args.save:
                filepath = evaluator.save_report(result, args.save)
                print(f"Relatório salvo em: {filepath}")
            elif not args.json and not args.no_save and sys.stdin.isatty():
                save_prompt = input("Salvar relatório? [s/N]: ").strip().lower()
                if save_prompt == 's':
                    filepath = evaluator.save_report(result)
                    print(f"Relatório salvo em: {filepath}")
        
        elif args.compare:
            baseline_path, new_path = args.compare
            
            for p in [baseline_path, new_path]:
                if not Path(p).exists():
                    reports_path = REPORTS_DIR / p
                    if reports_path.exists():
                        if p == baseline_path:
                            baseline_path = str(reports_path)
                        else:
                            new_path = str(reports_path)
            
            print(f"\nComparando relatórios...")
            comparison = RAGEvaluator.compare_reports(baseline_path, new_path)
            
            if args.json:
                print(json.dumps(comparison, indent=2, ensure_ascii=False))
            else:
                print("\n" + "=" * 60)
                print("  COMPARAÇÃO DE AVALIAÇÕES")
                print("=" * 60)
                print(f"  Baseline: {comparison['baseline']}")
                print(f"  Novo:     {comparison['compared_to']}")
                print("-" * 60)
                
                for metric, values in comparison['differences'].items():
                    delta = values['delta']
                    pct = values['pct_change']
                    arrow = "↑" if delta > 0 else "↓" if delta < 0 else "="
                    color_start = ""
                    if delta > 0.01:
                        status = f"{arrow} +{pct:.1f}%"
                    elif delta < -0.01:
                        status = f"{arrow} {pct:.1f}%"
                    else:
                        status = "="
                    
                    print(f"  {metric:18s}: {values['old']:.3f} → {values['new']:.3f}  {status}")
                
                print("-" * 60)
                if comparison['improved']:
                    print(f"  Melhorou: {', '.join(comparison['improved'])}")
                if comparison['regressed']:
                    print(f"  Piorou:   {', '.join(comparison['regressed'])}")
                print("=" * 60 + "\n")
        
        elif args.list:
            print("\n" + "=" * 60)
            print("  RECURSOS DISPONÍVEIS")
            print("=" * 60)
            
            golden_sets = RAGEvaluator.list_available_golden_sets()
            print(f"\n  Golden Sets ({len(golden_sets)}):")
            if golden_sets:
                for gs in golden_sets:
                    print(f"    - {gs}")
            else:
                print("    (nenhum golden set criado ainda)")
            
            reports = list(REPORTS_DIR.glob("*.json"))
            print(f"\n  Relatórios ({len(reports)}):")
            if reports:
                for r in sorted(reports, reverse=True)[:10]:
                    print(f"    - {r.name}")
                if len(reports) > 10:
                    print(f"    ... e mais {len(reports) - 10}")
            else:
                print("    (nenhum relatório gerado ainda)")
            
            print("\n" + "=" * 60 + "\n")
    
    except FileNotFoundError as e:
        print(f"\nErro: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nErro inesperado: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
