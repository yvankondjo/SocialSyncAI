# Architecture Diagrams & Visual Guides

This file contains ASCII diagrams and visual representations of the SocialSync AI architecture.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SocialSync AI Platform                        │
│                    =======================                       │
└─────────────────┬───────────────────────────────────────────────┘
                  │
    ┌─────────────▼─────────────────────────────────────┐
    │                User Interface                      │
    │                ===============                     │
    │  ┌─────────────────────────────────────────────┐  │
    │  │           Next.js Frontend                   │  │
    │  │           localhost:3000                     │  │
    │  │                                             │  │
    │  │  • Dashboard & Analytics                    │  │
    │  │  • Unified Inbox (DMs + Comments)           │  │
    │  │  • Knowledge Base Management                │  │
    │  │  • AI Studio (Content Generation)           │  │
    │  │  • Post Scheduling Calendar                 │  │
    │  │  • Settings & Configuration                 │  │
    │  └─────────────────────────────────────────────┘  │
    └─────────────┬─────────────────────────────────────┘
                  │
    ┌─────────────▼─────────────────────────────────────┐
    │               API Gateway Layer                    │
    │               ==================                   │
    │  ┌─────────────────────────────────────────────┐  │
    │  │           FastAPI Backend                    │  │
    │  │           localhost:8000                     │  │
    │  │                                             │  │
    │  │  • REST API Endpoints                       │  │
    │  │  • Authentication & Authorization           │  │
    │  │  • Request Validation                       │  │
    │  │  • Response Formatting                      │  │
    │  └─────────────────────────────────────────────┘  │
    └─────────────┬─────────────────────────────────────┘
                  │
    ┌─────────────▼─────────────────────────────────────┐
    │             Background Services                    │
    │             ====================                   │
    │  ┌─────────────────────────────────────────────┐  │
    │  │        Celery Workers & Tasks               │  │
    │  │                                             │  │
    │  │  • Message Processing                       │  │
    │  │  • Comment Monitoring                       │  │
    │  │  • AI Response Generation                   │  │
    │  │  • Scheduled Post Publishing                │  │
    │  │  • Analytics Processing                     │  │
    │  └─────────────────────────────────────────────┘  │
    └─────────────┬─────────────────────────────────────┘
                  │
    ┌─────────────▼─────────────────────────────────────┐
    │               Data Layer                           │
    │               ===========                          │
    │  ┌─────────────────────────────────────────────┐  │
    │  │         Supabase PostgreSQL                 │  │
    │  │                                             │  │
    │  │  • User Authentication                      │  │
    │  │  • Application Data                         │  │
    │  │  • Vector Embeddings (pg_vector)            │  │
    │  │  • Row Level Security (RLS)                 │  │
    │  │                                             │  │
    │  │         Redis Cache & Queue                 │  │
    │  │  • Session Storage                          │  │
    │  │  • Task Queues                              │  │
    │  │  • Rate Limiting                            │  │
    │  └─────────────────────────────────────────────┘  │
    └─────────────┬─────────────────────────────────────┘
                  │
    ┌─────────────▼─────────────────────────────────────┐
    │             External Integrations                  │
    │             ======================                 │
    │  ┌─────────────────────────────────────────────┐  │
    │  │      Social Media Platforms                 │  │
    │  │                                             │  │
    │  │  • Instagram Graph API                      │  │
    │  │  • WhatsApp Business API                    │  │
    │  │  • Webhook Event Processing                 │  │
    │  │                                             │  │
    │  │      AI & ML Services                       │  │
    │  │                                             │  │
    │  │  • OpenRouter (Multi-LLM)                  │  │
    │  │  • Google Gemini (Embeddings)               │  │
    │  │  • LangChain Orchestration                  │  │
    │  └─────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────┘
```

## Data Flow Architecture

```
User Interaction Flow:
┌─────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  User   │───▶│  Frontend   │───▶│   Backend   │───▶│  Database   │
│ Action  │    │   (React)   │    │   (API)     │    │  (Supabase) │
└─────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                        │
                                        ▼
Real-time Processing Flow:              ┌─────────────┐    ┌─────────────┐
                                        │   Celery    │───▶│   Social    │
                                        │   Worker    │    │   APIs      │
                                        └─────────────┘    └─────────────┘
                                               │
                                               ▼
                                        ┌─────────────┐    ┌─────────────┐
                                        │   AI/ML     │───▶│  Response   │
                                        │ Processing  │    │ Generation  │
                                        └─────────────┘    └─────────────┘
```

## AI Pipeline Architecture

```
Knowledge Base Processing:
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Documents     │───▶│   Chunking &    │───▶│   Embedding     │
│   (PDF, TXT)    │    │   Preprocessing │    │   Generation    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Vector Store   │◀───│   Similarity    │───▶│   Context       │
│  (pg_vector)    │    │   Search        │    │   Retrieval     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LangGraph     │───▶│   RAG Agent     │───▶│   LLM Response  │
│   Orchestration │    │   Processing    │    │   Generation    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Component Interaction Diagram

```
Component Interaction Matrix:

Frontend Components:
├── Dashboard (Analytics & Metrics)
├── Inbox (DMs & Comments)
├── Knowledge Base (Document Management)
├── AI Studio (Content Generation)
├── Calendar (Post Scheduling)
└── Settings (Configuration)

Backend Services:
├── Authentication Service
├── Social Media Integration
├── AI Processing Service
├── Analytics Service
├── Scheduling Service
└── Webhook Handler

Database Tables:
├── auth.users (User accounts)
├── social_accounts (Platform connections)
├── conversations (Messages & threads)
├── comments (Instagram comments)
├── knowledge_base (Documents & embeddings)
├── scheduled_posts (Content calendar)
├── analytics (Metrics & reports)
└── ai_settings (Model configurations)
```

## Deployment Architecture

```
Production Deployment:
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose Stack                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────┐ │
│  │  Frontend   │ │   Backend   │ │   Celery    │ │  Redis  │ │
│  │  (Next.js)  │ │  (FastAPI)  │ │   Workers   │ │         │ │
│  │             │ │             │ │             │ │         │ │
│  │  Port 3000  │ │  Port 8000  │ │             │ │ Port    │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────┘ │
└─────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────┐
│                   External Services                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────┐ │
│  │  Supabase   │ │   OpenRouter│ │  Instagram │ │ WhatsApp │ │
│  │ PostgreSQL  │ │     API     │ │ Graph API  │ │Business │ │
│  │   + Auth    │ │             │ │            │ │   API    │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Security Architecture

```
Security Layers:
┌─────────────────────────────────────────────────────────────┐
│                 Authentication & Authorization              │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐    │
│  │              JWT Token Validation                   │    │
│  │  • Supabase Auth Integration                       │    │
│  │  • Automatic Token Refresh                        │    │
│  │  • Role-based Access Control                      │    │
│  └─────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐    │
│  │              API Security                           │    │
│  │  • Request Validation (Pydantic)                   │    │
│  │  • Rate Limiting (Redis)                          │    │
│  │  • CORS Configuration                             │    │
│  │  • Input Sanitization                             │    │
│  └─────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Data Security                          │    │
│  │  • Row Level Security (RLS)                       │    │
│  │  • Encrypted API Keys                             │    │
│  │  • Secure Environment Variables                   │    │
│  │  • Audit Logging                                  │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```
