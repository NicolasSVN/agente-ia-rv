"""
Framework de avaliação de cenários de conversa para o agente Stevan.
Executa cenários, avalia respostas e gera relatórios detalhados.
"""

import asyncio
import json
import time
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from services.openai_agent import OpenAIAgent
from tests.conversation_tests.scenarios import SCENARIOS


class ConversationEvaluator:
    
    def __init__(self):
        self.agent = OpenAIAgent()
        self.results = []
        self._loop = None
    
    def _run_async(self, coro):
        """Helper to run async functions synchronously."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(asyncio.run, coro).result()
            else:
                return loop.run_until_complete(coro)
        except RuntimeError:
            return asyncio.run(coro)
    
    def _evaluate_criteria(
        self, 
        response: str, 
        evaluation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Avalia uma resposta contra os critérios definidos.
        Retorna detalhes da avaliação com score e diagnóstico.
        """
        response_lower = response.lower()
        response_upper = response.upper()
        passed = True
        checks = []
        failure_type = None
        
        must_contain = evaluation.get("must_contain_any", [])
        if must_contain:
            found_any_group = False
            for keyword_group in must_contain:
                group_found = any(
                    kw.lower() in response_lower for kw in keyword_group
                )
                if group_found:
                    found_any_group = True
                    checks.append({
                        "check": "must_contain_any",
                        "keywords": keyword_group,
                        "result": "PASS",
                        "detail": f"Encontrou pelo menos uma keyword do grupo"
                    })
                    break
            
            if not found_any_group:
                passed = False
                checks.append({
                    "check": "must_contain_any",
                    "keywords": must_contain,
                    "result": "FAIL",
                    "detail": f"Nenhum grupo de keywords obrigatórias encontrado na resposta"
                })
                behavior = evaluation.get("behavior", "")
                if behavior in ["structured_data", "precise_retrieval", "concise_summary"]:
                    failure_type = "RECUPERAÇÃO"
                elif behavior in ["disambiguation", "contextual_followup", "topic_switch", "typo_correction"]:
                    failure_type = "CONVERSA"
                else:
                    failure_type = "GERAÇÃO"
        
        should_contain = evaluation.get("should_contain_any", [])
        should_hits = 0
        for keyword_group in should_contain:
            group_found = any(kw.lower() in response_lower for kw in keyword_group)
            if group_found:
                should_hits += 1
                checks.append({
                    "check": "should_contain",
                    "keywords": keyword_group,
                    "result": "PASS"
                })
            else:
                checks.append({
                    "check": "should_contain",
                    "keywords": keyword_group,
                    "result": "WARN",
                    "detail": "Keywords desejáveis não encontradas"
                })
        
        should_score = should_hits / len(should_contain) if should_contain else 1.0
        
        must_not_contain = evaluation.get("must_not_contain", [])
        for forbidden in must_not_contain:
            if forbidden.lower() in response_lower:
                passed = False
                failure_type = failure_type or "GERAÇÃO"
                checks.append({
                    "check": "must_not_contain",
                    "keyword": forbidden,
                    "result": "FAIL",
                    "detail": f"Resposta contém texto proibido: '{forbidden}'"
                })
        
        max_length = evaluation.get("max_length")
        if max_length and len(response) > max_length:
            checks.append({
                "check": "max_length",
                "expected": max_length,
                "actual": len(response),
                "result": "WARN",
                "detail": f"Resposta excede tamanho máximo sugerido ({len(response)} > {max_length})"
            })
        
        quality_score = 1.0 if passed else 0.0
        quality_score = (quality_score * 0.6) + (should_score * 0.4)
        
        return {
            "passed": passed,
            "quality_score": round(quality_score, 2),
            "failure_type": failure_type,
            "checks": checks,
            "should_score": round(should_score, 2)
        }
    
    def _run_step(
        self,
        step: Dict[str, Any],
        conversation_history: List[Dict[str, Any]]
    ) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]]]:
        """
        Executa um passo do cenário (setup + mensagem principal).
        Retorna a resposta, resultado da avaliação e histórico atualizado.
        """
        if "setup_message" in step:
            setup_msg = step["setup_message"]
            print(f"    [Setup] Enviando: \"{setup_msg}\"")
            
            setup_response, _, setup_ctx = self._run_async(
                self.agent.generate_response(
                    user_message=setup_msg,
                    conversation_history=conversation_history
                )
            )
            
            conversation_history.append({
                "role": "user",
                "content": setup_msg
            })
            conversation_history.append({
                "role": "assistant",
                "content": setup_response,
                "metadata": setup_ctx or {}
            })
            
            print(f"    [Setup] Resposta recebida ({len(setup_response)} chars)")
            time.sleep(1)
        
        message = step["message"]
        print(f"    [Test] Enviando: \"{message}\"")
        
        response, should_ticket, context_info = self._run_async(
            self.agent.generate_response(
                user_message=message,
                conversation_history=conversation_history
            )
        )
        
        conversation_history.append({
            "role": "user",
            "content": message
        })
        conversation_history.append({
            "role": "assistant",
            "content": response,
            "metadata": context_info or {}
        })
        
        eval_result = self._evaluate_criteria(response, step["evaluation"])
        
        return response, eval_result, conversation_history
    
    def run_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Executa um cenário completo e retorna o resultado."""
        scenario_id = scenario["id"]
        scenario_name = scenario["name"]
        
        print(f"\n{'='*60}")
        print(f"Cenário {scenario_id}: {scenario_name}")
        print(f"Categoria: {scenario['category']}")
        print(f"{'='*60}")
        
        conversation_history = []
        step_results = []
        overall_passed = True
        
        start_time = time.time()
        
        for i, step in enumerate(scenario["steps"]):
            print(f"\n  Passo {i+1}:")
            
            response, eval_result, conversation_history = self._run_step(
                step, conversation_history
            )
            
            step_results.append({
                "step": i + 1,
                "message": step["message"],
                "response": response,
                "response_length": len(response),
                "evaluation": eval_result,
                "criteria_description": step["evaluation"].get("description", ""),
            })
            
            if not eval_result["passed"]:
                overall_passed = False
            
            status = "APROVADO" if eval_result["passed"] else "REPROVADO"
            print(f"    Resultado: [{status}] (Score: {eval_result['quality_score']})")
            if not eval_result["passed"]:
                print(f"    Tipo de Falha: {eval_result['failure_type']}")
            
            print(f"    Resposta ({len(response)} chars): {response[:150]}...")
        
        elapsed = time.time() - start_time
        
        failure_type = None
        if not overall_passed:
            for sr in step_results:
                if sr["evaluation"].get("failure_type"):
                    failure_type = sr["evaluation"]["failure_type"]
                    break
        
        avg_quality = sum(
            sr["evaluation"]["quality_score"] for sr in step_results
        ) / len(step_results) if step_results else 0
        
        result = {
            "scenario_id": scenario_id,
            "scenario_name": scenario_name,
            "category": scenario["category"],
            "description": scenario["description"],
            "status": "APROVADO" if overall_passed else "REPROVADO",
            "failure_type": failure_type,
            "quality_score": round(avg_quality, 2),
            "elapsed_seconds": round(elapsed, 1),
            "steps": step_results,
            "note": scenario["steps"][0]["evaluation"].get("note", None)
        }
        
        self.results.append(result)
        
        final_status = "APROVADO" if overall_passed else "REPROVADO"
        print(f"\n  >>> Cenário {scenario_id}: [{final_status}] <<<")
        
        return result
    
    def run_all(self, scenario_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """Executa todos os cenários (ou os especificados)."""
        scenarios = SCENARIOS
        if scenario_ids:
            scenarios = [s for s in SCENARIOS if s["id"] in scenario_ids]
        
        print(f"\n{'#'*60}")
        print(f"# TESTE DE CONVERSA DO AGENTE STEVAN")
        print(f"# Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"# Cenários: {len(scenarios)}")
        print(f"{'#'*60}")
        
        for scenario in scenarios:
            self.run_scenario(scenario)
            time.sleep(2)
        
        return self.results
    
    def generate_report(self) -> Dict[str, Any]:
        """Gera um relatório completo com métricas e diagnóstico."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "APROVADO")
        failed = sum(1 for r in self.results if r["status"] == "REPROVADO")
        
        failure_types = {}
        for r in self.results:
            if r["failure_type"]:
                ft = r["failure_type"]
                failure_types[ft] = failure_types.get(ft, 0) + 1
        
        by_category = {}
        for r in self.results:
            cat = r["category"]
            if cat not in by_category:
                by_category[cat] = {"total": 0, "passed": 0, "failed": 0}
            by_category[cat]["total"] += 1
            if r["status"] == "APROVADO":
                by_category[cat]["passed"] += 1
            else:
                by_category[cat]["failed"] += 1
        
        avg_quality = sum(r["quality_score"] for r in self.results) / total if total else 0
        avg_time = sum(r["elapsed_seconds"] for r in self.results) / total if total else 0
        
        report = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_scenarios": total,
                "agent_version": "Stevan v1.0"
            },
            "summary": {
                "passed": passed,
                "failed": failed,
                "pass_rate": round(passed / total * 100, 1) if total else 0,
                "average_quality_score": round(avg_quality, 2),
                "average_response_time": round(avg_time, 1),
            },
            "failure_analysis": {
                "by_type": failure_types,
                "recommendations": self._generate_recommendations(failure_types)
            },
            "by_category": by_category,
            "scenarios": self.results
        }
        
        return report
    
    def _generate_recommendations(self, failure_types: Dict[str, int]) -> List[str]:
        """Gera recomendações baseadas nos tipos de falha."""
        recs = []
        
        if failure_types.get("RECUPERAÇÃO", 0) > 0:
            recs.append(
                "RECUPERAÇÃO: Verifique os chunks no ChromaDB. "
                "Possíveis causas: metadados ausentes, threshold de similaridade alto, "
                "ou chunks mal formatados. Ajuste a busca híbrida em enhanced_search."
            )
        
        if failure_types.get("GERAÇÃO", 0) > 0:
            recs.append(
                "GERAÇÃO: Revise o template do prompt. "
                "Seja mais explícito nas instruções ao LLM (ex: 'Responda de forma concisa', "
                "'Estruture em tópicos'). Verifique se os chunks recuperados estão no contexto."
            )
        
        if failure_types.get("CONVERSA", 0) > 0:
            recs.append(
                "CONVERSA: Revise o sistema de memória/estado da conversa. "
                "O agente precisa lembrar dos últimos tópicos e entidades. "
                "Refine a lógica de desambiguação e follow-up."
            )
        
        if not recs:
            recs.append("Todos os cenários passaram! Continue monitorando com novos cenários.")
        
        return recs
    
    def save_report(self, report: Dict[str, Any], filename: Optional[str] = None) -> str:
        """Salva o relatório em JSON."""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"conversation_test_{timestamp}.json"
        
        filepath = os.path.join(
            os.path.dirname(__file__), 'reports', filename
        )
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\nRelatório salvo em: {filepath}")
        return filepath
    
    def print_summary(self, report: Dict[str, Any]):
        """Imprime um resumo formatado do relatório."""
        summary = report["summary"]
        
        print(f"\n{'='*60}")
        print(f"RELATÓRIO FINAL")
        print(f"{'='*60}")
        print(f"Data: {report['metadata']['timestamp']}")
        print(f"Total de Cenários: {report['metadata']['total_scenarios']}")
        print(f"")
        print(f"  APROVADOS:  {summary['passed']}")
        print(f"  REPROVADOS: {summary['failed']}")
        print(f"  TAXA DE APROVAÇÃO: {summary['pass_rate']}%")
        print(f"  QUALIDADE MÉDIA: {summary['average_quality_score']}")
        print(f"  TEMPO MÉDIO: {summary['average_response_time']}s")
        
        print(f"\n--- Resultado por Cenário ---")
        for r in report["scenarios"]:
            status_icon = "✓" if r["status"] == "APROVADO" else "✗"
            failure_info = f" [{r['failure_type']}]" if r["failure_type"] else ""
            note_info = f" (⚠ {r['note']})" if r.get("note") else ""
            print(f"  {status_icon} Cenário {r['scenario_id']:2d}: [{r['status']}] "
                  f"Score={r['quality_score']}{failure_info}{note_info}")
            print(f"     {r['scenario_name']}")
        
        print(f"\n--- Análise de Falhas ---")
        failure_analysis = report["failure_analysis"]
        if failure_analysis["by_type"]:
            for ft, count in failure_analysis["by_type"].items():
                print(f"  {ft}: {count} cenário(s)")
        else:
            print(f"  Nenhuma falha detectada!")
        
        print(f"\n--- Recomendações ---")
        for i, rec in enumerate(failure_analysis["recommendations"], 1):
            print(f"  {i}. {rec}")
        
        print(f"\n--- Por Categoria ---")
        for cat, stats in report["by_category"].items():
            rate = round(stats["passed"] / stats["total"] * 100) if stats["total"] else 0
            print(f"  {cat}: {stats['passed']}/{stats['total']} ({rate}%)")
        
        print(f"{'='*60}\n")
