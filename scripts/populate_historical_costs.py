"""
Script para popular a Central de Custos com dados históricos estimados.
Baseado nos dados reais do projeto:
- 354 insights (interações analisadas)
- 351 buscas RAG
- 167 chunks no ChromaDB
- 9 buscas Tavily
- 3 materiais processados
- 55 blocos de conteúdo enriquecidos
- 69 escalações
- ~15 áudios estimados
Distribuídos pelos dias reais de atividade (07/dez/2025 a 09/fev/2026).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import random
from database.database import SessionLocal
from database.models import CostTracking

EXCHANGE_RATE = 5.80

DAILY_VOLUMES = {
    "2025-12-07": 5, "2025-12-08": 6, "2025-12-09": 5, "2025-12-10": 3,
    "2025-12-11": 2, "2025-12-12": 1, "2025-12-13": 7, "2025-12-14": 2,
    "2025-12-15": 4, "2025-12-16": 6, "2025-12-17": 4, "2025-12-18": 7,
    "2025-12-19": 3, "2025-12-20": 5, "2025-12-21": 6, "2025-12-22": 1,
    "2025-12-23": 4, "2025-12-24": 4, "2025-12-25": 3, "2025-12-26": 5,
    "2025-12-27": 2, "2025-12-28": 5, "2025-12-29": 4, "2025-12-30": 6,
    "2025-12-31": 5, "2026-01-01": 2, "2026-01-02": 5, "2026-01-03": 3,
    "2026-01-04": 2, "2026-01-05": 6, "2026-01-06": 3, "2026-01-07": 5,
    "2026-01-08": 4, "2026-01-09": 2, "2026-01-10": 6, "2026-01-11": 1,
    "2026-01-12": 8, "2026-01-13": 4, "2026-01-14": 2, "2026-01-15": 5,
    "2026-01-16": 4, "2026-01-17": 5, "2026-01-18": 5, "2026-01-19": 4,
    "2026-01-20": 4, "2026-01-21": 5, "2026-01-22": 5, "2026-01-23": 2,
    "2026-01-24": 4, "2026-01-25": 7, "2026-01-26": 3, "2026-01-27": 6,
    "2026-01-28": 5, "2026-01-29": 2, "2026-01-30": 6, "2026-01-31": 8,
    "2026-02-01": 7, "2026-02-02": 6, "2026-02-03": 5, "2026-02-04": 27,
    "2026-02-05": 31, "2026-02-06": 21, "2026-02-09": 19,
}

TOTAL_INTERACTIONS = sum(DAILY_VOLUMES.values())

CHAT_CONTEXTS = [
    'chat_response', 'agent_reply', 'whatsapp_chat',
    'bot_conversation', 'assessor_query'
]
ESCALATION_CATEGORIES = [
    'duvida_operacional', 'consulta_produto', 'informacao_mercado',
    'regulatorio', 'tributacao', 'reclamacao_sistema'
]

def random_time(day_str):
    d = datetime.strptime(day_str, "%Y-%m-%d")
    h = random.randint(8, 18)
    m = random.randint(0, 59)
    s = random.randint(0, 59)
    return d.replace(hour=h, minute=m, second=s)


def create_chat_record(day_str, turns=1):
    records = []
    for _ in range(turns):
        input_tokens = random.randint(2800, 4200)
        output_tokens = random.randint(250, 500)
        total = input_tokens + output_tokens
        cost_input = input_tokens / 1_000_000 * 2.50
        cost_output = output_tokens / 1_000_000 * 10.00
        cost_usd = cost_input + cost_output
        records.append(CostTracking(
            service='openai',
            operation='chat_completion',
            model='gpt-4o',
            prompt_tokens=input_tokens,
            completion_tokens=output_tokens,
            total_tokens=total,
            cost_usd=round(cost_usd, 6),
            cost_brl=round(cost_usd * EXCHANGE_RATE, 4),
            exchange_rate=EXCHANGE_RATE,
            context=random.choice(CHAT_CONTEXTS),
            created_at=random_time(day_str)
        ))
    return records


def create_classification_record(day_str):
    input_tokens = random.randint(400, 600)
    output_tokens = random.randint(30, 80)
    total = input_tokens + output_tokens
    cost_usd = input_tokens / 1_000_000 * 0.15 + output_tokens / 1_000_000 * 0.60
    return CostTracking(
        service='openai',
        operation='intent_classification',
        model='gpt-4o-mini',
        prompt_tokens=input_tokens,
        completion_tokens=output_tokens,
        total_tokens=total,
        cost_usd=round(cost_usd, 6),
        cost_brl=round(cost_usd * EXCHANGE_RATE, 4),
        exchange_rate=EXCHANGE_RATE,
        context='message_classification',
        created_at=random_time(day_str)
    )


def create_insight_record(day_str):
    input_tokens = random.randint(800, 1200)
    output_tokens = random.randint(150, 350)
    total = input_tokens + output_tokens
    cost_usd = input_tokens / 1_000_000 * 0.15 + output_tokens / 1_000_000 * 0.60
    return CostTracking(
        service='openai',
        operation='insight_generation',
        model='gpt-4o-mini',
        prompt_tokens=input_tokens,
        completion_tokens=output_tokens,
        total_tokens=total,
        cost_usd=round(cost_usd, 6),
        cost_brl=round(cost_usd * EXCHANGE_RATE, 4),
        exchange_rate=EXCHANGE_RATE,
        context='post_conversation_analysis',
        created_at=random_time(day_str)
    )


def create_embedding_record(day_str, token_count, context):
    cost_usd = token_count / 1_000_000 * 0.13
    return CostTracking(
        service='openai',
        operation='embedding',
        model='text-embedding-3-large',
        prompt_tokens=token_count,
        completion_tokens=0,
        total_tokens=token_count,
        cost_usd=round(cost_usd, 6),
        cost_brl=round(cost_usd * EXCHANGE_RATE, 4),
        exchange_rate=EXCHANGE_RATE,
        context=context,
        created_at=random_time(day_str)
    )


def create_escalation_record(day_str):
    input_tokens = random.randint(1200, 1800)
    output_tokens = random.randint(200, 400)
    total = input_tokens + output_tokens
    cost_usd = input_tokens / 1_000_000 * 0.15 + output_tokens / 1_000_000 * 0.60
    return CostTracking(
        service='openai',
        operation='escalation_analysis',
        model='gpt-4o-mini',
        prompt_tokens=input_tokens,
        completion_tokens=output_tokens,
        total_tokens=total,
        cost_usd=round(cost_usd, 6),
        cost_brl=round(cost_usd * EXCHANGE_RATE, 4),
        exchange_rate=EXCHANGE_RATE,
        context=random.choice(ESCALATION_CATEGORIES),
        created_at=random_time(day_str)
    )


def main():
    db = SessionLocal()
    try:
        existing = db.query(CostTracking).count()
        if existing > 0:
            print(f"Já existem {existing} registros. Limpando para repopular...")
            db.query(CostTracking).delete()
            db.commit()

        all_records = []
        days = sorted(DAILY_VOLUMES.keys())
        total_volume = sum(DAILY_VOLUMES.values())

        escalation_days = random.sample(
            [d for d in days if DAILY_VOLUMES[d] >= 3], 
            min(69, len([d for d in days if DAILY_VOLUMES[d] >= 3]))
        )
        escalations_remaining = 69
        escalation_per_day = {}
        for d in escalation_days:
            if escalations_remaining <= 0:
                break
            n = min(random.randint(1, 3), escalations_remaining)
            escalation_per_day[d] = n
            escalations_remaining -= n
        if escalations_remaining > 0:
            for d in escalation_days:
                if escalations_remaining <= 0:
                    break
                escalation_per_day[d] = escalation_per_day.get(d, 0) + 1
                escalations_remaining -= 1

        tavily_days = random.sample(days, 9)
        
        audio_days = random.sample([d for d in days if DAILY_VOLUMES[d] >= 3], 15)

        doc_processing_days = ["2025-12-10", "2026-01-15", "2026-01-28"]

        chunk_enrichment_day = "2025-12-10"

        embedding_indexing_days = ["2025-12-10", "2026-01-15", "2026-01-28"]

        rag_remaining = 351
        rag_per_day = {}
        for d in days:
            proportion = DAILY_VOLUMES[d] / total_volume
            rag_per_day[d] = max(0, int(proportion * 351))
        leftover = 351 - sum(rag_per_day.values())
        for d in random.sample(days, abs(leftover)):
            rag_per_day[d] += 1 if leftover > 0 else -1

        chunk_embed_per_day = {}
        embed_days = ["2025-12-10", "2026-01-15", "2026-01-28"]
        chunks_each = [56, 56, 55]
        for i, d in enumerate(embed_days):
            chunk_embed_per_day[d] = chunks_each[i]

        turns_per_day = {}
        for d in days:
            proportion = DAILY_VOLUMES[d] / total_volume
            turns_per_day[d] = max(1, int(proportion * 885))
        leftover_turns = 885 - sum(turns_per_day.values())
        for d in random.sample(days, abs(leftover_turns)):
            turns_per_day[d] += 1 if leftover_turns > 0 else -1

        for day_str in days:
            volume = DAILY_VOLUMES[day_str]
            
            total_turns = turns_per_day[day_str]
            all_records.extend(create_chat_record(day_str, total_turns))

            for _ in range(total_turns):
                all_records.append(create_classification_record(day_str))

            for _ in range(volume):
                all_records.append(create_insight_record(day_str))

            for _ in range(rag_per_day.get(day_str, 0)):
                query_tokens = random.randint(30, 80)
                all_records.append(create_embedding_record(day_str, query_tokens, 'rag_query'))

            if day_str in escalation_per_day:
                for _ in range(escalation_per_day[day_str]):
                    all_records.append(create_escalation_record(day_str))

            if day_str in tavily_days:
                cost_usd = 0.01
                all_records.append(CostTracking(
                    service='tavily',
                    operation='web_search',
                    model=None,
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    cost_usd=cost_usd,
                    cost_brl=round(cost_usd * EXCHANGE_RATE, 4),
                    exchange_rate=EXCHANGE_RATE,
                    context='market_data_search',
                    created_at=random_time(day_str)
                ))

            if day_str in audio_days:
                duration = random.uniform(15, 60)
                cost_usd = (duration / 60) * 0.006
                all_records.append(CostTracking(
                    service='openai',
                    operation='audio_transcription',
                    model='whisper-1',
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    audio_duration_seconds=round(duration, 1),
                    cost_usd=round(cost_usd, 6),
                    cost_brl=round(cost_usd * EXCHANGE_RATE, 4),
                    exchange_rate=EXCHANGE_RATE,
                    context='whatsapp_audio',
                    created_at=random_time(day_str)
                ))

            if day_str in doc_processing_days:
                input_tokens = random.randint(6000, 10000)
                output_tokens = random.randint(2000, 4000)
                cost_usd = input_tokens / 1_000_000 * 2.50 + output_tokens / 1_000_000 * 10.00
                all_records.append(CostTracking(
                    service='openai',
                    operation='document_extraction',
                    model='gpt-4o',
                    prompt_tokens=input_tokens,
                    completion_tokens=output_tokens,
                    total_tokens=input_tokens + output_tokens,
                    cost_usd=round(cost_usd, 6),
                    cost_brl=round(cost_usd * EXCHANGE_RATE, 4),
                    exchange_rate=EXCHANGE_RATE,
                    context='pdf_extraction_vision',
                    created_at=random_time(day_str)
                ))
                meta_input = random.randint(1500, 2500)
                meta_output = random.randint(300, 700)
                meta_cost = meta_input / 1_000_000 * 2.50 + meta_output / 1_000_000 * 10.00
                all_records.append(CostTracking(
                    service='openai',
                    operation='metadata_extraction',
                    model='gpt-4o',
                    prompt_tokens=meta_input,
                    completion_tokens=meta_output,
                    total_tokens=meta_input + meta_output,
                    cost_usd=round(meta_cost, 6),
                    cost_brl=round(meta_cost * EXCHANGE_RATE, 4),
                    exchange_rate=EXCHANGE_RATE,
                    context='document_metadata',
                    created_at=random_time(day_str)
                ))

            if day_str in chunk_embed_per_day:
                for _ in range(chunk_embed_per_day[day_str]):
                    chunk_tokens = random.randint(300, 700)
                    all_records.append(create_embedding_record(day_str, chunk_tokens, 'chunk_indexing'))

            if day_str == chunk_enrichment_day:
                for _ in range(55):
                    input_tokens = random.randint(600, 1000)
                    output_tokens = random.randint(200, 400)
                    cost_usd = input_tokens / 1_000_000 * 0.15 + output_tokens / 1_000_000 * 0.60
                    all_records.append(CostTracking(
                        service='openai',
                        operation='chunk_enrichment',
                        model='gpt-4o-mini',
                        prompt_tokens=input_tokens,
                        completion_tokens=output_tokens,
                        total_tokens=input_tokens + output_tokens,
                        cost_usd=round(cost_usd, 6),
                        cost_brl=round(cost_usd * EXCHANGE_RATE, 4),
                        exchange_rate=EXCHANGE_RATE,
                        context='semantic_enrichment',
                        created_at=random_time(day_str)
                    ))

        db.bulk_save_objects(all_records)
        db.commit()

        total_usd = sum(r.cost_usd for r in all_records)
        total_brl = sum(r.cost_brl for r in all_records)

        print(f"\n{'='*60}")
        print(f"DADOS HISTÓRICOS INSERIDOS COM SUCESSO")
        print(f"{'='*60}")
        print(f"Total de registros: {len(all_records)}")
        print(f"Período: {days[0]} a {days[-1]}")
        print(f"Custo total estimado: US$ {total_usd:.2f} (R$ {total_brl:.2f})")
        print(f"{'='*60}")

        services = {}
        for r in all_records:
            key = f"{r.service}/{r.operation}"
            if key not in services:
                services[key] = {'count': 0, 'usd': 0}
            services[key]['count'] += 1
            services[key]['usd'] += r.cost_usd

        print(f"\nDetalhamento por operação:")
        print(f"{'Operação':<40} {'Qtd':>6} {'USD':>10}")
        print(f"{'-'*58}")
        for key in sorted(services, key=lambda k: services[k]['usd'], reverse=True):
            s = services[key]
            print(f"{key:<40} {s['count']:>6} ${s['usd']:>9.4f}")

    except Exception as e:
        db.rollback()
        print(f"Erro: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
