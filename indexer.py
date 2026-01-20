"""
Script autônomo para popular a base de dados vetorial a partir do Notion.
Lê páginas de um banco de dados do Notion, extrai texto, gera embeddings
e armazena no ChromaDB.

Uso:
    python indexer.py
"""
import os
import httpx
from typing import List, Dict, Any
from openai import OpenAI
import chromadb

# Configurações
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
CHROMA_PERSIST_DIRECTORY = "./chroma_db"


def get_notion_pages(database_id: str, api_key: str) -> List[Dict[str, Any]]:
    """
    Busca todas as páginas de um banco de dados do Notion.
    """
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    all_pages = []
    has_more = True
    start_cursor = None
    
    while has_more:
        payload = {}
        if start_cursor:
            payload["start_cursor"] = start_cursor
        
        response = httpx.post(url, headers=headers, json=payload, timeout=30.0)
        response.raise_for_status()
        data = response.json()
        
        all_pages.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")
    
    return all_pages


def get_page_content(page_id: str, api_key: str) -> str:
    """
    Busca o conteúdo de uma página do Notion (blocos de texto).
    """
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": "2022-06-28"
    }
    
    response = httpx.get(url, headers=headers, timeout=30.0)
    response.raise_for_status()
    blocks = response.json().get("results", [])
    
    content_parts = []
    
    for block in blocks:
        block_type = block.get("type")
        block_data = block.get(block_type, {})
        
        # Extrai texto de diferentes tipos de blocos
        rich_text = block_data.get("rich_text", [])
        for text_obj in rich_text:
            text = text_obj.get("plain_text", "")
            if text:
                content_parts.append(text)
    
    return " ".join(content_parts)


def extract_page_title(page: Dict[str, Any]) -> str:
    """
    Extrai o título de uma página do Notion.
    """
    properties = page.get("properties", {})
    
    # Tenta encontrar a propriedade de título
    for prop_name, prop_value in properties.items():
        if prop_value.get("type") == "title":
            title_list = prop_value.get("title", [])
            if title_list:
                return title_list[0].get("plain_text", "Sem título")
    
    return "Sem título"


def generate_embedding(text: str, client: OpenAI) -> List[float]:
    """
    Gera embedding para o texto usando o modelo text-embedding-3-small.
    """
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def main():
    """
    Função principal que executa a indexação.
    """
    print("=" * 50)
    print("Iniciando indexação do Notion para ChromaDB")
    print("=" * 50)
    
    # Verifica configurações
    if not NOTION_API_KEY:
        print("ERRO: NOTION_API_KEY não configurada.")
        print("Configure a variável de ambiente NOTION_API_KEY com sua chave da API do Notion.")
        return
    
    if not NOTION_DATABASE_ID:
        print("ERRO: NOTION_DATABASE_ID não configurado.")
        print("Configure a variável de ambiente NOTION_DATABASE_ID com o ID do seu banco de dados.")
        return
    
    if not OPENAI_API_KEY:
        print("ERRO: OPENAI_API_KEY não configurada.")
        print("Configure a variável de ambiente OPENAI_API_KEY com sua chave da OpenAI.")
        return
    
    # Inicializa clientes
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    
    chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIRECTORY)
    
    # Cria ou limpa a coleção
    try:
        chroma_client.delete_collection("knowledge_base")
    except:
        pass
    
    collection = chroma_client.create_collection(
        name="knowledge_base",
        metadata={"description": "Base de conhecimento do Notion"}
    )
    
    print(f"\nBuscando páginas do banco de dados: {NOTION_DATABASE_ID}")
    
    try:
        pages = get_notion_pages(NOTION_DATABASE_ID, NOTION_API_KEY)
        print(f"Encontradas {len(pages)} páginas.\n")
    except Exception as e:
        print(f"ERRO ao buscar páginas do Notion: {e}")
        return
    
    # Processa cada página
    for i, page in enumerate(pages, 1):
        page_id = page.get("id", "")
        title = extract_page_title(page)
        
        print(f"[{i}/{len(pages)}] Processando: {title}")
        
        try:
            # Busca conteúdo da página
            content = get_page_content(page_id, NOTION_API_KEY)
            
            if not content.strip():
                print(f"  -> Página vazia, pulando...")
                continue
            
            # Combina título e conteúdo para o embedding
            full_text = f"{title}\n\n{content}"
            
            # Gera embedding
            embedding = generate_embedding(full_text, openai_client)
            
            # Adiciona ao ChromaDB
            collection.add(
                ids=[page_id],
                embeddings=[embedding],
                documents=[full_text],
                metadatas=[{
                    "title": title,
                    "notion_id": page_id,
                    "source": "notion"
                }]
            )
            
            print(f"  -> Indexado com sucesso! ({len(content)} caracteres)")
            
        except Exception as e:
            print(f"  -> ERRO: {e}")
    
    # Os dados são persistidos automaticamente com PersistentClient
    
    print("\n" + "=" * 50)
    print(f"Indexação concluída!")
    print(f"Total de documentos indexados: {collection.count()}")
    print("=" * 50)


if __name__ == "__main__":
    main()
