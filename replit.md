# Agente IA - RV - Agente de IA para Assessores Financeiros

## Overview
This project is a comprehensive FastAPI application named Stevan, an AI agent designed for financial advisors. Its primary goal is to enhance efficiency in financial advisory services by centralizing information, automating routine tasks, and improving client interaction. Key capabilities include WhatsApp integration, semantic search on a Product CMS knowledge base, and an administrative dashboard with analytics, user management, and campaign tools.

## User Preferences
I prefer detailed explanations.
I want an iterative development process.
Ask before making major architectural changes.
Ensure code is well-documented and readable.
Focus on security best practices.
I prefer a clean and minimalist UI design.
Ensure all user-facing texts are in grammatically correct Portuguese with proper accentuation.
**CRITICAL: NEVER lose existing functionality when making changes.** Always verify that previously implemented features remain intact. Before modifying any component, review what features exist and ensure they are preserved. Call architect to validate UX changes.

## System Architecture
The application is built using FastAPI with a modular architecture.

**UI/UX Decisions:** The design system features a minimizable vertical sidebar, a light theme, and the Inter font. Global CSS centralizes styling, navigation is dynamic based on user roles, and a custom toast notification system provides consistent feedback. Modern React + Tailwind screens utilize Tailwind Preflight and utilities exclusively for spacing and styling, ensuring a modern SaaS-like user experience.

**Technical Implementations:**
- **AI Agent (Stevan):** Integrates OpenAI for chat and embeddings, configurable for personality, rules, and model parameters. It acts as an internal support broker, explaining strategies and products, and escalating to human specialists.
- **Semantic Search (V3.0 Enhanced RAG):** Employs ChromaDB and OpenAI text-embedding-3-large with hybrid ranking (vector, recency, exact_match). Chunks include global context.
- **AI Document Summaries:** Automatic generation of conceptual summaries and themes for each document using GPT-4o-mini, stored in the material model.
- **Semantic Transformer (3-Layer Architecture):** Processes content through technical extraction (GPT-4 Vision), semantic model (data normalization), and narrative chunk generation for RAG indexing.
- **FII External Lookup:** Automatically fetches public FII data from FundsExplorer.com.br.
- **WhatsApp Integration:** Uses Z-API for various message types, logs interactions, and provides a "Central de Mensagens" interface with real-time updates and conversation identification, including full media support (audio transcription, image analysis, document processing).
- **Authentication & Authorization:** JWT-based with role-based access control.
- **Database:** PostgreSQL (or SQLite for development) with SQLAlchemy ORM.
- **Admin Dashboard:** Provides tools for user, integration, advisor, and campaign management, a "Central de Mensagens", and knowledge base management.
- **Product CMS:** Manages products, materials, and content blocks, featuring PDF upload with GPT-4 Vision extraction, an approval system, semantic indexing, WhatsApp scripts, versioning, and validity control.
- **Smart Upload with Metadata Extraction:** `DocumentMetadataExtractor` service uses GPT-4 Vision to analyze PDFs, extracting metadata like fund_name, ticker, gestora, and document_type, with automated product matching or creation.
- **Observability and Auditing:** Includes `RetrievalLog` for RAG search, `IngestionLog` for document ingestion, RAG analytics, intelligent re-ranking, and content block tracking.
- **AI Agent Response Framework:** Utilizes a `ConversationState` machine, message normalization, contact identification, and AI-driven intent classification for human transfer.
- **V2.1 Escalation Intelligence:** GPT-powered analysis on every escalation with 11 categories, auto-generating ticket summaries and conversation topics, and tracking key timestamps.
- **V2.2 Bot Resolution Tracking:** Tracks conversations resolved by the bot, includes `bot_resolved_at` and `awaiting_confirmation` fields, a background scheduler for confirmation messages, and metrics on bot resolution.
- **V2.3 Separated Ticket Architecture:** `Conversation` and `ConversationTicket` are separate models, allowing continuous chat sessions with distinct historical data for each human intervention, tracking resolution metrics per ticket.
- **Insights Dashboard:** A management dashboard for Variable Income with `ConversationInsight` model, GPT-based post-conversation analysis, 12 classification categories, dynamic filters, KPI cards, Chart.js graphs, rankings, and campaign summaries.

**Feature Specifications:** Dynamic control over AI behavior parameters, real-time campaign dispatch with SSE, background document processing, customizable fields, and automated admin user creation.

## External Dependencies
- **OpenAI API:** AI agent interactions and text embeddings.
- **Z-API:** WhatsApp messaging integration.
- **PostgreSQL:** Primary relational database.
- **ChromaDB:** Vector database for semantic search.
- **Jinja2:** Templating engine.
- **Inter Font (Google Fonts):** Typography.
- **Tailwind CSS:** Utility-first CSS framework.
- **React 18 + Vite + React Router DOM:** Modern Knowledge Base UI.
- **Radix UI:** UI components (Dialog, Tabs, Select, Tooltip).
- **Framer Motion:** Animations and transitions.
- **Lucide React:** Icons.
- **react-dropzone:** File uploads.