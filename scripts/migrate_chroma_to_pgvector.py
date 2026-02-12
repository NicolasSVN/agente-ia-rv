"""
Script de migração ChromaDB → pgvector.
Transfere todos os documentos/embeddings existentes do ChromaDB local para PostgreSQL.
Custo zero: reutiliza embeddings já gerados, sem chamar OpenAI.

Uso: python scripts/migrate_chroma_to_pgvector.py
"""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chromadb
from core.config import get_settings
from database.database import SessionLocal
from sqlalchemy import text as sql_text

settings = get_settings()

KNOWN_METADATA_FIELDS = {
    'product_name', 'product_ticker', 'gestora', 'category', 'source',
    'title', 'block_type', 'material_type', 'publish_status', 'topic',
    'concepts', 'keywords', 'strategy', 'valid_until', 'structure_slug',
    'tab', 'has_diagram', 'diagram_image_path', 'block_id', 'material_id',
}

FIELD_MAP = {
    'created_at': 'created_at_source',
    'type': 'doc_type',
}


def migrate():
    print("=" * 60)
    print("MIGRAÇÃO ChromaDB → pgvector")
    print("=" * 60)

    try:
        client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)
        collection = client.get_or_create_collection("knowledge_base")
        total = collection.count()
        print(f"\nDocumentos no ChromaDB: {total}")
    except Exception as e:
        print(f"ERRO ao acessar ChromaDB: {e}")
        return

    if total == 0:
        print("Nenhum documento para migrar.")
        return

    batch_size = 100
    migrated = 0
    skipped = 0
    errors = 0

    db = SessionLocal()
    try:
        existing = db.execute(sql_text("SELECT COUNT(*) FROM document_embeddings")).scalar()
        print(f"Documentos já no pgvector: {existing}")

        offset = 0
        while offset < total:
            results = collection.get(
                limit=batch_size,
                offset=offset,
                include=['documents', 'metadatas', 'embeddings']
            )

            if not results or not results['ids']:
                break

            for i, doc_id in enumerate(results['ids']):
                try:
                    content = results['documents'][i] if results['documents'] else ""
                    metadata = results['metadatas'][i] if results['metadatas'] else {}
                    embedding = results['embeddings'][i] if results['embeddings'] else None

                    if not embedding:
                        print(f"  SKIP {doc_id}: sem embedding")
                        skipped += 1
                        continue

                    if not content:
                        content = ""

                    embedding_str = '[' + ','.join(str(v) for v in embedding) + ']'

                    columns = {
                        'doc_id': doc_id,
                        'content': content,
                    }

                    for key, value in metadata.items():
                        mapped_key = FIELD_MAP.get(key, key)

                        if mapped_key in KNOWN_METADATA_FIELDS or mapped_key in ('created_at_source', 'doc_type'):
                            if value is not None:
                                columns[mapped_key] = str(value) if not isinstance(value, str) else value

                    extra = {}
                    for key, value in metadata.items():
                        mapped_key = FIELD_MAP.get(key, key)
                        if mapped_key not in KNOWN_METADATA_FIELDS and mapped_key not in ('created_at_source', 'doc_type'):
                            extra[key] = value
                    if extra:
                        columns['extra_metadata'] = json.dumps(extra, ensure_ascii=False)

                    col_names = list(columns.keys()) + ['embedding']
                    placeholders = [f':{k}' for k in columns.keys()] + [f"'{embedding_str}'::vector"]

                    update_parts = []
                    for k in columns.keys():
                        if k != 'doc_id':
                            update_parts.append(f"{k} = EXCLUDED.{k}")
                    update_parts.append("embedding = EXCLUDED.embedding")
                    update_parts.append("updated_at = CURRENT_TIMESTAMP")

                    sql = f"""
                        INSERT INTO document_embeddings ({', '.join(col_names)})
                        VALUES ({', '.join(placeholders)})
                        ON CONFLICT (doc_id) DO UPDATE SET
                        {', '.join(update_parts)}
                    """

                    db.execute(sql_text(sql), columns)
                    migrated += 1

                    if migrated % 50 == 0:
                        db.commit()
                        print(f"  Progresso: {migrated}/{total} migrados...")

                except Exception as e:
                    errors += 1
                    print(f"  ERRO ao migrar {doc_id}: {e}")

            offset += batch_size

        db.commit()

        final_count = db.execute(sql_text("SELECT COUNT(*) FROM document_embeddings")).scalar()

        print(f"\n{'=' * 60}")
        print(f"MIGRAÇÃO CONCLUÍDA")
        print(f"{'=' * 60}")
        print(f"  Migrados: {migrated}")
        print(f"  Ignorados: {skipped}")
        print(f"  Erros: {errors}")
        print(f"  Total no pgvector: {final_count}")
        print(f"{'=' * 60}")

    except Exception as e:
        db.rollback()
        print(f"ERRO FATAL na migração: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
