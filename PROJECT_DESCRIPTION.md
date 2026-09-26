# Feedback Intelligence System: Complete Project Description

## Executive Summary

The Feedback Intelligence System is a comprehensive, production-ready platform designed to transform raw customer feedback and knowledge base documents into actionable business insights through the power of artificial intelligence, semantic search, and advanced analytics. Built with modern Python frameworks and leveraging state-of-the-art language models, this end-to-end solution enables organizations to ingest, analyze, search, and query customer feedback at scale while maintaining enterprise-grade reliability and security.

## Project Overview and Purpose

In today's data-driven business landscape, organizations receive vast amounts of unstructured customer feedback through multiple channels—product reviews, support tickets, NPS surveys, social media mentions, and direct user communications. Extracting meaningful insights from this deluge of information requires sophisticated natural language processing, intelligent categorization, and powerful search capabilities. The Feedback Intelligence System addresses these challenges by providing a unified platform that automates the entire feedback analysis pipeline from ingestion to intelligent querying.

The system serves multiple stakeholders: product managers seeking to understand feature requests and complaints, customer success teams identifying emerging issues, data analysts generating insights, and executives making strategic decisions based on customer sentiment trends. By combining automated AI labeling, semantic search powered by vector embeddings, and advanced RAG (Retrieval-Augmented Generation) capabilities, the platform transforms raw textual data into structured, queryable, and actionable intelligence.

## Architecture and Technology Stack

The system follows a clean, modular architecture with clear separation between frontend presentation, backend API services, data persistence, and machine learning components. The technology stack is carefully chosen for performance, scalability, and developer productivity.

### Backend Infrastructure

The backend is built on **FastAPI**, a modern, high-performance Python web framework that provides automatic OpenAPI documentation, type validation through Pydantic, and asynchronous request handling. FastAPI's dependency injection system enables clean database session management and service layer organization. The application exposes a RESTful API with comprehensive endpoints for all system operations, accessible via Swagger UI for interactive testing and documentation.

**PostgreSQL** serves as the primary database, chosen for its robustness, ACID compliance, and extensibility. The system leverages the **pgvector** extension, which enables native vector similarity search within the database. This approach eliminates the need for separate vector databases like Pinecone or Weaviate, reducing infrastructure complexity while maintaining excellent query performance. All database interactions are handled through **SQLAlchemy ORM**, providing type-safe query construction, relationship management, and automatic schema migrations.

### Machine Learning and AI Components

The system employs a dual-model approach for different AI tasks. **SentenceTransformers** with the BGE-small-en-v1.5 model generates 384-dimensional embeddings for semantic search. This model balances accuracy and computational efficiency, enabling real-time similarity search across thousands of feedback items and knowledge base chunks. Embeddings are generated on-demand during ingestion and stored directly in PostgreSQL using the pgvector extension.

For natural language understanding and generation, the system integrates with **Groq**, a high-performance inference platform that provides fast LLM responses. The Groq client supports configurable model selection (defaulting to llama3-8b-8192), allowing teams to choose between different model sizes based on latency and quality requirements. All LLM interactions use structured prompting techniques to ensure consistent, parseable outputs for sentiment analysis, categorization, and RAG-based question answering.

### Frontend Dashboard

The user interface is built with **Streamlit**, a Python framework that enables rapid development of interactive data applications. The frontend is organized as a multipage application with dedicated sections for ingestion, analytics, search, and AI-powered querying. Streamlit's reactive programming model ensures that UI components automatically update when backend data changes, providing a seamless user experience without manual page refreshes.

## Core Components and Features

### 1. Data Ingestion Module

The ingestion system supports multiple data sources and formats. For customer feedback, the system accepts CSV and JSON files with flexible schema support. Each ingestion run is tracked in the `ingestion_runs` table, recording total rows, successfully ingested items, rejected rows, and detailed error logs. This audit trail enables administrators to troubleshoot data quality issues and track ingestion history.

Feedback items capture comprehensive metadata: external IDs for cross-system integration, source system identifiers (review platforms, ticketing systems, surveys), user identifiers, locale information for international support, product names, version numbers, and timestamps. The raw payload is preserved as JSONB, allowing future extraction of additional metadata without schema changes.

For knowledge base documents, the system supports TXT, Markdown, and PDF files. Documents are stored in their entirety in the `kb_docs` table, then automatically chunked using configurable text splitting strategies. Chunks are sized appropriately for embedding generation and retrieval, typically between 200-500 words with overlap to maintain context continuity.

### 2. AI-Powered Labeling Service

The labeling service automates the classification of feedback using Groq's language models. The system employs a taxonomy-based approach, loading predefined categories (Bug, Feature Request, Complaint, Praise, Usability, Documentation, Performance, Pricing, Support, Security) and aspects from JSON configuration files. This ensures consistency across labeling runs and enables easy taxonomy updates without code changes.

For each feedback item, the labeling service constructs a carefully crafted prompt that instructs the LLM to classify sentiment (positive, neutral, negative), assign a primary category, and extract relevant aspects. The prompt enforces strict JSON output formatting, enabling reliable parsing. Confidence scores are assigned based on the model's certainty, though the current implementation uses fixed values that could be enhanced with token probability extraction.

The service supports both batch processing (labeling all unlabeled items) and incremental labeling (processing a limited number of recent items). This flexibility allows teams to balance processing costs with labeling coverage, running incremental labeling during regular operations and batch processing during initial system setup or periodic backfills.

### 3. Embedding Generation and Vector Indexing

Embedding generation transforms textual content into dense vector representations that capture semantic meaning. The system uses the BGE-small-en-v1.5 model, which produces 384-dimensional vectors optimized for English text. This dimensionality balances expressiveness with storage efficiency and query performance.

For feedback items, embeddings are generated from the raw text, enabling semantic search that understands intent beyond keyword matching. For knowledge base content, embeddings are generated at the chunk level, allowing precise retrieval of relevant document sections. All embeddings are stored using PostgreSQL's native vector type via pgvector, enabling efficient cosine similarity searches using indexes optimized for approximate nearest neighbor queries.

The system maintains a unified `search_index` table that combines feedback items and knowledge base chunks, enabling cross-domain semantic search. Each index entry includes metadata (product, locale, source type) and references back to the original source, maintaining full traceability while enabling unified retrieval.

### 4. Semantic Search Capabilities

The search service provides flexible, powerful semantic search across all indexed content. Queries are embedded using the same BGE model, ensuring query-document compatibility. The service supports filtering by product, locale, and reference type (feedback vs. knowledge base), enabling targeted searches within specific domains.

Search results include similarity scores, allowing users to assess relevance. The top_k parameter controls result count, and the system uses pgvector's cosine distance operator for efficient ranking. Results maintain full metadata context, including source references, timestamps, and original text, enabling users to drill down into retrieved items for detailed analysis.

### 5. Retrieval-Augmented Generation (RAG)

The RAG service combines semantic search with language model generation to answer complex questions. When a user submits a query, the system retrieves the most relevant chunks from the unified search index, constructs a context-rich prompt that includes retrieved sources, and generates a coherent answer that cites specific sources.

The RAG prompt includes explicit instructions to use only provided sources, preventing hallucination and ensuring answers are grounded in actual data. Source citations are included in the response, allowing users to verify claims and explore referenced materials. The service uses lower temperature settings (0.2) to ensure factual accuracy over creative expression.

### 6. Agentic Query Planner

The agent service represents the system's most sophisticated component, implementing an intelligent query planner that determines the optimal approach for answering questions. The planner analyzes user queries to detect intent and orchestrates multiple data sources accordingly.

For queries requesting statistics or trends (e.g., "What are the top complaints this month?"), the planner triggers the stats computation module, which executes whitelisted SQL aggregations. This security-focused approach uses parameterized queries and limits available operations to prevent SQL injection while enabling common analytics patterns. The stats module supports sentiment trend analysis, top category extraction, and keyword-filtered aggregations.

For queries requesting examples ("Show me complaints about battery life"), the planner retrieves relevant feedback items either through keyword matching or semantic search, prioritizing recent items and maintaining relevance to the query topic.

For explanatory queries ("Why are users complaining about performance?"), the planner invokes the RAG service to generate context-aware explanations based on retrieved knowledge base content and relevant feedback.

The planner then synthesizes results from all invoked modules into a coherent, comprehensive answer. This multi-step approach enables the system to handle diverse question types—from factual queries requiring direct database lookups to complex analytical questions requiring statistical analysis and contextual explanation.

### 7. Analytics and Reporting

The analytics service provides comprehensive insights through multiple visualization and aggregation endpoints. Key Performance Indicators (KPIs) include total feedback volume, sentiment distribution percentages, top categories, and top aspects. All KPIs support flexible filtering by date range, product, locale, and version, enabling drill-down analysis.

Trend analysis tracks sentiment and category distribution over time, with configurable intervals (daily, weekly, monthly). The service aggregates data efficiently using SQL window functions and date truncation, enabling visualization of long-term patterns and seasonal variations.

The drilldown functionality allows users to explore individual feedback items matching specific criteria, with pagination support for large result sets. The export feature generates CSV files containing filtered feedback data, enabling further analysis in external tools like Excel or Python notebooks.

### 8. Frontend Dashboard Features

The Streamlit dashboard provides intuitive access to all system capabilities through organized pages. The Home page displays system health and provides navigation guidance. The Ingestion pages support file uploads with progress indicators and success/failure feedback. The combined Ingest & Label page streamlines the workflow by enabling ingestion and labeling in a single operation.

The Analytics Dashboard presents KPIs as metric cards, trends as interactive charts, and detailed feedback listings in sortable, filterable tables. The Ask AI page provides a conversational interface for RAG-based question answering, displaying answers with source citations. The Ask Agent page showcases the planner's capabilities, showing which modules were invoked and how results were synthesized.

The Search Demo page enables interactive exploration of the semantic search index, allowing users to experiment with queries and observe similarity scores and retrieved content.

## Data Flow and Workflows

The system supports two primary workflows: feedback analysis and knowledge base querying. In the feedback workflow, users upload CSV or JSON files containing customer feedback. The ingestion service parses files, validates data, creates ingestion run records, and inserts feedback items into the database. Users then trigger labeling, which processes unlabeled items in batches, calling the Groq API for each item and updating database records with sentiment, category, and aspects.

Embedding generation transforms labeled feedback into vectors, and indexing populates the unified search index. Once indexed, feedback becomes searchable and queryable through the RAG and agent services.

The knowledge base workflow begins with document upload. Documents are chunked using configurable strategies (by paragraph, sentence, or fixed token counts), and each chunk is embedded and stored. Chunks are automatically indexed, making knowledge base content immediately available for semantic search and RAG queries.

## Database Schema and Data Models

The database schema follows a normalized design with clear relationships and comprehensive indexing. The `ingestion_runs` table tracks batch processing operations, maintaining audit trails and error logs. The `feedback` table stores individual feedback items with rich metadata and optional embeddings. JSONB columns enable flexible storage of aspects, raw payloads, and corrected labels while maintaining queryability.

The `kb_docs` and `kb_chunks` tables implement a parent-child relationship, allowing documents to be stored intact while enabling granular chunk-level retrieval. The `search_index` table serves as a denormalized view optimized for retrieval, containing pre-computed embeddings and metadata for fast similarity searches.

All tables include appropriate indexes for common query patterns: date ranges, product filters, sentiment and category lookups, and vector similarity searches. The pgvector extension enables efficient approximate nearest neighbor searches using HNSW or IVFFlat indexes.

## Security and Operational Considerations

Security is addressed through multiple layers. Environment variables store sensitive credentials (database URLs, API keys), preventing accidental exposure in version control. The agent service uses whitelisted SQL operations and parameterized queries to prevent injection attacks. All user inputs are validated through Pydantic schemas before processing.

Operational reliability is ensured through comprehensive error handling, transaction management, and logging. Failed ingestion operations are recorded with detailed error messages, enabling troubleshooting without data loss. Database transactions ensure atomicity of multi-step operations like labeling and embedding generation.

The system supports incremental processing, allowing teams to process new data without reprocessing entire datasets. This capability reduces computational costs and enables near-real-time updates as new feedback arrives.

## Use Cases and Applications

The Feedback Intelligence System addresses diverse use cases across product development, customer success, and business intelligence domains. Product managers can identify trending feature requests, track sentiment changes after releases, and discover emerging issues before they become widespread. Customer success teams can prioritize support efforts based on complaint volume and severity, identify common pain points, and reference knowledge base content when responding to inquiries.

Data analysts can generate custom reports, export filtered datasets for advanced analysis, and track key metrics over time. Executives can monitor high-level sentiment trends, assess product health, and make data-driven decisions about resource allocation and strategic priorities.

The system's RAG and agent capabilities enable natural language querying, allowing non-technical users to ask complex questions and receive comprehensive, cited answers without requiring SQL knowledge or data engineering expertise.

## Future Enhancement Opportunities

Several enhancement opportunities could further expand the system's capabilities. Multi-language support would require language detection, multilingual embedding models, and locale-aware processing. Reranking models could improve retrieval precision by rescoring initial search results using cross-encoder architectures.

Fine-tuning the labeling models on domain-specific feedback could improve categorization accuracy for specialized industries or products. Role-based access control would enable multi-tenant deployments with data isolation and permission management. Real-time streaming ingestion would support event-driven architectures with near-instantaneous feedback processing.

Docker containerization and Docker Compose configurations would simplify deployment and enable consistent environments across development, staging, and production. Integration with external systems (Jira, Slack, customer support platforms) would enable automated ticket creation, alerting, and workflow automation.

## Conclusion

The Feedback Intelligence System represents a complete, production-ready solution for customer feedback analysis. By combining modern web frameworks, state-of-the-art machine learning models, vector search capabilities, and intelligent query planning, the system transforms unstructured textual data into actionable business intelligence. The modular architecture, comprehensive API, and intuitive dashboard enable diverse stakeholders to extract value from customer feedback, ultimately improving product quality, customer satisfaction, and business outcomes.

The system's design prioritizes maintainability, scalability, and security while remaining flexible enough to adapt to evolving requirements. Whether processing hundreds or millions of feedback items, the platform provides consistent performance and reliable insights, making it an invaluable tool for any organization committed to data-driven customer understanding.

