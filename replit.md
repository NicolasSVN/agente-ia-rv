# Agente IA - RV - Agente de IA para Assessores Financeiros

## Overview
Stevan is a FastAPI-based AI agent designed to enhance efficiency for financial advisors by centralizing information, automating routine tasks, and improving client interactions. Its core purpose is to leverage AI for natural language understanding to provide intelligent support and streamline workflows for financial advisors. Key capabilities include WhatsApp integration, semantic search within a product knowledge base, and an administrative panel for analytics, user management, and campaign tools.

## User Preferences
Prefiro explicações detalhadas.
Quero um processo de desenvolvimento iterativo.
Pergunte antes de fazer mudanças arquiteturais significativas.
Garanta que o código seja bem documentado e legível.
Foque em boas práticas de segurança.
Prefiro um design de UI limpo e minimalista.
Garanta que todos os textos voltados ao usuário estejam em português gramaticalmente correto com acentuação adequada.
**CRÍTICO: NUNCA perca funcionalidades existentes ao fazer mudanças.** Sempre verifique se as funcionalidades implementadas anteriormente permanecem intactas. Antes de modificar qualquer componente, revise quais funcionalidades existem e garanta que sejam preservadas. Chame o architect para validar mudanças de UX.

## System Architecture
The application is built using FastAPI with a modular architecture.

**UI/UX Decisions:** The design system features a minimizable vertical sidebar, light theme, and Inter font. Global CSS centralizes styling, navigation is dynamic based on user roles, and a custom toast notification system provides consistent feedback. Modern React + Tailwind screens exclusively use Tailwind Preflight and utilities for spacing and styling, ensuring a modern SaaS-style user experience.

**Technical Implementations:**
- **AI Agent (Stevan) — Pipeline V2 Agentic RAG:** Uses OpenAI function calling in an iterative loop (MAX_ITERATIONS=3) where GPT decides when to search. Architecture: `services/agent_tools.py` (5 tools: search_knowledge_base, search_web, lookup_fii_public, send_document, send_payoff_diagram), `services/agent_prompt.py` (modular system prompt), `generate_response_v2` in `openai_agent.py` (agentic loop). Key change: user message is sent raw (no context injected in user turn) — GPT decides via tool-calling what information to fetch. Parallel tool execution via asyncio.gather. The old V1 pipeline (`generate_response`) is preserved but unused — both WhatsApp and Testar Agente use V2.
- **Semantic Search (RAG V3.2 Enhanced):** Utilizes `pgvector (PostgreSQL)` and OpenAI `text-embedding-3-large` with hybrid ranking, intelligent ticker detection (regex `[A-Z]{4}[0-9]{1,2}` for stocks like CPLE3, VALE3 + extended pattern for FIIs like BTLG11), a financial glossary for query expansion, and semantic enrichment. Content blocks with JSON tabular data are resolved at query time via `services/content_formatter.py` — original content_block values are looked up and converted to readable text before being injected into the AI context. Indexing uses `index_approved_blocks` only, and product/material deletion automatically cleans vector store embeddings. Includes Temporal Reference Enrichment (`services/temporal_enrichment.py`): at query time, content blocks with quantitative data but no temporal reference are enriched by inspecting ±2 neighbor blocks (by `order` within the same `material_id`) for dates/periods, prefixing the content with `[Ref.Temporal: ...]`. This is read-only (no DB writes) and non-blocking.
- **Manager Disambiguation V2 (GPT-driven):** The Query Rewriter (`services/query_rewriter.py`) includes a `manager_query` field where GPT-4o semantically determines if the user is asking about a financial manager. This replaced the old substring-matching approach (`if "xp" in query_lower`) that caused false positives (e.g., "explicar" → "xp" → XP Asset). The `_check_manager_disambiguation_gpt` method in `openai_agent.py` uses the GPT decision to list available products and allow selection. Unrecognized responses to disambiguation now fall through to normal RAG instead of failing silently.
- **AI Document Summaries:** Automatic conceptual summaries and theme generation for documents using GPT-4o-mini.
- **Semantic Transformer:** A 3-layer architecture processes content through technical extraction (GPT-4 Vision), semantic modeling, and narrative chunk generation for RAG indexing.
- **XPI Derivatives System:** A comprehensive knowledge base for structured products with a 4-step conversational disambiguation flow, including content extracted via GPT-4 Vision and payoff diagrams.
- **External FIIs Query:** Automatically fetches public FII data from FundsExplorer.com.br.
- **WhatsApp Integration:** Uses Z-API for various message types, logs interactions, and provides a "Message Center" interface with real-time updates. Supports full media processing, including optimized audio transcription (Whisper) and image/document analysis. Includes message debounce (12s `asyncio` timer per phone to accumulate rapid messages), persistent conversation history loaded from `whatsapp_messages` table (survives deploys), and hierarchical memory: session active (last 20 messages), incremental summary (every 20 messages, compacts older half into summary), session gap summary (2h gap triggers GPT summary stored in `conversations.last_session_summary`), full history in DB. **Pipeline V2:** WhatsApp webhook calls `generate_response_v2` directly — GPT decides tool usage autonomously. Action tool calls (send_document, send_payoff_diagram) are processed post-response. Human handoff via `request_human_handoff` tool triggers ticket creation. Failed document sends notify the user with a retry prompt.
- **Testar Agente (agent_test.py):** Pipeline V2 equalizado com WhatsApp — usa `generate_response_v2`, normalize_message, resumo de sessão in-memory (gap de 2h), RetrievalLog para auditoria. Response includes tool_calls, pipeline, iterations, elapsed_ms.
- **Authentication and Authorization:** JWT-based with role-based access control, JWT hardening, rate limiting, account lockout, and comprehensive security headers. Global auth middleware is implemented, and structured security event logging is used.
- **Database:** PostgreSQL (or SQLite for development) with SQLAlchemy ORM.
- **Admin Panel:** Provides tools for user, integration, advisor, and campaign management, a "Message Center," and knowledge base management.
- **Product CMS:** Manages products, materials, and content blocks, featuring PDF upload with GPT-4 Vision extraction, approval system, semantic indexing, WhatsApp scripts, versioning, and validity control. PDFs are persistently stored in PostgreSQL (`material_files` table with `bytea`) to survive container deploys. Public download endpoint at `/api/files/{material_id}/download` (no auth) allows Z-API to fetch and send documents via WhatsApp. Admin endpoint `/api/products/admin/materials-without-files` lists materials missing PDF files. WhatsApp document sending now returns specific error messages: "arquivo não disponível" for missing files vs generic retry for transient errors. AI prompt enforces that `send_document` only be called for materials listed in the "Materiais com PDF disponível" context section. **Unified Pending Materials:** `/api/products/materials/pending-unified` endpoint consolidates all materials needing action — missing PDFs (success with blocks but no file) and failed processing — into a single view in SmartUpload. Includes duplicate detection (flags failed materials that have success versions) and bulk drag-and-drop PDF re-upload with auto-matching by ticker. The old standalone Re-upload PDFs page (`/admin/reupload-pdfs`) was removed and absorbed into SmartUpload.
- **Intelligent Upload with Metadata Extraction:** `DocumentMetadataExtractor` service uses GPT-4 Vision to analyze PDFs and extract metadata for automated product matching or creation. Adaptive DPI is used for PDF rendering.
- **Dependency Health Check:** `services/dependency_check.py` validates critical dependencies on startup, and `/api/health/detailed` provides real-time status.
- **Observability and Auditing:** Includes `RetrievalLog` for RAG searches, `IngestionLog` for document ingestion, RAG analytics, and content block tracking.
- **AI Agent Response Framework:** Utilizes a `ConversationState` machine, message normalization, contact identification, and AI-based intent classification for human transfer.
- **Escalation Intelligence V2.1:** GPT analysis on each escalation with 11 categories, auto-generating ticket summaries.
- **Bot Resolution Tracking V2.2:** Tracks bot-resolved conversations, including resolution metrics.
- **Separate Ticket Architecture V2.3:** `Conversation` and `ConversationTicket` are separate models, allowing continuous chat sessions with distinct historical data.
- **Insights Dashboard:** A management dashboard for Variable Income with `ConversationInsight` model, post-conversation GPT analysis, classification categories, dynamic filters, KPI cards, Chart.js graphs, rankings, and campaign summaries.
- **Web Search (Tavily AI):** Fallback for real-time market data when internal knowledge is insufficient, including a whitelist of trusted sources and an audit log.
- **Deployment Strategy:** Migrated from Replit to Railway via GitHub. The Dockerfile uses `python:3.12-slim` with necessary system dependencies. React frontend builds are pre-compiled in Replit and committed to the repository, as the Dockerfile is Python-only. **IMPORTANT:** The production `main.py` serves React assets from `frontend/react-knowledge/dist/` (NOT `frontend/static/react-knowledge/`). Always build with default output: `cd frontend/react-knowledge && npx vite build` (outputs to `dist/`). Commit the `dist/` directory for Railway deployment.

**Feature Specifications:** Dynamic control over AI behavior parameters, real-time campaign sending with SSE, background document processing, customizable fields, and automatic admin user creation.

## External Dependencies
- **API OpenAI:** AI agent interactions and text embeddings.
- **Z-API:** WhatsApp messaging integration.
- **Tavily AI:** Web search for real-time market data.
- **PostgreSQL:** Primary relational database.
- **pgvector:** PostgreSQL extension for vector storage and search.
- **Jinja2:** Templating engine.
- **Inter (Google Fonts):** Typography.
- **Tailwind CSS:** Utility-first CSS framework.
- **React 18 + Vite + React Router DOM:** Modern Knowledge Base UI.
- **Radix UI:** UI components (Dialog, Tabs, Select, Tooltip).
- **Framer Motion:** Animations and transitions.
- **Lucide React:** Icons.
- **react-dropzone:** File uploads.