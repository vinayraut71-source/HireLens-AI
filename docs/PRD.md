# HireLens AI — Product Requirements Document

**Version:** 2.0  
**Status:** Draft — Startup-Grade  
**Last Updated:** June 13, 2026  
**Owner:** Product & Engineering  
**Classification:** Internal

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [User Personas](#2-user-personas)
3. [User Stories](#3-user-stories)
4. [MVP Scope](#4-mvp-scope)
5. [Future Roadmap](#5-future-roadmap)
6. [System Architecture](#6-system-architecture)
7. [Database Schema](#7-database-schema)
8. [API Design](#8-api-design)
9. [AI Agent Architecture](#9-ai-agent-architecture)
10. [Security Requirements](#10-security-requirements)
11. [Folder Structure](#11-folder-structure)
12. [Development Sprints](#12-development-sprints)
13. [Resume Versioning System](#13-resume-versioning-system)
14. [Job Application Analytics](#14-job-application-analytics)
15. [Feedback Learning Loop](#15-feedback-learning-loop)
16. [Recruiter & Company Portal (Future B2B)](#16-recruiter--company-portal-future-b2b)
17. [Agent Audit & Activity Log](#17-agent-audit--activity-log)
18. [Human-in-the-Loop Application System](#18-human-in-the-loop-application-system)
19. [Success Metrics & KPIs](#19-success-metrics--kpis)
20. [Competitive Analysis](#20-competitive-analysis)
21. [Monetization Strategy](#21-monetization-strategy)
22. [Technical Scalability Roadmap](#22-technical-scalability-roadmap)

---

## 1. Executive Summary

### 1.1 Product Vision

**HireLens AI** is an AI-powered Career Copilot that guides job seekers from resume optimization through interview preparation and application tracking. Unlike static resume builders or generic job boards, HireLens combines semantic resume analysis, ATS scoring, job matching, skill-gap detection, and personalized learning roadmaps into a single intelligent workflow.

### 1.2 Problem Statement

Job seekers face fragmented tools and opaque hiring processes:

| Pain Point | Current Reality | HireLens Solution |
|---|---|---|
| Resume optimization | Manual guesswork; no ATS feedback | AI-driven parsing, scoring, and rewrite suggestions |
| Job discovery | Hours spent on multiple platforms | Semantic matching against user profile and preferences |
| Skill gaps | Unclear what to learn next | Gap analysis mapped to curated learning roadmaps |
| Application chaos | Spreadsheets and memory | Centralized tracker with status, notes, and reminders |
| Interview prep | Generic advice | Role-specific Q&A, behavioral coaching, mock sessions |

### 1.3 Target Market

- **Primary:** Early-to-mid career professionals (0–10 years experience) actively job searching
- **Secondary:** Career switchers, new graduates, and professionals upskilling for promotion
- **Geography (MVP):** English-speaking markets (US, UK, Canada, India)
- **Business model (future):** Freemium with premium tiers for advanced AI features, unlimited job matching, and interview coaching

### 1.4 Success Metrics (Summary)

Full KPI framework with 3/6/12-month targets is defined in [Section 19](#19-success-metrics--kpis). Headline 12-month targets:

| Metric | Target |
|---|---|
| Monthly Active Users (MAU) | 10,000 |
| Paid conversion rate | ≥ 8% |
| Avg. ATS score improvement (30 days) | +15 points |
| Interview conversion rate (applied → interview) | ≥ 12% |
| Application tracker adoption | ≥ 60% of active users |
| User retention (D30) | ≥ 35% |
| NPS | ≥ 40 |

### 1.5 Key Differentiators

1. **End-to-end copilot** — One product spans resume → match → learn → apply → interview
2. **Version-aware intelligence** — Immutable resume versions with ATS and match score trajectories
3. **Outcome-driven learning** — Feedback loop from application results improves recommendations over time
4. **Semantic intelligence** — Sentence Transformers + FAISS for meaning-based matching, not keyword stuffing
5. **Human-in-the-loop by design** — AI prepares applications; users always approve before submission
6. **Full agent auditability** — Every AI action logged with inputs, outputs, and approval status
7. **Transparent ATS scoring** — Explainable scores with section-level feedback and version comparison

---

## 2. User Personas

### 2.1 Priya — The Career Switcher

| Attribute | Detail |
|---|---|
| Age | 32 |
| Background | 6 years in marketing, transitioning to product management |
| Goals | Reframe resume, identify transferable skills, close PM skill gaps |
| Frustrations | ATS rejects her resume; doesn't know which courses matter |
| HireLens usage | Upload resume → gap analysis → learning roadmap → targeted job matches |
| Success criteria | Lands 3 PM interviews within 90 days |

### 2.2 Marcus — The Active Job Seeker

| Attribute | Detail |
|---|---|
| Age | 27 |
| Background | Software engineer, 4 YOE, laid off and searching aggressively |
| Goals | Maximize application volume with quality; track every application |
| Frustrations | Juggling 40+ applications across platforms; no interview prep time |
| HireLens usage | ATS optimization → auto job discovery → application tracker → interview prep |
| Success criteria | Tracks all applications in one place; improves ATS score to 85+ |

### 2.3 Elena — The New Graduate

| Attribute | Detail |
|---|---|
| Age | 22 |
| Background | CS graduate, first professional role |
| Goals | Build a strong resume from internship experience; understand what employers want |
| Frustrations | Thin resume; overwhelmed by job descriptions; no mentorship |
| HireLens usage | Resume builder guidance → skill gap detection → entry-level job matching |
| Success criteria | Gets first offer within 6 months of graduation |

### 2.4 David — The Upskiller

| Attribute | Detail |
|---|---|
| Age | 38 |
| Background | Senior analyst, wants promotion to data science lead |
| Goals | Identify skills needed for next level; stay competitive |
| Frustrations | Doesn't know if current skills align with market demand |
| HireLens usage | Periodic resume refresh → market-aligned skill analysis → learning roadmap |
| Success criteria | Closes 3 critical skill gaps within 6 months |

### 2.5 Recruiter / Hiring Manager (Future B2B Persona)

| Attribute | Detail |
|---|---|
| Role | Technical recruiter at mid-size company |
| Goals | Source better-matched candidates faster |
| HireLens usage (future) | Candidate matching portal, structured skill profiles |
| Note | Out of MVP scope; informs long-term platform strategy |

---

## 3. User Stories

Stories are grouped by epic. Priority: **P0** (MVP), **P1** (MVP stretch), **P2** (post-MVP).

### Epic 1: Authentication & Onboarding

| ID | Story | Priority | Acceptance Criteria |
|---|---|---|---|
| US-001 | As a new user, I want to sign up with email/password so I can access my career data securely. | P0 | Email verification; password strength rules; JWT session issued |
| US-002 | As a user, I want to sign in with Google OAuth so I can onboard quickly. | P1 | OAuth 2.0 flow; account linking; profile pre-fill |
| US-003 | As a new user, I want a guided onboarding wizard so I understand HireLens capabilities. | P1 | 4-step wizard; skip option; progress saved |
| US-004 | As a user, I want to set job preferences (role, location, remote, salary) so matching is personalized. | P0 | Preferences stored; editable anytime; used in job matching |

### Epic 2: Resume Management

| ID | Story | Priority | Acceptance Criteria |
|---|---|---|---|
| US-010 | As a user, I want to upload a resume (PDF/DOCX) so HireLens can analyze it. | P0 | Supports PDF & DOCX up to 5 MB; parsing completes in < 30s |
| US-011 | As a user, I want to see my parsed resume in a structured view so I can verify accuracy. | P0 | Sections: contact, summary, experience, education, skills, projects |
| US-012 | As a user, I want to edit parsed resume fields so I can correct extraction errors. | P0 | Inline editing; changes persisted; re-indexing triggered |
| US-013 | As a user, I want to maintain multiple resume versions so I can tailor per role. | P0 | Immutable version snapshots; compare v1 vs v2 vs v3; improvement timeline |
| US-014 | As a user, I want AI suggestions to improve resume bullet points so my impact is clearer. | P1 | Gemini-generated rewrites; accept/reject per suggestion |
| US-015 | As a user, I want to compare two resume versions side-by-side so I can see what changed. | P1 | Diff view: sections, ATS delta, match score delta |
| US-016 | As a user, I want an improvement history chart showing ATS progression so I stay motivated. | P1 | Line chart: v1 (62%) → v2 (78%) → v3 (91%) |

### Epic 3: ATS Scoring

| ID | Story | Priority | Acceptance Criteria |
|---|---|---|---|
| US-020 | As a user, I want an overall ATS compatibility score (0–100) so I know how machine-readable my resume is. | P0 | Score displayed with color-coded tier; updates on resume edit |
| US-021 | As a user, I want section-level ATS feedback so I know what to fix. | P0 | Feedback per section: formatting, keywords, length, structure |
| US-022 | As a user, I want to score my resume against a specific job description so I can tailor it. | P0 | Paste or select JD; keyword match %; missing keywords listed |
| US-023 | As a user, I want ATS score history so I can track improvement over time. | P0 | Per-version ATS history; delta from prior version |

### Epic 4: Job Matching

| ID | Story | Priority | Acceptance Criteria |
|---|---|---|---|
| US-030 | As a user, I want to paste a job description and see my match score so I can decide whether to apply. | P0 | Semantic similarity score; top matching skills; gaps highlighted |
| US-031 | As a user, I want recommended jobs based on my resume and preferences so I discover relevant openings. | P1 | Daily job feed; relevance score; filter by remote/location/salary |
| US-032 | As a user, I want to save interesting jobs so I can review them later. | P0 | Save/unsave; notes field; link to application tracker |
| US-033 | As a user, I want side-by-side resume vs. job comparison so I understand fit. | P0 | Matched skills, partial matches, missing skills visualized |

### Epic 5: Skill Gap Analysis & Learning Roadmaps

| ID | Story | Priority | Acceptance Criteria |
|---|---|---|---|
| US-040 | As a user, I want to see skill gaps between my resume and a target role so I know what to learn. | P0 | Gap list with priority (critical / nice-to-have); sourced from JD or role template |
| US-041 | As a user, I want a personalized learning roadmap so I have a structured plan to close gaps. | P0 | Ordered modules; estimated time per skill; resource links |
| US-042 | As a user, I want to mark skills as "in progress" or "completed" so I track learning progress. | P1 | Status per skill; progress bar on roadmap; completion timestamps |
| US-043 | As a user, I want roadmap resources (courses, articles, projects) so I know where to learn. | P1 | Curated links per skill; Gemini-generated project ideas |

### Epic 6: Application Tracking

| ID | Story | Priority | Acceptance Criteria |
|---|---|---|---|
| US-050 | As a user, I want to log job applications with status so I stay organized. | P0 | Statuses: Saved, Applied, Phone Screen, Interview, Offer, Rejected, Withdrawn |
| US-051 | As a user, I want to attach a resume version and notes to each application so I have context. | P0 | Resume version linked; free-text notes; applied date |
| US-052 | As a user, I want a kanban or list view of applications so I see my pipeline at a glance. | P0 | Filterable list; status counts; sort by date |
| US-053 | As a user, I want reminders for follow-ups so I don't miss opportunities. | P2 | Email/in-app reminder; configurable follow-up date |
| US-054 | As a user, I want an analytics dashboard showing my application funnel so I understand my job search performance. | P1 | Interview rate, rejection rate, offer rate, monthly trends |
| US-055 | As a user, I want to record application outcomes so HireLens learns what works for me. | P1 | Outcome events: viewed, rejected, interview, offer |

### Epic 7: Interview Preparation

| ID | Story | Priority | Acceptance Criteria |
|---|---|---|---|
| US-060 | As a user, I want role-specific interview questions generated from a job description so I can practice. | P1 | Technical + behavioral questions; categorized by topic |
| US-061 | As a user, I want AI feedback on my practice answers so I improve over time. | P2 | Text-based answer submission; Gemini critique with scoring |
| US-062 | As a user, I want a STAR-method coach for behavioral questions so my stories are structured. | P2 | Guided STAR template; AI refinement of each section |

### Epic 8: Job Discovery (Automated)

| ID | Story | Priority | Acceptance Criteria |
|---|---|---|---|
| US-070 | As a user, I want HireLens to automatically find jobs matching my profile so I save search time. | P2 | Background job ingestion; daily digest; relevance-ranked |
| US-071 | As a user, I want to configure discovery sources and filters so results match my criteria. | P2 | Source selection; keyword filters; frequency settings |

### Epic 9: Application Assistance (Human-in-the-Loop)

| ID | Story | Priority | Acceptance Criteria |
|---|---|---|---|
| US-080 | As a user, I want AI to draft cover letters tailored to a job so I apply faster. | P2 | Generated from resume + JD; editable; tone selection |
| US-081 | As a user, I want to review AI-prepared application packages before submission so I stay in control. | P2 | Review screen: tailored resume, cover letter, match score; explicit approve/reject |
| US-082 | As a user, I want AI to find and rank jobs for me but never apply without my approval. | P2 | Discovery agent proposes jobs; user approves each application |
| US-083 | As a user, I want a complete log of AI actions taken on my behalf so I can audit decisions. | P1 | Activity log: agent, action, timestamp, approval status |

### Epic 10: Analytics & Insights

| ID | Story | Priority | Acceptance Criteria |
|---|---|---|---|
| US-090 | As a user, I want to see resume improvement trends over time on my dashboard. | P1 | ATS score trend, version count, avg improvement per edit |
| US-091 | As a user, I want to see skill improvement trends as I complete roadmap modules. | P1 | Skills completed over time; gap closure rate |
| US-092 | As a user, I want to compare my match scores across applications so I apply strategically. | P1 | Avg match score by outcome (interview vs rejection) |

### Epic 11: Admin & Compliance (Internal)

| ID | Story | Priority | Acceptance Criteria |
|---|---|---|---|
| US-100 | As an admin, I want to view all AI agent actions across the platform for debugging and compliance. | P2 | Filterable audit log; export CSV |
| US-101 | As an admin, I want to see AI cost and usage metrics per user and per agent. | P2 | Token usage, cost attribution, anomaly alerts |

---

## 4. MVP Scope

### 4.1 MVP Definition

The MVP delivers the **core career intelligence loop**:

> **Upload resume → Get ATS score → Match to jobs → Detect skill gaps → Generate learning roadmap → Track applications**

### 4.2 In Scope (MVP — P0)

| Feature | Description |
|---|---|
| User authentication | Email/password signup, login, JWT sessions |
| User profile & preferences | Name, target role, location, remote preference |
| Resume upload & parsing | PDF/DOCX upload; structured extraction via Gemini |
| Resume versioning | Immutable version snapshots; ATS and match score history per version |
| Resume editor | View and edit parsed sections; edits create new versions |
| ATS scoring | Overall score + section feedback + JD-specific scoring |
| Job matching (manual) | Paste JD or select saved job; semantic match score |
| Skill gap analysis | Compare resume skills vs. job requirements |
| Learning roadmap | AI-generated ordered learning plan with resources |
| Application tracker | CRUD applications with status pipeline |
| Application analytics (basic) | Funnel stats: applied, interview, rejection, offer rates |
| Agent activity log (user-facing) | User-visible log of AI actions on their account |
| Dashboard | Summary cards: ATS score, applications, gaps, improvement trend |
| Responsive UI | Desktop-first; mobile-friendly layout |

### 4.3 Stretch Goals (MVP — P1)

| Feature | Description |
|---|---|
| Google OAuth | Social sign-in |
| Version comparison UI | Side-by-side diff of two resume versions |
| AI bullet rewrites | Gemini-powered improvement suggestions |
| Saved jobs library | Bookmark and annotate jobs |
| Interview question generator | Role-specific questions from JD |
| Outcome feedback capture | Record interview/rejection/offer outcomes |
| Application analytics (full) | Monthly trends, match score by outcome |

### 4.4 Explicitly Out of Scope (MVP)

| Feature | Rationale | Target Phase |
|---|---|---|
| Automated job discovery / scraping | Legal complexity; infra cost | Phase 2 |
| Cover letter generation | Depends on stable resume + match pipeline | Phase 2 |
| Mock interview (voice/video) | Requires real-time infra | Phase 3 |
| Browser extension for auto-apply | High risk; requires human-in-the-loop workflow first | Phase 3 |
| Recruiter / B2B portal | Different user segment; schema reserved in Phase 1 | Phase 4 |
| Mobile native apps | Web-first strategy | Phase 4 |
| Payment / subscriptions | Validate product-market fit first | Phase 2 |
| Fully autonomous application submission | Prohibited — always requires user approval | Never |
| Feedback learning loop (ML re-ranking) | Requires outcome data volume | Phase 2 |
| Multi-language support | English-only for MVP | Phase 3 |

### 4.5 MVP Technical Constraints

- Single-region deployment (US-East)
- Gemini API as primary LLM (no multi-model routing in MVP)
- FAISS in-memory index (rebuild on deploy; persist embeddings in PostgreSQL)
- Max 5 MB resume upload
- Immutable resume versions (no in-place overwrite of scored snapshots)
- Agent audit log table created at Sprint 0 (populated from Sprint 2 onward)
- Rate limit: 50 AI requests per user per day (MVP)
- No real-time collaboration features

### 4.6 MVP Definition of Done

- [ ] User can sign up, upload resume, and see parsed data within 30 seconds
- [ ] ATS score generated with actionable section feedback
- [ ] User can paste a JD and receive match score + skill gaps
- [ ] Learning roadmap generated with ≥ 3 modules per critical gap
- [ ] User can create and track ≥ 1 application through full status lifecycle
- [ ] All P0 API endpoints documented in OpenAPI spec
- [ ] Core user flows covered by integration tests
- [ ] Deployed to staging environment with CI/CD pipeline

---

## 5. Future Roadmap

### Phase 2 — Growth (Months 4–6)

**Theme:** Discovery, monetization, and depth

| Feature | Description |
|---|---|
| Automated job discovery | Ingest jobs from public APIs (LinkedIn, Indeed, Adzuna); daily digest |
| Cover letter generator | Tailored drafts from resume + JD |
| Subscription tiers | Free / Pro / Premium / Recruiter (see Section 21) |
| Resume version analytics | A/B performance by version; callback correlation |
| Outcome feedback loop | Capture application outcomes; re-rank recommendations |
| Application analytics dashboard | Full funnel metrics and trend widgets |
| Resume templates | ATS-friendly templates with guided fill |
| Email notifications | Application reminders, new match alerts |
| Skill progress tracking | Mark skills in-progress/completed on roadmap |

### Phase 3 — Intelligence (Months 7–10)

**Theme:** Advanced AI coaching and automation

| Feature | Description |
|---|---|
| Mock interview coach | Text-based practice with AI scoring and STAR coaching |
| Voice interview mode | Speech-to-text practice sessions |
| Application agent (assist mode) | Human-in-the-loop workflow; user approves before submit |
| Agent audit dashboard (admin) | Full platform audit log and cost attribution |
| Multi-resume A/B testing | Track which version gets more callbacks |
| Market insights dashboard | Salary benchmarks, skill demand trends |
| Chrome extension | Quick-match any job page against profile |

### Phase 4 — Platform (Months 11–14)

**Theme:** Ecosystem and B2B

| Feature | Description |
|---|---|
| Recruiter portal | Candidate search, AI ranking, company dashboard (schema pre-built) |
| Team / coach accounts | Career coaches manage multiple clients |
| API for partners | Embeddable ATS scoring widget |
| Mobile apps | iOS and Android native apps |
| Internationalization | Multi-language resume parsing and UI |
| Full application agent | AI prepares package; user reviews and approves submission |

### Phase 5 — Vision (15+ Months)

| Feature | Description |
|---|---|
| Career trajectory modeling | AI predicts career paths based on skills and market data |
| Networking copilot | Suggest connections, draft outreach messages |
| Offer negotiation coach | Salary benchmarking and negotiation scripts |
| Employer brand insights | Company culture and interview process intelligence |
| Agentic career management | Proactive copilot that acts on user's behalf within guardrails |

---

## 6. System Architecture

### 6.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                               │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Next.js App (TypeScript + Tailwind CSS)                     │   │
│  │  - App Router  - Server Components  - Client Components      │   │
│  │  - Auth context  - API client (fetch/axios)  - State (Zustand)│  │
│  └──────────────────────────┬───────────────────────────────────┘   │
└─────────────────────────────┼───────────────────────────────────────┘
                              │ HTTPS (REST + JSON)
┌─────────────────────────────┼───────────────────────────────────────┐
│                          API LAYER                                  │
│  ┌──────────────────────────▼───────────────────────────────────┐   │
│  │  FastAPI Application                                         │   │
│  │  - Auth middleware (JWT)  - Rate limiter  - Request validation│  │
│  │  - Routers: auth, users, resumes, jobs, applications, analytics, ai, audit │
│  └──────┬──────────────┬──────────────┬─────────────────────────┘   │
│         │              │              │                             │
│  ┌──────▼──────┐ ┌─────▼─────┐ ┌─────▼─────────────────────────┐   │
│  │  PostgreSQL │ │  Redis    │ │  Background Workers (Celery/   │   │
│  │  (primary   │ │  (cache,  │ │  ARQ) — resume parsing,       │   │
│  │   datastore)│ │   sessions│ │  embedding generation,       │   │
│  │             │ │   queues) │ │  job ingestion                │   │
│  └─────────────┘ └───────────┘ └───────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────┼───────────────────────────────────────┐
│                          AI LAYER                                   │
│  ┌──────────────────────────▼───────────────────────────────────┐   │
│  │  AI Service Module                                           │   │
│  │  ┌─────────────┐  ┌──────────────────┐  ┌─────────────────┐  │   │
│  │  │ Gemini API  │  │ Sentence         │  │ FAISS Vector    │  │   │
│  │  │ - Parsing   │  │ Transformers     │  │ Index           │  │   │
│  │  │ - Scoring   │  │ (all-MiniLM-L6)  │  │ - Resume embeds │  │   │
│  │  │ - Roadmaps  │  │ - JD embeds      │  │ - Job embeds    │  │   │
│  │  │ - Interview │  │ - Skill embeds   │  │ - Skill embeds  │  │   │
│  │  └─────────────┘  └──────────────────┘  └─────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 Component Responsibilities

| Component | Responsibility |
|---|---|
| **Next.js Frontend** | UI rendering, client-side state, auth token management, file upload UX |
| **FastAPI Backend** | Business logic, auth, data validation, orchestration of AI services |
| **PostgreSQL** | Persistent storage for users, resumes, jobs, applications, embeddings metadata |
| **Redis** | Session cache, rate limiting counters, background job queue |
| **Background Workers** | Async resume parsing, embedding generation, batch job ingestion |
| **Gemini API** | LLM tasks: parsing, scoring rationale, roadmap generation, interview Q&A |
| **Sentence Transformers** | Local embedding model for semantic similarity (no API cost) |
| **FAISS** | In-memory vector index for fast similarity search |

### 6.3 Key Data Flows

#### Flow 1: Resume Upload & Analysis

```
User uploads PDF/DOCX
  → Frontend sends multipart POST to /api/v1/resumes
  → FastAPI stores file in object storage (local/S3)
  → Background worker:
      1. Extract text (PyMuPDF / python-docx)
      2. Send text to Gemini for structured parsing
      3. Generate embedding via Sentence Transformers
      4. Store parsed JSON + embedding in PostgreSQL
      5. Add embedding to FAISS index
  → Return parsed resume + ATS score to user
```

#### Flow 2: Job Matching

```
User provides job description (paste or saved job)
  → Generate JD embedding (Sentence Transformers)
  → FAISS similarity search against user's resume embedding
  → Gemini generates detailed match analysis (skills, gaps, suggestions)
  → Return match score + gap analysis + recommendations
```

#### Flow 3: Learning Roadmap Generation

```
Skill gaps identified from match analysis
  → Gemini generates ordered learning modules per gap
  → Each module: skill, priority, estimated hours, resources, project idea
  → Store roadmap in PostgreSQL linked to user + target job
  → Return interactive roadmap to frontend
```

#### Flow 4: Human-in-the-Loop Application (Phase 2+)

```
Discovery Agent finds job → logs agent_audit_log (job_discovered)
  → Matching Agent calculates score → logs (job_matched)
  → Resume Agent tailors resume version → logs (resume_tailored)
  → Coaching Agent generates cover letter → logs (cover_letter_generated)
  → Application package status = pending_review
  → User reviews package in UI
  → User approves → logs (user_approved) → status = approved
  → User submits externally OR via integration → logs (application_submitted)
  → User records outcome → outcome_events → Feedback Learning Loop
```

### 6.4 Deployment Architecture (MVP)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Vercel     │     │   Railway /  │     │   Supabase / │
│   (Next.js)  │────▶│   Render     │────▶│   Railway    │
│              │     │   (FastAPI)  │     │   (PostgreSQL)│
└──────────────┘     └──────┬───────┘     └──────────────┘
                            │
                     ┌──────▼───────┐
                     │   Redis      │
                     │   (Upstash)  │
                     └──────────────┘
```

### 6.5 Technology Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Frontend framework | Next.js 14+ (App Router) | SSR, API routes for BFF pattern, Vercel deploy |
| Backend framework | FastAPI | Async, auto OpenAPI docs, Python AI ecosystem |
| Database | PostgreSQL 16 | JSONB for parsed resumes, pgvector future option |
| ORM | SQLAlchemy 2.0 + Alembic | Mature, async support, migration management |
| Auth | JWT (access + refresh tokens) | Stateless, works with SPA and mobile future |
| File storage | S3-compatible (or local for dev) | Scalable resume file storage |
| Embedding model | `all-MiniLM-L6-v2` | Fast, 384-dim, good quality for short text |
| Vector index | FAISS (IndexFlatIP) | Simple, fast for < 1M vectors; swap to pgvector later |
| LLM | Gemini 1.5 Pro / Flash | Cost-effective, strong structured output |
| Background jobs | ARQ (async Redis queue) | Lightweight, native async Python |
| CI/CD | GitHub Actions | Lint, test, deploy on merge to main |

---

## 7. Database Schema

### 7.1 Entity-Relationship Overview

```
users ─────────┬────── resume_profiles ────── resume_versions ────── resume_version_embeddings
               │                                    │
               │                                    ├── ats_score_history
               │                                    └── match_score_history
               │
               ├────── user_preferences
               │
               ├────── jobs (saved/matched)
               │           │
               │           └── job_embeddings
               │
               ├────── match_results
               │
               ├────── skill_gaps
               │
               ├────── learning_roadmaps ──── roadmap_modules
               │
               ├────── applications ────── application_outcome_events
               │           │
               │           └── application_packages (human-in-the-loop)
               │
               ├────── outcome_events (feedback learning)
               │
               ├────── recommendation_signals
               │
               ├────── agent_audit_log
               │
               └────── user_analytics_snapshots (materialized daily)

─── FUTURE B2B (schema reserved, empty until Phase 4) ───

companies ────── recruiters ────── company_users
    │                                  │
    └────── job_postings ──────────────┴────── candidate_matches
```

### 7.2 Core Table Definitions

#### `users`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK, DEFAULT gen_random_uuid() | User identifier |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | Login email |
| `password_hash` | VARCHAR(255) | NOT NULL | bcrypt hash |
| `full_name` | VARCHAR(255) | NOT NULL | Display name |
| `avatar_url` | TEXT | NULLABLE | Profile image URL |
| `plan_tier` | VARCHAR(20) | DEFAULT 'free' | free / pro / premium |
| `is_active` | BOOLEAN | DEFAULT true | Account status |
| `is_verified` | BOOLEAN | DEFAULT false | Email verified |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Registration time |
| `updated_at` | TIMESTAMPTZ | DEFAULT now() | Last update |

#### `user_preferences`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | Preference record ID |
| `user_id` | UUID | FK → users.id, UNIQUE | One per user |
| `target_role` | VARCHAR(255) | NULLABLE | Desired job title |
| `target_industry` | VARCHAR(255) | NULLABLE | Industry focus |
| `preferred_locations` | JSONB | DEFAULT '[]' | Array of location strings |
| `remote_preference` | VARCHAR(20) | DEFAULT 'any' | remote / hybrid / onsite / any |
| `min_salary` | INTEGER | NULLABLE | Minimum salary expectation |
| `max_salary` | INTEGER | NULLABLE | Maximum salary expectation |
| `experience_years` | INTEGER | NULLABLE | Years of experience |
| `updated_at` | TIMESTAMPTZ | DEFAULT now() | Last update |

#### `resume_profiles`

Parent entity representing a logical resume document. Versions hang off this.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | Profile identifier |
| `user_id` | UUID | FK → users.id, NOT NULL | Owner |
| `title` | VARCHAR(255) | NOT NULL | User-given name (e.g., "SWE Resume") |
| `is_default` | BOOLEAN | DEFAULT false | Default profile for matching |
| `current_version_id` | UUID | FK → resume_versions.id, NULLABLE | Pointer to latest version |
| `version_count` | INTEGER | DEFAULT 0 | Denormalized count for UI |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Created time |
| `updated_at` | TIMESTAMPTZ | DEFAULT now() | Last update |

#### `resume_versions`

Immutable snapshot created on every upload or material edit. Never updated in place.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | Version identifier |
| `profile_id` | UUID | FK → resume_profiles.id, NOT NULL | Parent profile |
| `user_id` | UUID | FK → users.id, NOT NULL | Owner (denormalized for queries) |
| `version_number` | INTEGER | NOT NULL | Sequential: 1, 2, 3… |
| `version_label` | VARCHAR(50) | NOT NULL | Display label: "v1", "v2", "v3" |
| `source` | VARCHAR(20) | NOT NULL | upload / edit / ai_tailor / duplicate |
| `parent_version_id` | UUID | FK → resume_versions.id, NULLABLE | Version this was derived from |
| `change_summary` | TEXT | NULLABLE | Auto-generated diff summary |
| `file_url` | TEXT | NULLABLE | Original file storage path |
| `file_type` | VARCHAR(10) | NULLABLE | pdf / docx |
| `raw_text` | TEXT | NULLABLE | Extracted plain text |
| `parsed_data` | JSONB | NULLABLE | Structured parsed content (snapshot) |
| `ats_score` | INTEGER | NULLABLE | ATS score at creation (0–100) |
| `ats_feedback` | JSONB | NULLABLE | Section-level feedback snapshot |
| `ats_score_delta` | INTEGER | NULLABLE | Change from parent version |
| `status` | VARCHAR(20) | DEFAULT 'processing' | processing / ready / error |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Version creation time |

**Unique constraint:** `(profile_id, version_number)`

**`parsed_data` JSONB structure:**

```json
{
  "contact": { "name": "", "email": "", "phone": "", "linkedin": "", "location": "" },
  "summary": "",
  "experience": [
    { "company": "", "title": "", "start_date": "", "end_date": "", "bullets": [""] }
  ],
  "education": [
    { "institution": "", "degree": "", "field": "", "graduation_date": "" }
  ],
  "skills": { "technical": [], "soft": [], "tools": [] },
  "projects": [
    { "name": "", "description": "", "technologies": [] }
  ],
  "certifications": []
}
```

#### `resume_version_embeddings`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | Embedding record ID |
| `version_id` | UUID | FK → resume_versions.id, UNIQUE | One embedding per version |
| `embedding` | BYTEA | NOT NULL | Serialized numpy array (384-dim) |
| `model_version` | VARCHAR(50) | NOT NULL | Embedding model identifier |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Generation time |

#### `ats_score_history`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | History record ID |
| `version_id` | UUID | FK → resume_versions.id, NOT NULL | Version scored |
| `profile_id` | UUID | FK → resume_profiles.id, NOT NULL | Parent profile |
| `user_id` | UUID | FK → users.id, NOT NULL | Owner |
| `job_id` | UUID | FK → jobs.id, NULLABLE | JD-specific (null = general) |
| `score` | INTEGER | NOT NULL | ATS score (0–100) |
| `score_delta` | INTEGER | NULLABLE | Delta from previous version |
| `feedback` | JSONB | NULLABLE | Section feedback snapshot |
| `scored_by` | VARCHAR(20) | DEFAULT 'system' | system / user_request / auto_on_edit |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Scored time |

#### `match_score_history`

Tracks match score changes per resume version per job over time.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | History record ID |
| `user_id` | UUID | FK → users.id, NOT NULL | Owner |
| `version_id` | UUID | FK → resume_versions.id, NOT NULL | Resume version used |
| `profile_id` | UUID | FK → resume_profiles.id, NOT NULL | Parent profile |
| `job_id` | UUID | FK → jobs.id, NOT NULL | Job matched against |
| `overall_score` | FLOAT | NOT NULL | Semantic similarity (0.0–1.0) |
| `ats_score` | INTEGER | NULLABLE | JD-specific ATS score |
| `score_delta` | FLOAT | NULLABLE | Delta from prior version on same job |
| `matched_skills` | JSONB | DEFAULT '[]' | Skills present in both |
| `missing_skills` | JSONB | DEFAULT '[]' | Required but absent |
| `match_result_id` | UUID | FK → match_results.id, NULLABLE | Full match result link |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Match time |

#### `jobs`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | Job identifier |
| `user_id` | UUID | FK → users.id, NOT NULL | User who saved/matched |
| `title` | VARCHAR(255) | NOT NULL | Job title |
| `company` | VARCHAR(255) | NULLABLE | Company name |
| `description` | TEXT | NOT NULL | Full job description text |
| `source_url` | TEXT | NULLABLE | Original posting URL |
| `location` | VARCHAR(255) | NULLABLE | Job location |
| `remote_type` | VARCHAR(20) | NULLABLE | remote / hybrid / onsite |
| `salary_min` | INTEGER | NULLABLE | Min salary if known |
| `salary_max` | INTEGER | NULLABLE | Max salary if known |
| `required_skills` | JSONB | DEFAULT '[]' | Extracted skill requirements |
| `is_saved` | BOOLEAN | DEFAULT false | Bookmarked by user |
| `discovered_by_agent` | BOOLEAN | DEFAULT false | Found by discovery agent |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Created time |

#### `job_embeddings`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | Embedding record ID |
| `job_id` | UUID | FK → jobs.id, UNIQUE | One embedding per job |
| `embedding` | BYTEA | NOT NULL | Serialized numpy array |
| `model_version` | VARCHAR(50) | NOT NULL | Model identifier |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Generation time |

#### `match_results`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | Match result ID |
| `user_id` | UUID | FK → users.id | User |
| `version_id` | UUID | FK → resume_versions.id | Resume version used |
| `job_id` | UUID | FK → jobs.id | Job matched against |
| `overall_score` | FLOAT | NOT NULL | Semantic similarity (0.0–1.0) |
| `ats_score` | INTEGER | NULLABLE | ATS-specific score for this JD |
| `matched_skills` | JSONB | DEFAULT '[]' | Skills present in both |
| `partial_skills` | JSONB | DEFAULT '[]' | Related but not exact matches |
| `missing_skills` | JSONB | DEFAULT '[]' | Required but absent |
| `ai_analysis` | TEXT | NULLABLE | Gemini narrative analysis |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Match time |

#### `skill_gaps`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | Gap ID |
| `user_id` | UUID | FK → users.id | User |
| `match_result_id` | UUID | FK → match_results.id | Source match |
| `skill_name` | VARCHAR(255) | NOT NULL | Missing skill |
| `priority` | VARCHAR(20) | NOT NULL | critical / important / nice_to_have |
| `category` | VARCHAR(50) | NULLABLE | technical / soft / domain |
| `description` | TEXT | NULLABLE | Why this skill matters |
| `status` | VARCHAR(20) | DEFAULT 'identified' | identified / in_progress / completed |
| `completed_at` | TIMESTAMPTZ | NULLABLE | When marked completed |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Identified time |

#### `learning_roadmaps`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | Roadmap ID |
| `user_id` | UUID | FK → users.id | User |
| `title` | VARCHAR(255) | NOT NULL | Roadmap title |
| `target_role` | VARCHAR(255) | NULLABLE | Target role |
| `match_result_id` | UUID | FK → match_results.id, NULLABLE | Source match |
| `status` | VARCHAR(20) | DEFAULT 'active' | active / completed / archived |
| `estimated_hours` | INTEGER | NULLABLE | Total estimated learning time |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Created time |
| `updated_at` | TIMESTAMPTZ | DEFAULT now() | Last update |

#### `roadmap_modules`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | Module ID |
| `roadmap_id` | UUID | FK → learning_roadmaps.id | Parent roadmap |
| `skill_gap_id` | UUID | FK → skill_gaps.id, NULLABLE | Linked gap |
| `order_index` | INTEGER | NOT NULL | Display order |
| `title` | VARCHAR(255) | NOT NULL | Module title |
| `description` | TEXT | NULLABLE | What to learn |
| `estimated_hours` | INTEGER | NULLABLE | Time estimate |
| `resources` | JSONB | DEFAULT '[]' | [{ "type": "course", "title": "", "url": "" }] |
| `project_idea` | TEXT | NULLABLE | Hands-on project suggestion |
| `status` | VARCHAR(20) | DEFAULT 'pending' | pending / in_progress / completed |
| `completed_at` | TIMESTAMPTZ | NULLABLE | Completion time |

#### `applications`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | Application ID |
| `user_id` | UUID | FK → users.id | Applicant |
| `job_id` | UUID | FK → jobs.id, NULLABLE | Linked job (if saved) |
| `version_id` | UUID | FK → resume_versions.id, NULLABLE | Resume version used |
| `company` | VARCHAR(255) | NOT NULL | Company name |
| `position` | VARCHAR(255) | NOT NULL | Role title |
| `status` | VARCHAR(30) | DEFAULT 'saved' | Pipeline status |
| `match_score` | FLOAT | NULLABLE | Match score at time of application |
| `applied_date` | DATE | NULLABLE | Date applied |
| `follow_up_date` | DATE | NULLABLE | Next follow-up |
| `job_url` | TEXT | NULLABLE | Application URL |
| `notes` | TEXT | NULLABLE | User notes |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Created time |
| `updated_at` | TIMESTAMPTZ | DEFAULT now() | Last update |

**Application status enum:** `saved`, `applied`, `viewed`, `rejected`, `phone_screen`, `interview_scheduled`, `interview_passed`, `offer_received`, `offer_accepted`, `withdrawn`

#### `application_packages` (Human-in-the-Loop)

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | Package ID |
| `user_id` | UUID | FK → users.id, NOT NULL | Applicant |
| `job_id` | UUID | FK → jobs.id, NOT NULL | Target job |
| `application_id` | UUID | FK → applications.id, NULLABLE | Linked after submission |
| `tailored_version_id` | UUID | FK → resume_versions.id, NOT NULL | AI-tailored resume |
| `cover_letter` | TEXT | NULLABLE | Generated cover letter |
| `match_score` | FLOAT | NOT NULL | Score at package creation |
| `approval_status` | VARCHAR(20) | DEFAULT 'pending_review' | See Section 18 |
| `approved_at` | TIMESTAMPTZ | NULLABLE | User approval timestamp |
| `submitted_at` | TIMESTAMPTZ | NULLABLE | Submission timestamp |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Package creation time |

#### `outcome_events` (Feedback Learning Loop)

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | Event ID |
| `user_id` | UUID | FK → users.id, NOT NULL | User |
| `application_id` | UUID | FK → applications.id, NOT NULL | Related application |
| `event_type` | VARCHAR(30) | NOT NULL | See outcome enum below |
| `version_id` | UUID | FK → resume_versions.id, NULLABLE | Resume version at outcome |
| `match_score` | FLOAT | NULLABLE | Match score at outcome |
| `metadata` | JSONB | DEFAULT '{}' | Extra context (rejection reason, offer amount) |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Event time |

**Outcome event enum:** `applied`, `viewed`, `rejected`, `interview_scheduled`, `interview_passed`, `offer_received`, `offer_accepted`

#### `recommendation_signals`

Stores learned weights from outcome data for personalization.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | Signal ID |
| `user_id` | UUID | FK → users.id, NOT NULL | User |
| `signal_type` | VARCHAR(30) | NOT NULL | job / skill / resume_suggestion |
| `signal_key` | VARCHAR(255) | NOT NULL | e.g., skill name, job category |
| `weight` | FLOAT | NOT NULL | Learned preference weight (-1.0 to 1.0) |
| `sample_count` | INTEGER | DEFAULT 1 | Number of outcomes contributing |
| `last_updated` | TIMESTAMPTZ | DEFAULT now() | Last recalculation |

#### `agent_audit_log`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | Log entry ID |
| `user_id` | UUID | FK → users.id, NOT NULL | Affected user |
| `agent_name` | VARCHAR(50) | NOT NULL | resume_agent / matching_agent / discovery_agent / etc. |
| `action_type` | VARCHAR(50) | NOT NULL | See action enum below |
| `input_ref_type` | VARCHAR(30) | NULLABLE | resume_version / job / application / etc. |
| `input_ref_id` | UUID | NULLABLE | ID of input entity |
| `output_ref_type` | VARCHAR(30) | NULLABLE | match_result / application_package / etc. |
| `output_ref_id` | UUID | NULLABLE | ID of output entity |
| `approval_status` | VARCHAR(20) | DEFAULT 'not_required' | not_required / pending / approved / rejected |
| `metadata` | JSONB | DEFAULT '{}' | Token count, model, duration_ms, error |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Action timestamp |

**Action type enum:** `resume_analyzed`, `ats_score_generated`, `job_matched`, `roadmap_generated`, `resume_tailored`, `cover_letter_generated`, `job_discovered`, `application_suggested`, `user_approved`, `user_rejected`, `application_submitted`

#### `user_analytics_snapshots`

Pre-computed daily aggregates for dashboard performance.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | Snapshot ID |
| `user_id` | UUID | FK → users.id, NOT NULL | User |
| `snapshot_date` | DATE | NOT NULL | Aggregation date |
| `total_applications` | INTEGER | DEFAULT 0 | Cumulative applications |
| `applications_this_month` | INTEGER | DEFAULT 0 | Applications in calendar month |
| `interview_rate` | FLOAT | NULLABLE | interviews / applied |
| `rejection_rate` | FLOAT | NULLABLE | rejections / applied |
| `offer_rate` | FLOAT | NULLABLE | offers / applied |
| `avg_match_score` | FLOAT | NULLABLE | Mean match score across applications |
| `avg_ats_score` | FLOAT | NULLABLE | Mean ATS score across versions |
| `ats_improvement` | INTEGER | NULLABLE | ATS delta (latest vs first version) |
| `skills_completed` | INTEGER | DEFAULT 0 | Roadmap modules completed |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Computed time |

**Unique constraint:** `(user_id, snapshot_date)`

### 7.3 Future B2B Tables (Schema Reserved)

#### `companies`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | Company identifier |
| `name` | VARCHAR(255) | NOT NULL | Company name |
| `domain` | VARCHAR(255) | UNIQUE, NULLABLE | Email domain for verification |
| `logo_url` | TEXT | NULLABLE | Company logo |
| `industry` | VARCHAR(100) | NULLABLE | Industry sector |
| `size` | VARCHAR(20) | NULLABLE | startup / smb / enterprise |
| `plan_tier` | VARCHAR(20) | DEFAULT 'recruiter_starter' | Recruiter plan tier |
| `is_active` | BOOLEAN | DEFAULT true | Account status |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Registration time |

#### `recruiters`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | Recruiter identifier |
| `company_id` | UUID | FK → companies.id, NOT NULL | Employer |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | Login email |
| `password_hash` | VARCHAR(255) | NOT NULL | bcrypt hash |
| `full_name` | VARCHAR(255) | NOT NULL | Display name |
| `role` | VARCHAR(30) | DEFAULT 'recruiter' | admin / recruiter / viewer |
| `is_active` | BOOLEAN | DEFAULT true | Account status |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Registration time |

#### `company_users`

Links job seekers who opt in to be discoverable by companies.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | Link ID |
| `company_id` | UUID | FK → companies.id, NOT NULL | Company |
| `user_id` | UUID | FK → users.id, NOT NULL | Candidate (opted in) |
| `visibility` | VARCHAR(20) | DEFAULT 'private' | private / anonymized / full |
| `consent_given_at` | TIMESTAMPTZ | NULLABLE | When user opted in |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Link time |

#### `job_postings`

Company-owned job postings (distinct from user-saved jobs).

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | Posting ID |
| `company_id` | UUID | FK → companies.id, NOT NULL | Employer |
| `posted_by` | UUID | FK → recruiters.id, NOT NULL | Recruiter who posted |
| `title` | VARCHAR(255) | NOT NULL | Job title |
| `description` | TEXT | NOT NULL | Full JD |
| `location` | VARCHAR(255) | NULLABLE | Job location |
| `remote_type` | VARCHAR(20) | NULLABLE | remote / hybrid / onsite |
| `salary_min` | INTEGER | NULLABLE | Min salary |
| `salary_max` | INTEGER | NULLABLE | Max salary |
| `required_skills` | JSONB | DEFAULT '[]' | Extracted requirements |
| `status` | VARCHAR(20) | DEFAULT 'draft' | draft / active / closed |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Posted time |

#### `candidate_matches`

Recruiter-side AI-ranked candidate matches against a job posting.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | Match ID |
| `job_posting_id` | UUID | FK → job_postings.id, NOT NULL | Target posting |
| `user_id` | UUID | FK → users.id, NOT NULL | Candidate |
| `version_id` | UUID | FK → resume_versions.id, NOT NULL | Resume version matched |
| `overall_score` | FLOAT | NOT NULL | AI ranking score |
| `matched_skills` | JSONB | DEFAULT '[]' | Overlapping skills |
| `missing_skills` | JSONB | DEFAULT '[]' | Gaps |
| `ai_summary` | TEXT | NULLABLE | Recruiter-facing summary |
| `recruiter_status` | VARCHAR(20) | DEFAULT 'new' | new / shortlisted / rejected / contacted |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Match time |

### 7.4 Indexes

```sql
-- Resume versioning
CREATE INDEX idx_resume_profiles_user ON resume_profiles(user_id);
CREATE INDEX idx_resume_versions_profile ON resume_versions(profile_id, version_number);
CREATE INDEX idx_resume_versions_user ON resume_versions(user_id, created_at DESC);
CREATE INDEX idx_ats_history_version ON ats_score_history(version_id, created_at);
CREATE INDEX idx_ats_history_profile ON ats_score_history(profile_id, created_at);
CREATE INDEX idx_match_history_version_job ON match_score_history(version_id, job_id, created_at);
CREATE INDEX idx_match_history_user ON match_score_history(user_id, created_at DESC);

-- Jobs & matching
CREATE INDEX idx_jobs_user_id ON jobs(user_id);
CREATE INDEX idx_match_results_user_version ON match_results(user_id, version_id);
CREATE INDEX idx_skill_gaps_user ON skill_gaps(user_id, status);

-- Applications & outcomes
CREATE INDEX idx_applications_user_id ON applications(user_id);
CREATE INDEX idx_applications_status ON applications(user_id, status);
CREATE INDEX idx_applications_applied_date ON applications(user_id, applied_date);
CREATE INDEX idx_outcome_events_app ON outcome_events(application_id, event_type);
CREATE INDEX idx_outcome_events_user ON outcome_events(user_id, created_at DESC);
CREATE INDEX idx_app_packages_user ON application_packages(user_id, approval_status);

-- Analytics & audit
CREATE INDEX idx_analytics_snapshots_user_date ON user_analytics_snapshots(user_id, snapshot_date DESC);
CREATE INDEX idx_agent_audit_user ON agent_audit_log(user_id, created_at DESC);
CREATE INDEX idx_agent_audit_action ON agent_audit_log(action_type, created_at DESC);
CREATE INDEX idx_recommendation_signals_user ON recommendation_signals(user_id, signal_type);

-- B2B (future)
CREATE INDEX idx_job_postings_company ON job_postings(company_id, status);
CREATE INDEX idx_candidate_matches_posting ON candidate_matches(job_posting_id, overall_score DESC);

-- Roadmaps
CREATE INDEX idx_roadmap_modules_roadmap ON roadmap_modules(roadmap_id, order_index);
```

### 7.5 Migration Strategy

| Phase | Tables | Notes |
|---|---|---|
| Sprint 0 | All core tables including `agent_audit_log`, B2B tables (empty) | Single initial migration |
| Sprint 2 | `resume_profiles`, `resume_versions` replace flat `resumes` | Data migration script for any test data |
| Sprint 6 | `user_analytics_snapshots`, `outcome_events` | Nightly aggregation job |
| Phase 2 | `application_packages`, `recommendation_signals` | Human-in-the-loop workflow |
| Phase 4 | B2B tables activated | Recruiter auth domain added |

---

## 8. API Design

### 8.1 Conventions

| Convention | Value |
|---|---|
| Base URL | `/api/v1` |
| Format | JSON (request & response) |
| Auth | Bearer JWT in `Authorization` header |
| Errors | `{ "detail": "message", "code": "ERROR_CODE" }` |
| Pagination | `?page=1&limit=20` → `{ "data": [], "total": 100, "page": 1, "limit": 20 }` |
| Versioning | URL prefix (`/api/v1`) |

### 8.2 Authentication Endpoints

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/auth/register` | Create account | No |
| `POST` | `/auth/login` | Login, receive tokens | No |
| `POST` | `/auth/refresh` | Refresh access token | Refresh token |
| `POST` | `/auth/logout` | Invalidate refresh token | Yes |
| `POST` | `/auth/forgot-password` | Send reset email | No |
| `POST` | `/auth/reset-password` | Reset with token | No |
| `GET` | `/auth/me` | Current user profile | Yes |

**`POST /auth/register`**

```json
// Request
{ "email": "user@example.com", "password": "securePass123!", "full_name": "Jane Doe" }

// Response 201
{ "id": "uuid", "email": "user@example.com", "full_name": "Jane Doe", "access_token": "...", "refresh_token": "..." }
```

### 8.3 User Endpoints

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/users/me` | Get profile | Yes |
| `PATCH` | `/users/me` | Update profile | Yes |
| `GET` | `/users/me/preferences` | Get job preferences | Yes |
| `PUT` | `/users/me/preferences` | Update preferences | Yes |
| `GET` | `/users/me/dashboard` | Dashboard summary data | Yes |

**`GET /users/me/dashboard`**

```json
// Response 200
{
  "default_resume": {
    "profile_id": "uuid",
    "title": "Main Resume",
    "current_version": "v3",
    "ats_score": 91,
    "ats_improvement": 29
  },
  "applications": { "total": 12, "applied": 5, "interview": 2, "offer": 0, "interview_rate": 0.14 },
  "top_skill_gaps": [{ "skill_name": "Kubernetes", "priority": "critical" }],
  "recent_matches": [{ "job_title": "Senior SWE", "company": "Acme", "score": 0.82 }],
  "analytics_summary": { "applications_this_month": 4, "avg_match_score": 0.74 }
}
```

### 8.4 Resume Profile & Version Endpoints

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/resume-profiles` | Create profile + upload first version | Yes |
| `GET` | `/resume-profiles` | List user's resume profiles | Yes |
| `GET` | `/resume-profiles/{id}` | Get profile with current version summary | Yes |
| `PATCH` | `/resume-profiles/{id}` | Update profile metadata (title, default) | Yes |
| `DELETE` | `/resume-profiles/{id}` | Delete profile and all versions | Yes |
| `POST` | `/resume-profiles/{id}/versions` | Upload new version or create from edit | Yes |
| `GET` | `/resume-profiles/{id}/versions` | List all versions with scores | Yes |
| `GET` | `/resume-profiles/{id}/versions/{vid}` | Get specific version with parsed data | Yes |
| `POST` | `/resume-profiles/{id}/versions/{vid}/analyze` | Re-run ATS analysis | Yes |
| `GET` | `/resume-profiles/{id}/versions/{vid}/ats-score` | Get ATS score + feedback | Yes |
| `POST` | `/resume-profiles/{id}/versions/{vid}/score-against` | Score against a JD | Yes |
| `GET` | `/resume-profiles/{id}/improvement-history` | ATS score progression across versions | Yes |
| `GET` | `/resume-profiles/{id}/versions/compare` | Compare two versions side-by-side | Yes |
| `POST` | `/resume-profiles/{id}/versions/{vid}/suggest` | AI bullet point suggestions | Yes |

**`POST /resume-profiles/{id}/versions`**

```
Content-Type: multipart/form-data (upload) OR application/json (edit)
- file: (PDF or DOCX, max 5MB) — for upload source
- parsed_data: { ... } — for edit source
- source: upload | edit | ai_tailor | duplicate
- parent_version_id: uuid (optional)

Response 202:
{
  "id": "uuid",
  "version_number": 3,
  "version_label": "v3",
  "status": "processing",
  "parent_version_id": "uuid"
}
```

**`GET /resume-profiles/{id}/improvement-history`**

```json
// Response 200
{
  "profile_id": "uuid",
  "title": "Software Engineer Resume",
  "versions": [
    { "version_label": "v1", "ats_score": 62, "score_delta": null, "created_at": "2026-03-01" },
    { "version_label": "v2", "ats_score": 78, "score_delta": 16, "created_at": "2026-04-15" },
    { "version_label": "v3", "ats_score": 91, "score_delta": 13, "created_at": "2026-05-20" }
  ],
  "total_improvement": 29,
  "avg_improvement_per_version": 14.5
}
```

**`GET /resume-profiles/{id}/versions/compare?version_a={id}&version_b={id}`**

```json
// Response 200
{
  "version_a": { "label": "v1", "ats_score": 62 },
  "version_b": { "label": "v3", "ats_score": 91 },
  "ats_delta": 29,
  "section_diffs": [
    { "section": "experience", "changes": ["Added quantified metrics to 3 bullets"] },
    { "section": "skills", "changes": ["Added Kubernetes, CI/CD"] }
  ],
  "match_score_comparison": [
    { "job_title": "Senior SWE", "version_a_score": 0.65, "version_b_score": 0.82, "delta": 0.17 }
  ]
}
```

### 8.5 Job Endpoints

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/jobs` | Create/save a job (paste JD) | Yes |
| `GET` | `/jobs` | List saved jobs | Yes |
| `GET` | `/jobs/{id}` | Get job details | Yes |
| `PATCH` | `/jobs/{id}` | Update job (notes, save status) | Yes |
| `DELETE` | `/jobs/{id}` | Delete job | Yes |
| `POST` | `/jobs/{id}/match` | Match resume against job | Yes |
| `POST` | `/jobs/analyze` | Analyze JD without saving | Yes |

**`POST /jobs/{id}/match`**

```json
// Request
{ "version_id": "uuid" }

// Response 200
{
  "match_result_id": "uuid",
  "overall_score": 0.78,
  "ats_score": 72,
  "score_delta_from_prior": 0.05,
  "matched_skills": ["Python", "React", "PostgreSQL"],
  "partial_skills": [{ "required": "cloud infrastructure", "found": "AWS" }],
  "missing_skills": ["Kubernetes", "CI/CD"],
  "ai_analysis": "Your backend experience aligns well with this role..."
}
```

### 8.6 Skill Gap & Roadmap Endpoints

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/skill-gaps` | List user's skill gaps | Yes |
| `PATCH` | `/skill-gaps/{id}` | Update gap status | Yes |
| `POST` | `/roadmaps` | Generate learning roadmap | Yes |
| `GET` | `/roadmaps` | List roadmaps | Yes |
| `GET` | `/roadmaps/{id}` | Get roadmap with modules | Yes |
| `PATCH` | `/roadmaps/{id}/modules/{module_id}` | Update module status | Yes |

**`POST /roadmaps`**

```json
// Request
{ "match_result_id": "uuid", "title": "Path to Senior SWE at Acme" }
// OR
{ "skill_gap_ids": ["uuid1", "uuid2"], "target_role": "Senior Software Engineer" }

// Response 201
{
  "id": "uuid",
  "title": "Path to Senior SWE at Acme",
  "estimated_hours": 120,
  "modules": [
    {
      "order_index": 1,
      "title": "Kubernetes Fundamentals",
      "description": "Learn container orchestration...",
      "estimated_hours": 40,
      "resources": [
        { "type": "course", "title": "K8s for Developers", "url": "https://..." }
      ],
      "project_idea": "Deploy a microservices app on K8s"
    }
  ]
}
```

### 8.7 Application Endpoints

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/applications` | Create application | Yes |
| `GET` | `/applications` | List applications (filterable) | Yes |
| `GET` | `/applications/{id}` | Get application details | Yes |
| `PATCH` | `/applications/{id}` | Update application | Yes |
| `DELETE` | `/applications/{id}` | Delete application | Yes |
| `GET` | `/applications/stats` | Pipeline statistics | Yes |
| `POST` | `/applications/{id}/outcomes` | Record outcome event | Yes |
| `GET` | `/applications/{id}/outcomes` | List outcome events for application | Yes |

### 8.8 Analytics Endpoints

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/analytics/overview` | Full analytics dashboard data | Yes |
| `GET` | `/analytics/applications` | Application funnel metrics | Yes |
| `GET` | `/analytics/applications/monthly` | Applications per month time series | Yes |
| `GET` | `/analytics/resume-trends` | ATS improvement trends across versions | Yes |
| `GET` | `/analytics/skill-trends` | Skill completion and gap closure trends | Yes |
| `GET` | `/analytics/match-scores` | Average match score by outcome type | Yes |

**`GET /analytics/overview`**

```json
// Response 200
{
  "applications": {
    "total": 47,
    "this_month": 12,
    "interview_rate": 0.14,
    "rejection_rate": 0.62,
    "offer_rate": 0.04
  },
  "resume": {
    "current_ats_score": 91,
    "starting_ats_score": 62,
    "total_improvement": 29,
    "version_count": 3
  },
  "skills": {
    "gaps_identified": 15,
    "gaps_completed": 8,
    "completion_rate": 0.53
  },
  "matching": {
    "avg_match_score": 0.74,
    "avg_match_score_interviewed": 0.82,
    "avg_match_score_rejected": 0.61
  }
}
```

**`GET /analytics/applications/monthly?months=6`**

```json
// Response 200
{
  "data": [
    { "month": "2026-01", "applied": 5, "interviews": 1, "offers": 0, "rejections": 3 },
    { "month": "2026-02", "applied": 8, "interviews": 2, "offers": 0, "rejections": 5 }
  ]
}
```

### 8.9 Application Package Endpoints (Human-in-the-Loop)

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/application-packages` | AI creates application package | Yes |
| `GET` | `/application-packages` | List packages (filter by status) | Yes |
| `GET` | `/application-packages/{id}` | Get package for review | Yes |
| `POST` | `/application-packages/{id}/approve` | User approves package | Yes |
| `POST` | `/application-packages/{id}/reject` | User rejects package | Yes |
| `POST` | `/application-packages/{id}/submit` | Mark as submitted (user confirms) | Yes |
| `PATCH` | `/application-packages/{id}` | Edit cover letter or notes before approval | Yes |

**`POST /application-packages/{id}/approve`**

```json
// Response 200
{
  "id": "uuid",
  "approval_status": "approved",
  "approved_at": "2026-06-13T10:30:00Z",
  "message": "Package approved. You may now submit your application."
}
```

### 8.10 Agent Audit Endpoints

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/audit/activity` | User's AI activity log | Yes |
| `GET` | `/admin/audit` | Platform-wide audit log | Admin |
| `GET` | `/admin/audit/stats` | AI usage and cost stats | Admin |

**`GET /audit/activity?limit=20&action_type=job_matched`**

```json
// Response 200
{
  "data": [
    {
      "id": "uuid",
      "agent_name": "matching_agent",
      "action_type": "job_matched",
      "input_ref_type": "resume_version",
      "input_ref_id": "uuid",
      "output_ref_type": "match_result",
      "output_ref_id": "uuid",
      "approval_status": "not_required",
      "created_at": "2026-06-13T09:15:00Z"
    }
  ],
  "total": 156,
  "page": 1
}
```

### 8.11 AI / Interview Endpoints (P1)

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/ai/interview-questions` | Generate questions from JD | Yes |
| `POST` | `/ai/evaluate-answer` | Evaluate practice answer | Yes |
| `POST` | `/ai/improve-bullet` | Rewrite resume bullet | Yes |

**`GET /applications?status=interview_scheduled&sort=applied_date&order=desc`**

```json
// Response 200
{
  "data": [
    {
      "id": "uuid",
      "company": "Acme Corp",
      "position": "Senior SWE",
      "status": "interview_scheduled",
      "applied_date": "2026-05-15",
      "match_score": 0.82,
      "resume_version": { "id": "uuid", "version_label": "v3" },
      "notes": "Phone screen went well"
    }
  ],
  "total": 2,
  "page": 1,
  "limit": 20
}
```

### 8.12 Error Codes

| HTTP Status | Code | Description |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Invalid request body or parameters |
| 401 | `UNAUTHORIZED` | Missing or invalid token |
| 403 | `FORBIDDEN` | Insufficient permissions |
| 403 | `APPROVAL_REQUIRED` | Action requires user approval first |
| 404 | `NOT_FOUND` | Resource not found |
| 409 | `CONFLICT` | Duplicate email, etc. |
| 413 | `FILE_TOO_LARGE` | Resume exceeds 5 MB |
| 422 | `UNSUPPORTED_FILE` | File type not PDF/DOCX |
| 429 | `RATE_LIMITED` | AI request quota exceeded |
| 500 | `INTERNAL_ERROR` | Server error |
| 503 | `AI_SERVICE_UNAVAILABLE` | Gemini API down |

---

## 9. AI Agent Architecture

### 9.1 AI System Overview

HireLens uses a **hybrid AI architecture** combining local embeddings for fast similarity search and Gemini API for reasoning, generation, and structured extraction.

```
┌─────────────────────────────────────────────────────────────┐
│                    AI ORCHESTRATOR                          │
│              (backend/app/services/ai/)                    │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Resume      │  │ Matching     │  │ Coaching         │   │
│  │ Agent       │  │ Agent        │  │ Agent            │   │
│  │             │  │              │  │                  │   │
│  │ - Parse     │  │ - Embed      │  │ - Roadmap gen    │   │
│  │ - ATS score │  │ - Similarity │  │ - Interview Qs   │   │
│  │ - Suggest   │  │ - Gap detect │  │ - Answer eval    │   │
│  └──────┬──────┘  └──────┬───────┘  └────────┬─────────┘   │
│         │                │                    │             │
│  ┌──────▼────────────────▼────────────────────▼─────────┐   │
│  │              SHARED AI SERVICES                     │   │
│  │  ┌──────────────┐  ┌───────────────┐  ┌──────────┐  │   │
│  │  │ Gemini Client│  │ Embedding     │  │ FAISS    │  │   │
│  │  │ (LLM calls)  │  │ Service (ST)  │  │ Index    │  │   │
│  │  └──────────────┘  └───────────────┘  └──────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 9.2 Agent Definitions

#### 9.2.1 Resume Agent

**Purpose:** Parse, analyze, and improve resumes.

| Capability | Model | Input | Output |
|---|---|---|---|
| Text extraction | PyMuPDF / python-docx | PDF/DOCX file | Plain text |
| Structured parsing | Gemini 1.5 Flash | Resume text | JSON (parsed_data schema) |
| ATS scoring | Gemini 1.5 Flash | Parsed resume + rules | Score (0–100) + section feedback |
| JD-specific scoring | Gemini 1.5 Flash | Resume + JD text | Keyword match + tailored feedback |
| Bullet rewriting | Gemini 1.5 Pro | Bullet + context | Improved bullet suggestions |

**Prompt strategy:**
- System prompt defines ATS scoring rubric (formatting, keywords, quantification, section completeness)
- Structured output via Gemini JSON mode
- Temperature: 0.2 for scoring, 0.7 for suggestions

#### 9.2.2 Matching Agent

**Purpose:** Compute semantic fit between resumes and jobs; detect skill gaps.

| Capability | Model | Input | Output |
|---|---|---|---|
| Resume embedding | Sentence Transformers (`all-MiniLM-L6-v2`) | Resume text | 384-dim vector |
| Job embedding | Sentence Transformers | JD text | 384-dim vector |
| Similarity search | FAISS (IndexFlatIP) | Resume vector + job index | Top-K matches with scores |
| Skill extraction | Gemini 1.5 Flash | JD text | Required skills list |
| Gap analysis | Gemini 1.5 Flash | Resume skills + JD skills | Matched / partial / missing |
| Match narrative | Gemini 1.5 Pro | Resume + JD + scores | Human-readable analysis |

**Matching pipeline:**

```
1. Extract skills from resume (parsed_data.skills)
2. Extract skills from JD (Gemini)
3. Compute semantic similarity (FAISS cosine)
4. Compute skill overlap (exact + fuzzy via embeddings)
5. overall_score = 0.4 * semantic_sim + 0.6 * skill_overlap
6. Generate gap analysis and narrative (Gemini)
```

#### 9.2.3 Coaching Agent

**Purpose:** Generate learning roadmaps and interview preparation content.

| Capability | Model | Input | Output |
|---|---|---|---|
| Roadmap generation | Gemini 1.5 Pro | Skill gaps + target role | Ordered modules with resources |
| Interview questions | Gemini 1.5 Flash | JD + resume | Categorized question list |
| Answer evaluation | Gemini 1.5 Pro | Question + user answer | Score + feedback |
| STAR coaching | Gemini 1.5 Pro | Behavioral question + draft | Structured STAR response |

#### 9.2.4 Feedback Learning Agent (Phase 2+)

**Purpose:** Learn from application outcomes to improve recommendations.

| Capability | Model | Input | Output |
|---|---|---|---|
| Outcome ingestion | Rule-based | outcome_events | Updated recommendation_signals |
| Job re-ranking | Weighted scoring | user signals + match scores | Re-ranked job feed |
| Skill prioritization | Weighted scoring | completed gaps + outcomes | Re-prioritized gap list |
| Resume suggestion tuning | Pattern analysis | version performance by outcome | Targeted improvement suggestions |

### 9.3 Embedding Strategy

| Entity | Text Source | Index | Update Trigger |
|---|---|---|---|
| Resume version | Concatenation of summary + experience bullets + skills | Per-user FAISS sub-index | Version upload/edit |
| Job | Full JD text | Global FAISS index | Job save/ingest |
| Skills | Individual skill names | Skill lookup index | Skill taxonomy update |

**FAISS index management:**
- On startup: load all embeddings from PostgreSQL → build FAISS index
- On new embedding: add to index + persist to DB
- On resume delete: remove from index
- MVP: single-process index (no distributed sharding)
- Future: migrate to pgvector for persistence-native search

### 9.4 Prompt Templates

Stored in `backend/app/services/ai/prompts/` as versioned template files.

| Template | File | Purpose |
|---|---|---|
| `resume_parse.txt` | Structured extraction | Parse raw text to JSON |
| `ats_score.txt` | Scoring rubric | General ATS compatibility |
| `ats_score_jd.txt` | Scoring rubric | JD-specific ATS scoring |
| `skill_extract.txt` | Skill extraction | Extract skills from JD |
| `gap_analysis.txt` | Gap detection | Compare resume vs. JD skills |
| `match_narrative.txt` | Analysis generation | Human-readable match summary |
| `roadmap_generate.txt` | Roadmap creation | Learning path from gaps |
| `interview_questions.txt` | Question generation | Role-specific interview Qs |
| `answer_evaluate.txt` | Answer scoring | Evaluate practice answers |
| `bullet_improve.txt` | Resume improvement | Rewrite bullet points |

### 9.5 AI Guardrails

| Guardrail | Implementation |
|---|---|
| Rate limiting | 50 AI calls/user/day (MVP); Redis counter |
| Input sanitization | Strip HTML/scripts from pasted JD text |
| Output validation | Pydantic models validate all Gemini JSON responses |
| Fallback behavior | If Gemini fails, return embedding-only scores without narrative |
| Token budgeting | Max 8K tokens input per request; truncate long JDs |
| Content safety | Gemini safety settings enabled; filter inappropriate content |
| Cost tracking | Log token usage per request; daily cost dashboard |
| No PII in prompts to logs | Redact email/phone from logged prompt text |

### 9.6 Future Agentic Architecture (Phase 3+)

```
┌──────────────────────────────────────────────┐
│           CAREER COPILOT ORCHESTRATOR         │
│                                              │
│  ┌──────────┐ ┌──────────┐ ┌────────────┐   │
│  │ Discovery│ │ Apply    │ │ Interview  │   │
│  │ Agent    │ │ Agent    │ │ Agent      │   │
│  └────┬─────┘ └────┬─────┘ └─────┬──────┘   │
│       │            │              │          │
│  ┌────▼────────────▼──────────────▼───────┐  │
│  │         TOOL REGISTRY                  │  │
│  │  - search_jobs    - fill_form          │  │
│  │  - score_resume   - send_email         │  │
│  │  - generate_letter - schedule_reminder │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  User approval gate before any external act  │
└──────────────────────────────────────────────┘
```

Agents will use a ReAct-style loop with tool calling, always requiring explicit user confirmation before external actions (submitting applications, sending emails).

---

## 10. Security Requirements

### 10.1 Authentication & Authorization

| Requirement | Implementation |
|---|---|
| Password storage | bcrypt with cost factor 12 |
| Token strategy | JWT access token (15 min) + refresh token (7 days) |
| Refresh token storage | Hashed in database; rotated on use |
| Session invalidation | Logout clears refresh token; password change invalidates all sessions |
| Authorization model | User owns all resources; row-level filtering by `user_id` |
| OAuth (P1) | Google OAuth 2.0 with PKCE |

### 10.2 Data Protection

| Requirement | Implementation |
|---|---|
| Encryption in transit | TLS 1.3 on all endpoints |
| Encryption at rest | PostgreSQL volume encryption; S3 server-side encryption |
| PII fields | Email, name, phone, location — classified as PII |
| Resume files | Stored in private bucket; pre-signed URLs for access (15 min expiry) |
| Data retention | User data deleted within 30 days of account deletion request |
| GDPR readiness | Export user data endpoint; right to deletion |

### 10.3 API Security

| Requirement | Implementation |
|---|---|
| Rate limiting | 100 req/min per user (general); 50 AI req/day per user |
| Input validation | Pydantic models on all endpoints; max payload sizes enforced |
| CORS | Whitelist frontend origin only |
| CSRF | Not needed (JWT bearer, no cookies for auth) |
| File upload security | MIME type validation; file size limit (5 MB); virus scan (future) |
| SQL injection | SQLAlchemy ORM parameterized queries only |
| XSS | Frontend output encoding; CSP headers |

### 10.4 AI Security

| Requirement | Implementation |
|---|---|
| Prompt injection defense | Sanitize user-provided JD text; system prompts isolated |
| Output filtering | Validate AI responses against expected schemas |
| API key management | Gemini API key in environment variables; never in code or client |
| User data in AI calls | Send only necessary resume/job text; no user IDs in prompts |
| Audit logging | All AI actions logged to `agent_audit_log` with input/output refs |

### 10.5 Infrastructure Security

| Requirement | Implementation |
|---|---|
| Secrets management | Environment variables via platform (Railway/Render secrets) |
| Dependency scanning | Dependabot / `pip audit` + `npm audit` in CI |
| Container security | Non-root user in Docker; minimal base image |
| Database access | Connection pooling; no direct external DB access |
| Logging | Structured JSON logs; no PII in logs; centralized log aggregation |
| Backups | Daily PostgreSQL backups; 30-day retention |

### 10.7 Human-in-the-Loop Security

| Requirement | Implementation |
|---|---|
| No autonomous submission | `application_packages` require `approval_status = approved` before submit |
| Approval audit trail | Every approve/reject logged in `agent_audit_log` |
| Package immutability | Tailored resume version locked after approval |
| Rate limit on packages | Max 10 packages generated per user per day |
| User consent | Explicit checkbox: "I approve submitting this application" |
| Rollback | User can reject package; no data sent externally |

### 10.8 Compliance Considerations (Future)

| Standard | Relevance | Timeline |
|---|---|---|
| SOC 2 Type I | B2B customers, enterprise trust | Phase 3 |
| GDPR | EU users | Phase 2 |
| CCPA | California users | Phase 2 |
| EEOC compliance | AI must not introduce hiring bias | Ongoing — audit AI outputs for bias |

---

## 11. Folder Structure

```
HireLens-AI/
├── docs/
│   ├── PRD.md                          # This document
│   ├── API.md                          # API documentation (generated from OpenAPI)
│   └── ARCHITECTURE.md                 # Architecture decision records
│
├── frontend/                           # Next.js application
│   ├── public/
│   │   ├── logo.svg
│   │   └── favicon.ico
│   ├── src/
│   │   ├── app/                        # App Router pages
│   │   │   ├── (auth)/
│   │   │   │   ├── login/page.tsx
│   │   │   │   ├── register/page.tsx
│   │   │   │   └── layout.tsx
│   │   │   ├── (dashboard)/
│   │   │   │   ├── dashboard/page.tsx
│   │   │   │   ├── resumes/
│   │   │   │   │   ├── page.tsx                # Resume profile list
│   │   │   │   │   ├── upload/page.tsx         # Upload flow
│   │   │   │   │   └── [id]/
│   │   │   │   │       ├── page.tsx            # Profile detail + version list
│   │   │   │   │       ├── ats/page.tsx        # ATS score view
│   │   │   │   │       ├── history/page.tsx    # Improvement history chart
│   │   │   │   │       ├── compare/page.tsx    # Version comparison
│   │   │   │   │       └── versions/[vid]/page.tsx  # Version editor
│   │   │   │   ├── analytics/
│   │   │   │   │   └── page.tsx                # Application analytics dashboard
│   │   │   │   ├── jobs/
│   │   │   │   │   ├── page.tsx                # Saved jobs
│   │   │   │   │   ├── match/page.tsx          # Job matching
│   │   │   │   │   └── [id]/page.tsx           # Job detail + comparison
│   │   │   │   ├── roadmaps/
│   │   │   │   │   ├── page.tsx                # Roadmap list
│   │   │   │   │   └── [id]/page.tsx           # Roadmap detail
│   │   │   │   ├── applications/
│   │   │   │   │   ├── page.tsx                # Application tracker
│   │   │   │   │   ├── [id]/page.tsx           # Application detail
│   │   │   │   │   └── packages/[id]/page.tsx  # Review application package
│   │   │   │   ├── activity/
│   │   │   │   │   └── page.tsx                # AI activity log (user-facing)
│   │   │   │   ├── interview/
│   │   │   │   │   └── page.tsx                # Interview prep (P1)
│   │   │   │   ├── settings/page.tsx
│   │   │   │   └── layout.tsx                  # Dashboard layout (sidebar)
│   │   │   ├── layout.tsx                      # Root layout
│   │   │   ├── page.tsx                        # Landing page
│   │   │   └── globals.css
│   │   ├── components/
│   │   │   ├── ui/                             # Reusable UI primitives
│   │   │   │   ├── button.tsx
│   │   │   │   ├── card.tsx
│   │   │   │   ├── input.tsx
│   │   │   │   ├── modal.tsx
│   │   │   │   ├── badge.tsx
│   │   │   │   └── ...
│   │   │   ├── layout/
│   │   │   │   ├── sidebar.tsx
│   │   │   │   ├── header.tsx
│   │   │   │   └── footer.tsx
│   │   │   ├── resume/
│   │   │   │   ├── resume-uploader.tsx
│   │   │   │   ├── resume-editor.tsx
│   │   │   │   ├── ats-score-card.tsx
│   │   │   │   ├── section-feedback.tsx
│   │   │   │   ├── version-timeline.tsx
│   │   │   │   └── version-comparison.tsx
│   │   │   ├── jobs/
│   │   │   │   ├── job-input.tsx
│   │   │   │   ├── match-score-card.tsx
│   │   │   │   ├── skill-comparison.tsx
│   │   │   │   └── gap-list.tsx
│   │   │   ├── roadmaps/
│   │   │   │   ├── roadmap-timeline.tsx
│   │   │   │   └── module-card.tsx
│   │   │   ├── applications/
│   │   │   │   ├── application-form.tsx
│   │   │   │   ├── application-list.tsx
│   │   │   │   ├── status-pipeline.tsx
│   │   │   │   └── package-review.tsx          # Human-in-the-loop review
│   │   │   ├── analytics/
│   │   │   │   ├── funnel-chart.tsx
│   │   │   │   ├── monthly-trends.tsx
│   │   │   │   ├── resume-trend-chart.tsx
│   │   │   │   └── skill-progress-chart.tsx
│   │   │   ├── activity/
│   │   │   │   └── activity-log.tsx
│   │   │   └── dashboard/
│   │   │       ├── stats-cards.tsx
│   │   │       └── recent-activity.tsx
│   │   ├── lib/
│   │   │   ├── api.ts                          # API client wrapper
│   │   │   ├── auth.ts                         # Auth helpers
│   │   │   └── utils.ts                        # Utility functions
│   │   ├── hooks/
│   │   │   ├── use-auth.ts
│   │   │   ├── use-resume.ts
│   │   │   └── use-applications.ts
│   │   ├── stores/
│   │   │   └── auth-store.ts                   # Zustand auth state
│   │   └── types/
│   │       ├── resume.ts
│   │       ├── job.ts
│   │       ├── application.ts
│   │       └── api.ts
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.ts
│   └── .env.local.example
│
├── backend/                            # FastAPI application
│   ├── app/
│   │   ├── main.py                             # FastAPI app entry point
│   │   ├── config.py                           # Settings (pydantic-settings)
│   │   ├── dependencies.py                     # DI: db session, current user
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── router.py                   # Aggregates all v1 routers
│   │   │   │   ├── auth.py
│   │   │   │   ├── users.py
│   │   │   │   ├── resumes.py
│   │   │   │   ├── jobs.py
│   │   │   │   ├── applications.py
│   │   │   │   ├── application_packages.py
│   │   │   │   ├── analytics.py
│   │   │   │   ├── audit.py
│   │   │   │   ├── skill_gaps.py
│   │   │   │   ├── roadmaps.py
│   │   │   │   └── ai.py
│   │   │   └── deps.py                         # Shared route dependencies
│   │   ├── models/                             # SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── resume_profile.py
│   │   │   ├── resume_version.py
│   │   │   ├── job.py
│   │   │   ├── application.py
│   │   │   ├── application_package.py
│   │   │   ├── outcome_event.py
│   │   │   ├── agent_audit.py
│   │   │   ├── analytics.py
│   │   │   ├── skill_gap.py
│   │   │   ├── roadmap.py
│   │   │   ├── embedding.py
│   │   │   └── b2b/                            # Future: company, recruiter, etc.
│   │   ├── schemas/                            # Pydantic request/response schemas
│   │   │   ├── auth.py
│   │   │   ├── user.py
│   │   │   ├── resume.py
│   │   │   ├── resume_version.py
│   │   │   ├── analytics.py
│   │   │   ├── audit.py
│   │   │   ├── application_package.py
│   │   │   ├── job.py
│   │   │   ├── application.py
│   │   │   ├── skill_gap.py
│   │   │   ├── roadmap.py
│   │   │   └── ai.py
│   │   ├── services/                           # Business logic layer
│   │   │   ├── auth_service.py
│   │   │   ├── resume_service.py
│   │   │   ├── job_service.py
│   │   │   ├── match_service.py
│   │   │   ├── application_service.py
│   │   │   ├── roadmap_service.py
│   │   │   ├── analytics_service.py
│   │   │   ├── audit_service.py
│   │   │   ├── feedback_service.py
│   │   │   └── ai/
│   │   │       ├── orchestrator.py
│   │   │       ├── resume_agent.py
│   │   │       ├── matching_agent.py
│   │   │       ├── coaching_agent.py
│   │   │       ├── discovery_agent.py
│   │   │       ├── feedback_agent.py
│   │   │       ├── gemini_client.py
│   │   │       ├── embedding_service.py
│   │   │       ├── faiss_index.py
│   │   │       └── prompts/
│   │   │           ├── resume_parse.txt
│   │   │           ├── ats_score.txt
│   │   │           ├── ats_score_jd.txt
│   │   │           ├── skill_extract.txt
│   │   │           ├── gap_analysis.txt
│   │   │           ├── match_narrative.txt
│   │   │           ├── roadmap_generate.txt
│   │   │           └── interview_questions.txt
│   │   ├── workers/
│   │   │   ├── resume_processor.py
│   │   │   ├── embedding_worker.py
│   │   │   └── analytics_aggregator.py
│   │   ├── db/
│   │   │   ├── session.py                      # Async DB session factory
│   │   │   └── base.py                         # Declarative base
│   │   └── utils/
│   │       ├── security.py                     # JWT, password hashing
│   │       ├── file_handler.py                 # Upload validation & storage
│   │       └── rate_limiter.py
│   ├── alembic/                                # Database migrations
│   │   ├── versions/
│   │   └── env.py
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_resumes.py
│   │   ├── test_jobs.py
│   │   ├── test_matching.py
│   │   ├── test_applications.py
│   │   └── test_ai/
│   │       ├── test_resume_agent.py
│   │       └── test_matching_agent.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── docker-compose.yml                  # Local dev: PostgreSQL + Redis + backend
├── .github/
│   └── workflows/
│       ├── ci.yml                              # Lint + test on PR
│       └── deploy.yml                          # Deploy on merge to main
├── .gitignore
├── README.md
└── LICENSE
```

---

## 12. Development Sprints

### Sprint 0 — Foundation (Week 1–2)

**Goal:** Project scaffolding, dev environment, CI/CD pipeline.

| Task | Owner | Deliverable |
|---|---|---|
| Initialize monorepo structure | Backend + Frontend | Folder structure per Section 11 |
| Docker Compose for local dev | Backend | PostgreSQL 16 + Redis + backend container |
| FastAPI skeleton with health check | Backend | `/health` endpoint, OpenAPI docs |
| Next.js skeleton with Tailwind | Frontend | Landing page, layout, routing |
| SQLAlchemy models + Alembic setup | Backend | All tables from Section 7; initial migration |
| GitHub Actions CI | DevOps | Lint (ruff, eslint) + test on PR |
| Environment configuration | Backend | `.env.example`, pydantic-settings |
| README with setup instructions | All | Developer onboarding doc |

**Sprint 0 Exit Criteria:**
- [ ] `docker-compose up` starts all services
- [ ] Frontend renders landing page at `localhost:3000`
- [ ] Backend responds at `localhost:8000/health`
- [ ] Database migrations run successfully
- [ ] CI pipeline passes on empty test suite

---

### Sprint 1 — Authentication & User Management (Week 3–4)

**Goal:** Users can register, login, and manage profiles.

| Task | Owner | Deliverable |
|---|---|---|
| Auth service (register, login, JWT) | Backend | `POST /auth/register`, `/auth/login`, `/auth/refresh` |
| User model + preferences endpoints | Backend | `GET/PATCH /users/me`, `PUT /users/me/preferences` |
| Auth middleware + dependencies | Backend | `get_current_user` dependency |
| Login & register pages | Frontend | Form validation, error handling |
| Auth context + token management | Frontend | Zustand store, auto-refresh, protected routes |
| Dashboard layout (sidebar, header) | Frontend | Shell for authenticated pages |
| Settings page | Frontend | Profile edit, preferences form |
| Auth integration tests | Backend | Register, login, token refresh, unauthorized access |

**Sprint 1 Exit Criteria:**
- [ ] User can register, login, and see dashboard
- [ ] JWT tokens issued and refreshed correctly
- [ ] Protected routes redirect unauthenticated users
- [ ] User preferences saved and retrieved

---

### Sprint 2 — Resume Upload & Parsing (Week 5–6)

**Goal:** Users can upload resumes and see structured parsed data.

| Task | Owner | Deliverable |
|---|---|---|
| File upload endpoint | Backend | `POST /resumes` with multipart, validation |
| Resume text extraction | Backend | PyMuPDF (PDF) + python-docx (DOCX) |
| Gemini resume parsing agent | Backend | Structured JSON extraction |
| Background resume processor | Backend | ARQ worker for async parsing |
| Resume CRUD + versioning endpoints | Backend | `resume_profiles` + `resume_versions` API |
| Version creation on edit | Backend | Edits create new immutable versions |
| Agent audit logging | Backend | All parse operations logged |
| Resume upload page | Frontend | Drag-and-drop uploader, progress indicator |
| Resume profile + version UI | Frontend | Profile list, version timeline, editor |
| Resume processing tests | Backend | Upload, parse, edit, delete flows |

**Sprint 2 Exit Criteria:**
- [ ] User uploads PDF/DOCX and sees parsed resume within 30s
- [ ] Upload creates resume profile v1; edits create v2+
- [ ] Invalid files rejected with clear errors

---

### Sprint 3 — ATS Scoring (Week 7–8)

**Goal:** Users receive ATS compatibility scores with actionable feedback.

| Task | Owner | Deliverable |
|---|---|---|
| ATS scoring agent (Gemini) | Backend | General ATS score + section feedback |
| JD-specific scoring | Backend | `POST /resumes/{id}/score-against` |
| ATS score history per version | Backend | `ats_score_history` linked to `version_id` |
| Improvement history endpoint | Backend | `GET /resume-profiles/{id}/improvement-history` |
| Version comparison endpoint | Backend | Side-by-side diff API |
| Score recalculation on edit | Backend | Re-trigger on resume PATCH |
| ATS score card component | Frontend | Circular score gauge, color tiers |
| Section feedback component | Frontend | Per-section issues and suggestions |
| JD scoring page | Frontend | Paste JD, see tailored score |
| ATS score history chart | Frontend | Line chart per version |
| Improvement history page | Frontend | Version timeline with score progression |
| ATS agent tests | Backend | Score range validation, feedback structure |

**Sprint 3 Exit Criteria:**
- [ ] ATS score (0–100) generated for every parsed resume
- [ ] Section-level feedback actionable and accurate
- [ ] JD-specific scoring highlights missing keywords
- [ ] Score updates when resume is edited

---

### Sprint 4 — Job Matching & Skill Gaps (Week 9–10)

**Goal:** Users can match resumes to jobs and see skill gaps.

| Task | Owner | Deliverable |
|---|---|---|
| Embedding service (Sentence Transformers) | Backend | `all-MiniLM-L6-v2` model loading + inference |
| FAISS index manager | Backend | Build, add, search, rebuild index |
| Job CRUD endpoints | Backend | `POST/GET/PATCH/DELETE /jobs` |
| Matching agent | Backend | Semantic similarity + skill extraction + gap analysis |
| Match score history | Backend | `match_score_history` per version per job |
| Job input + saved jobs pages | Frontend | Paste JD, save jobs, list view |
| Match score page | Frontend | Overall score, skill comparison visualization |
| Skill gap list component | Frontend | Priority-coded gap cards |
| Side-by-side comparison view | Frontend | Resume skills vs. job requirements |
| Matching pipeline tests | Backend | End-to-end match flow with mock embeddings |

**Sprint 4 Exit Criteria:**
- [ ] User pastes JD and receives match score
- [ ] Matched, partial, and missing skills displayed
- [ ] AI narrative analysis generated
- [ ] Skill gaps stored and listed per user

---

### Sprint 5 — Learning Roadmaps (Week 11–12)

**Goal:** Users receive personalized learning roadmaps from skill gaps.

| Task | Owner | Deliverable |
|---|---|---|
| Coaching agent (roadmap generation) | Backend | Gemini-powered module generation |
| Roadmap CRUD endpoints | Backend | `POST/GET /roadmaps`, module status updates |
| Roadmap generation from gaps | Backend | Auto-create from match result |
| Roadmap timeline page | Frontend | Ordered modules with progress |
| Module card component | Frontend | Resources, project ideas, status toggle |
| Skill gap → roadmap linking | Frontend | "Generate Roadmap" CTA on gap analysis |
| Roadmap agent tests | Backend | Module structure validation, resource links |

**Sprint 5 Exit Criteria:**
- [ ] Roadmap generated from skill gaps with ≥ 3 modules
- [ ] Each module has resources and project idea
- [ ] User can mark modules as in-progress/completed
- [ ] Estimated hours displayed

---

### Sprint 6 — Application Tracker & Dashboard (Week 13–14)

**Goal:** Users can track applications and see a unified dashboard.

| Task | Owner | Deliverable |
|---|---|---|
| Application CRUD endpoints | Backend | Full lifecycle with status transitions |
| Application stats + analytics endpoints | Backend | Pipeline stats + `user_analytics_snapshots` |
| Outcome events API | Backend | `POST /applications/{id}/outcomes` |
| Analytics dashboard page | Frontend | Funnel, monthly trends, conversion rates |
| AI activity log page | Frontend | User-facing agent audit log |
| Application tracker page | Frontend | List view with filters, status badges |
| Application form (create/edit) | Frontend | Link to job, resume, notes |
| Status pipeline component | Frontend | Visual pipeline (saved → applied → interview → offer) |
| Dashboard page | Frontend | Stats cards, recent matches, top gaps |
| Application tracker tests | Backend | CRUD, status transitions, stats |

**Sprint 6 Exit Criteria:**
- [ ] User can create, update, and track applications
- [ ] All 7 status values supported
- [ ] Dashboard shows ATS score, application counts, top gaps, improvement trend
- [ ] Applications linked to resume versions
- [ ] Basic analytics: interview rate, rejection rate, monthly applications

---

### Sprint 7 — Polish, P1 Features & Launch Prep (Week 15–16)

**Goal:** MVP polish, stretch features, staging deployment.

| Task | Owner | Deliverable |
|---|---|---|
| Interview question generator (P1) | Backend + Frontend | `POST /ai/interview-questions` + practice UI |
| AI bullet suggestions (P1) | Backend + Frontend | `POST /resumes/{id}/suggest` + accept/reject UI |
| Google OAuth (P1) | Backend + Frontend | Social login flow |
| Error handling & loading states | Frontend | Skeleton loaders, toast notifications, error boundaries |
| Responsive design pass | Frontend | Mobile-friendly all pages |
| Rate limiting | Backend | Redis-based per-user limits |
| Staging deployment | DevOps | Vercel (frontend) + Railway (backend + DB) |
| End-to-end testing | QA | Core user flows: signup → upload → match → roadmap → apply |
| Performance optimization | Backend | Embedding model warm-up, response caching |
| Security audit | All | OWASP top 10 review, dependency audit |

**Sprint 7 Exit Criteria:**
- [ ] All P0 features functional on staging
- [ ] At least 2 P1 features shipped (interview questions, bullet suggestions)
- [ ] Core flows pass E2E tests
- [ ] Rate limiting active
- [ ] Staging URL accessible for beta testing

---

### Sprint Summary Timeline

```
Week  1  2  3  4  5  6  7  8  9  10  11  12  13  14  15  16
      ├─ S0 ─┤  ├─ S1 ─┤  ├─ S2 ─┤  ├─ S3 ─┤  ├─ S4 ──┤  ├─ S5 ──┤  ├─ S6 ──┤  ├─ S7 ──┤
      Foundation  Auth       Resume     ATS        Matching    Roadmaps   Apps       Launch
```

**Total MVP timeline: 16 weeks (4 months)**

### Post-MVP Sprint Cadence

- **2-week sprints** with demo at end of each
- **Sprint planning:** Prioritize from Phase 2 roadmap backlog
- **Retrospective:** After S7 and every 3 sprints thereafter
- **Beta program:** Start at end of Sprint 6 with 20–50 users
- **Public launch:** End of Sprint 7

- **Public launch:** End of Sprint 7

---

## 13. Resume Versioning System

### 13.1 Overview

Resume versioning is a first-class feature, not an afterthought. Every upload, edit, or AI tailoring creates an **immutable snapshot** so users can track improvement and correlate resume changes with application outcomes.

**Example progression:**

```
Resume v1 → ATS 62%  (upload, Mar 1)
Resume v2 → ATS 78%  (+16, edit after feedback, Apr 15)
Resume v3 → ATS 91%  (+13, AI-tailored for SWE roles, May 20)
Total improvement: +29 points across 3 versions
```

### 13.2 Version Creation Rules

| Trigger | Source Value | Behavior |
|---|---|---|
| Initial upload | `upload` | Creates profile + v1 |
| User edits parsed data | `edit` | Creates v(n+1) from current version; parent linked |
| AI bullet accept | `edit` | New version with accepted changes |
| AI tailor for job | `ai_tailor` | New version optimized for specific JD |
| Duplicate version | `duplicate` | Copy of existing version as starting point |

**Immutability rule:** Once a version reaches `status = ready` and has an ATS score, its `parsed_data`, `ats_score`, and `ats_feedback` are never modified. Edits always produce a new version.

### 13.3 Score Tracking

| Metric | Storage | Display |
|---|---|---|
| ATS score per version | `resume_versions.ats_score` + `ats_score_history` | Version timeline, improvement chart |
| ATS delta | `resume_versions.ats_score_delta` | Badge: "+16 from v1" |
| Match score per version per job | `match_score_history` | Comparison view, job-specific trend |
| Match delta | `match_score_history.score_delta` | "Match improved 17% after tailoring" |

### 13.4 API Endpoints

See [Section 8.4](#84-resume-profile--version-endpoints) for full endpoint list. Key operations:

- `POST /resume-profiles/{id}/versions` — Create new version
- `GET /resume-profiles/{id}/improvement-history` — ATS progression
- `GET /resume-profiles/{id}/versions/compare` — Side-by-side diff
- `GET /resume-profiles/{id}/versions/{vid}/match-history` — Match scores over versions for a job

### 13.5 UI Requirements

| Screen | Components | Behavior |
|---|---|---|
| **Profile list** | Profile cards with current version ATS score, version count | Show latest score badge and trend arrow (↑↓) |
| **Version timeline** | Vertical timeline: v1 → v2 → v3 with scores and dates | Click version to view; highlight best score |
| **Improvement chart** | Line chart: ATS score by version number | Annotate events ("Added metrics", "AI tailored") |
| **Version comparison** | Split-pane diff: sections, skills, scores | Select any two versions; show ATS and match deltas |
| **Version detail** | Full editor (creates new version on save) | Warn: "Saving will create v4" |
| **Match history tab** | Table: job title × version × match score | Heatmap showing which version performs best per job type |

### 13.6 Tier Limits

| Plan | Max profiles | Max versions per profile |
|---|---|---|
| Free | 1 | 5 |
| Pro | 3 | 20 |
| Premium | Unlimited | Unlimited |

---

## 14. Job Application Analytics

### 14.1 Overview

The analytics module transforms raw application data into actionable job-search intelligence. It helps users understand what's working and gives HireLens data for the feedback learning loop.

### 14.2 Tracked Metrics

| Metric | Formula | Source |
|---|---|---|
| Total applications | COUNT(applications) | `applications` |
| Applications per month | COUNT GROUP BY month(applied_date) | `applications` |
| Interview rate | (interview_scheduled + interview_passed) / applied | `applications`, `outcome_events` |
| Rejection rate | rejected / applied | `outcome_events` |
| Offer rate | (offer_received + offer_accepted) / applied | `outcome_events` |
| Average match score | AVG(match_score) across applications | `applications` |
| Avg match score (interviewed) | AVG(match_score) WHERE outcome = interview | `applications` + `outcome_events` |
| Resume improvement trend | latest ATS − first ATS | `resume_versions` |
| Skill improvement trend | gaps completed / gaps identified over time | `skill_gaps`, `roadmap_modules` |

### 14.3 Database Design

**Primary tables:** `applications`, `outcome_events`, `user_analytics_snapshots`, `resume_versions`, `match_score_history`, `skill_gaps`

**Nightly aggregation job** (`analytics_aggregator.py`):
1. Compute per-user metrics
2. Upsert into `user_analytics_snapshots`
3. Cache result in Redis (TTL: 1 hour)

### 14.4 Dashboard Widgets

| Widget | Type | Data Source | Placement |
|---|---|---|---|
| **Application Funnel** | Funnel chart: saved → applied → interview → offer | `applications` by status | Dashboard top |
| **Monthly Applications** | Bar chart: applications per month (6-month window) | `user_analytics_snapshots` | Analytics page |
| **Conversion Rates** | Stat cards: interview %, rejection %, offer % | Computed rates | Analytics page |
| **Resume Score Trend** | Line chart: ATS score by version | `resume_versions` | Dashboard + Analytics |
| **Match Score by Outcome** | Grouped bar: avg match for interviewed vs rejected | `applications` + `outcome_events` | Analytics page |
| **Skill Progress** | Progress ring: gaps completed / total | `skill_gaps` | Dashboard |
| **Best Performing Version** | Card: version with highest interview rate | Cross-reference versions + outcomes | Analytics page |
| **Activity Summary** | Stat row: AI actions this week | `agent_audit_log` | Dashboard |

### 14.5 API Endpoints

See [Section 8.8](#88-analytics-endpoints). All endpoints require authentication and return data scoped to `user_id` only.

---

## 15. Feedback Learning Loop

### 15.1 Overview

HireLens improves over time by learning from real application outcomes. When users record what happened after applying, the system adjusts future recommendations.

### 15.2 Outcome Events

| Event | Trigger | Signal Generated |
|---|---|---|
| `applied` | User marks application as applied | Baseline: match score + version used |
| `viewed` | User reports employer viewed resume | Positive: version + job type correlation |
| `rejected` | User reports rejection | Negative: down-rank similar jobs/skills |
| `interview_scheduled` | User reports interview invite | Strong positive: up-rank job profile match |
| `interview_passed` | User reports passing interview | Strong positive: up-rank resume patterns |
| `offer_received` | User reports offer | Very strong positive: reinforce full package |
| `offer_accepted` | User accepts offer | Gold-standard signal for model training |

### 15.3 Data Model

```
applications ──→ outcome_events ──→ recommendation_signals
                      │
                      └──→ agent_audit_log (outcome_recorded)
```

**`recommendation_signals`** stores per-user learned weights:
- `signal_type = job` → job categories that lead to interviews
- `signal_type = skill` → skills correlated with positive outcomes
- `signal_type = resume_suggestion` → edit types that improve results

### 15.4 Recommendation Workflow

```
1. User applies with version v3 (match score 0.82)
2. User records outcome: interview_scheduled
3. Feedback Agent processes:
   a. Increment weight for job category (+0.1)
   b. Increment weight for skills in v3 (+0.05 each)
   c. Record: v3 + this job type → positive outcome
4. Next job recommendations:
   overall_rank = semantic_score * 0.5 + skill_overlap * 0.3 + signal_weight * 0.2
5. Next skill recommendations:
   Prioritize gaps that appear in positively-correlated jobs
6. Next resume suggestions:
   Suggest edits similar to those in v3 (which got interview)
```

### 15.5 Future AI Learning Strategy

| Phase | Approach | Data Required |
|---|---|---|
| **Phase 2 (MVP+)** | Rule-based weight adjustment | 100+ outcomes per user |
| **Phase 3** | Collaborative filtering across anonymized users | 10,000+ outcomes platform-wide |
| **Phase 4** | Fine-tuned ranking model (LightGBM / small NN) | 100,000+ outcomes; feature engineering pipeline |
| **Phase 5** | LLM-based personalized coaching from outcome patterns | Full career trajectory data per user |

**Privacy guardrails:**
- Cross-user learning uses only anonymized, aggregated patterns
- No user can see another user's outcomes
- Users can opt out of contributing to aggregate learning
- All learning weights are explainable ("Recommended because similar roles led to interviews")

---

## 16. Recruiter & Company Portal (Future B2B)

### 16.1 Overview

The B2B portal is reserved in the schema from Sprint 0 but not activated until Phase 4. This avoids costly migrations later and ensures candidate data models are recruiter-ready.

### 16.2 Database Tables

See [Section 7.3](#73-future-b2b-tables-schema-reserved): `companies`, `recruiters`, `company_users`, `job_postings`, `candidate_matches`.

### 16.3 Future Features

| Feature | Description | Phase |
|---|---|---|
| **Candidate search** | Search opted-in candidates by skills, experience, location | Phase 4 |
| **Resume search** | Semantic search across anonymized resume embeddings | Phase 4 |
| **AI candidate ranking** | Rank candidates against a job posting with explainable scores | Phase 4 |
| **Recruiter dashboard** | Pipeline: new matches → shortlisted → contacted → hired | Phase 4 |
| **Bias audit** | AI ranking fairness report per job posting | Phase 5 |

### 16.4 Candidate Consent Model

- Job seekers must explicitly opt in to be discoverable
- Default visibility: `private` (not searchable)
- Options: `anonymized` (skills + scores, no name/contact) or `full` (complete profile)
- Consent is revocable; data removed from recruiter indexes within 24 hours

### 16.5 Architecture Reservation

- Separate auth domain for recruiters (`/api/v1/recruiter/...`)
- B2B tables created in Sprint 0 migration (empty, no API exposure)
- Candidate embeddings shared with job seeker index (read-only for recruiters)
- Row-level security: recruiters see only their company's data

---

## 17. Agent Audit & Activity Log

### 17.1 Overview

Every AI action in HireLens is logged. This supports user trust, debugging, compliance, and cost attribution.

### 17.2 Logged Actions

| Action Type | Agent | Input Ref | Output Ref | Approval |
|---|---|---|---|---|
| `resume_analyzed` | resume_agent | resume_version | resume_version | not_required |
| `ats_score_generated` | resume_agent | resume_version | ats_score_history | not_required |
| `job_matched` | matching_agent | resume_version + job | match_result | not_required |
| `roadmap_generated` | coaching_agent | skill_gaps | learning_roadmap | not_required |
| `resume_tailored` | resume_agent | resume_version + job | resume_version (new) | not_required |
| `cover_letter_generated` | coaching_agent | resume_version + job | application_package | not_required |
| `job_discovered` | discovery_agent | user_preferences | job | not_required |
| `application_suggested` | discovery_agent | match_result | application_package | pending |
| `user_approved` | system | application_package | application_package | approved |
| `user_rejected` | system | application_package | application_package | rejected |
| `application_submitted` | system | application_package | application | approved |

### 17.3 Database Schema

See `agent_audit_log` in [Section 7.2](#72-core-table-definitions).

**Retention:** 2 years for user-facing logs; 5 years for admin logs.

### 17.4 API Endpoints

See [Section 8.10](#810-agent-audit-endpoints).

### 17.5 Admin Dashboard Requirements

| View | Features |
|---|---|
| **Activity feed** | Real-time stream of all AI actions; filter by agent, user, action type, date |
| **Cost dashboard** | Token usage and estimated cost per agent, per user, per day |
| **Error monitor** | Failed AI actions with error metadata; alert on error rate > 5% |
| **Approval queue** | Pending application packages across all users (for support) |
| **Export** | CSV export of audit log for compliance review |

### 17.6 User-Facing Activity Log

Users see a simplified view at `/activity`:
- Last 50 AI actions on their account
- Plain-language descriptions ("Analyzed your resume v3", "Matched you to Senior SWE at Acme — 82%")
- Approval status for actions requiring consent
- Link to relevant entity (resume, job, application package)

---

## 18. Human-in-the-Loop Application System

### 18.1 Design Principle

**HireLens NEVER automatically submits a job application.** AI prepares; the user decides.

### 18.2 Workflow

```
┌─────────────────┐
│ Discovery Agent │  Finds job matching user profile
└────────┬────────┘
         ▼
┌─────────────────┐
│ Matching Agent  │  Calculates match score (e.g., 82%)
└────────┬────────┘
         ▼
┌─────────────────┐
│  Resume Agent   │  Tailors resume → creates new version (ai_tailor)
└────────┬────────┘
         ▼
┌─────────────────┐
│ Coaching Agent  │  Generates cover letter draft
└────────┬────────┘
         ▼
┌─────────────────┐
│ Application     │  status: pending_review
│ Package Created │
└────────┬────────┘
         ▼
┌─────────────────┐
│  USER REVIEWS   │  Sees: tailored resume, cover letter, match score, gaps
│  in UI          │  Can edit cover letter, swap resume version
└────────┬────────┘
         ▼
    ┌────┴────┐
    ▼         ▼
 APPROVE   REJECT
    │         │
    ▼         ▼
 approved  rejected
    │
    ▼
┌─────────────────┐
│ USER SUBMITS    │  User applies on company site (or future integration)
│ (manual confirm)│  Marks as submitted in HireLens
└────────┬────────┘
         ▼
┌─────────────────┐
│ Outcome Events  │  User records: viewed → interview → offer
└─────────────────┘
```

### 18.3 Approval States

| State | Description | Transitions |
|---|---|---|
| `pending_review` | AI package ready; awaiting user | → approved, rejected |
| `approved` | User approved content | → submitted |
| `rejected` | User declined package | Terminal |
| `submitted` | User confirmed external submission | Terminal |
| `expired` | Package older than 30 days without action | Terminal |

### 18.4 Database Schema

See `application_packages` in [Section 7.2](#72-core-table-definitions).

### 18.5 API Requirements

See [Section 8.9](#89-application-package-endpoints-human-in-the-loop).

**Critical API rules:**
- `POST /application-packages/{id}/submit` returns 403 unless `approval_status = approved`
- `POST /application-packages/{id}/approve` requires authenticated user who owns the package
- All state transitions logged in `agent_audit_log`

### 18.6 Security Requirements

See [Section 10.7](#107-human-in-the-loop-security).

---

## 19. Success Metrics & KPIs

### 19.1 KPI Categories

#### User Growth

| Metric | 3 Months | 6 Months | 12 Months |
|---|---|---|---|
| Registered users | 500 | 3,000 | 15,000 |
| Monthly Active Users (MAU) | 200 | 2,000 | 10,000 |
| DAU/MAU ratio | ≥ 20% | ≥ 25% | ≥ 30% |
| Organic signup % | ≥ 40% | ≥ 50% | ≥ 55% |
| Referral rate | ≥ 5% | ≥ 10% | ≥ 15% |

#### Resume Improvement

| Metric | 3 Months | 6 Months | 12 Months |
|---|---|---|---|
| Resumes uploaded | 800 | 6,000 | 30,000 |
| Avg versions per user | 1.5 | 2.5 | 3.5 |
| Avg ATS improvement (30 days) | +8 pts | +12 pts | +15 pts |
| Users reaching ATS ≥ 80 | 20% | 35% | 50% |
| Version comparison usage | 10% | 25% | 40% |

#### Application Success

| Metric | 3 Months | 6 Months | 12 Months |
|---|---|---|---|
| Applications tracked | 300 | 3,000 | 20,000 |
| Avg applications per active user | 3 | 8 | 15 |
| Interview conversion (applied → interview) | 8% | 10% | 12% |
| Offer rate (applied → offer) | 2% | 3% | 5% |
| Avg match score at application | 0.65 | 0.72 | 0.78 |

#### Interview Conversion

| Metric | 3 Months | 6 Months | 12 Months |
|---|---|---|---|
| Interview prep sessions | 50 | 500 | 3,000 |
| Users using interview prep | 15% | 30% | 45% |
| Interview → offer rate | 15% | 20% | 25% |

#### Retention

| Metric | 3 Months | 6 Months | 12 Months |
|---|---|---|---|
| D7 retention | 30% | 35% | 40% |
| D30 retention | 20% | 28% | 35% |
| D90 retention | 10% | 18% | 25% |
| Churn rate (monthly) | < 15% | < 12% | < 10% |
| NPS | 25 | 35 | 40 |

#### Subscription Revenue

| Metric | 3 Months | 6 Months | 12 Months |
|---|---|---|---|
| Paid subscribers | 0 (beta) | 150 | 800 |
| Free → Pro conversion | — | 5% | 8% |
| Pro → Premium upgrade | — | 15% | 20% |
| MRR | $0 | $2,250 | $15,000 |
| ARPU (paid) | — | $15 | $18 |
| LTV/CAC ratio | — | ≥ 2:1 | ≥ 3:1 |

---

## 20. Competitive Analysis

### 20.1 Competitive Landscape

| Platform | Primary Focus | AI Depth | Application Tracking | Resume Versioning | India Market |
|---|---|---|---|---|---|
| **LinkedIn** | Networking + job board | Low (basic insights) | None | None | Strong |
| **Naukri** | India job board | Low | Basic | None | Dominant |
| **Indeed** | Global job board | Low | None | None | Strong |
| **Foundit** (Monster India) | India job board | Low | None | None | Strong |
| **Teal** | Career copilot | Medium | Strong | Basic | Weak |
| **Jobscan** | ATS optimization | Medium | None | None | Weak |
| **HireLens AI** | AI career copilot | High | Strong | Advanced | Planned |

### 20.2 Detailed Comparison

#### LinkedIn

| | |
|---|---|
| **Strengths** | Massive network, employer brand, Easy Apply, professional identity |
| **Weaknesses** | No ATS scoring, no skill gap analysis, no learning roadmaps, noisy feed |
| **HireLens advantage** | Deeper AI analysis, version tracking, outcome-based learning, application intelligence |

#### Naukri / Foundit (India)

| | |
|---|---|
| **Strengths** | India-specific job inventory, recruiter relationships, brand trust |
| **Weaknesses** | Legacy UX, keyword-based matching, no AI coaching, application black hole |
| **HireLens advantage** | AI-first experience, semantic matching, skill roadmaps, analytics dashboard |

#### Indeed

| | |
|---|---|
| **Strengths** | Largest job inventory globally, simple UX, employer reviews |
| **Weaknesses** | No resume intelligence, no career coaching, commoditized experience |
| **HireLens advantage** | End-to-end copilot, not just discovery; personalized improvement loop |

#### Teal

| | |
|---|---|
| **Strengths** | Closest competitor; job tracking, resume builder, Chrome extension |
| **Weaknesses** | Limited AI depth, no semantic matching, no learning roadmaps, US-centric |
| **HireLens advantage** | Semantic matching (FAISS), skill gap → roadmap pipeline, outcome learning, version analytics |

#### Jobscan

| | |
|---|---|
| **Strengths** | Best-in-class ATS scoring, keyword analysis, market leader for ATS |
| **Weaknesses** | Single-feature tool, no job matching, no application tracking, no coaching |
| **HireLens advantage** | ATS scoring plus full career workflow; Jobscan is a feature within HireLens |

### 20.3 HireLens Differentiators (Summary)

1. **Only platform** combining ATS scoring + semantic matching + skill roadmaps + application analytics + outcome learning
2. **Immutable resume versioning** with improvement trajectories (no competitor does this well)
3. **Human-in-the-loop** application assistance (trust-first, not auto-apply)
4. **Full agent audit trail** (transparency no competitor offers)
5. **India + global** positioning with semantic AI (not keyword matching)
6. **Feedback learning loop** that improves recommendations from real outcomes

### 20.4 Competitive Risks

| Risk | Mitigation |
|---|---|
| LinkedIn adds AI coaching | Move fast; depth over breadth; outcome data moat |
| Teal expands AI features | Differentiate on semantic matching + roadmaps + India market |
| Jobscan adds job tracking | Full-platform value prop; Jobscan is one feature we offer |
| Naukri builds AI team | Partner or integrate; focus on AI quality and UX |

---

## 21. Monetization Strategy

### 21.1 Pricing Philosophy

- **Free tier is genuinely useful** — not a crippled demo; drives word-of-mouth
- **Pro unlocks volume and depth** — for active job seekers
- **Premium unlocks intelligence** — for career switchers and power users
- **Recruiter is B2B** — separate pricing, separate value prop

### 21.2 Plan Comparison

| Feature | Free | Pro ($15/mo) | Premium ($29/mo) | Recruiter ($99/mo) |
|---|---|---|---|---|
| Resume profiles | 1 | 3 | Unlimited | — |
| Versions per profile | 5 | 20 | Unlimited | — |
| ATS scores per month | 5 | Unlimited | Unlimited | — |
| Job matches per month | 10 | Unlimited | Unlimited | — |
| Learning roadmaps | 1 active | 5 active | Unlimited | — |
| Application tracking | 10 | Unlimited | Unlimited | — |
| Analytics dashboard | Basic | Full | Full + export | — |
| Interview prep | — | 20 sessions/mo | Unlimited | — |
| AI bullet rewrites | 5/mo | Unlimited | Unlimited | — |
| Cover letter generation | — | 10/mo | Unlimited | — |
| Application packages | — | 5/mo | Unlimited | — |
| Job discovery agent | — | Daily digest | Real-time | — |
| Outcome learning | Basic | Full | Full + insights | — |
| Priority AI processing | — | — | ✓ | — |
| Candidate search | — | — | — | 500/mo |
| AI candidate ranking | — | — | — | ✓ |
| Job postings | — | — | — | 10 active |

### 21.3 Feature Gating Implementation

| Gate | Implementation |
|---|---|
| Plan tier check | `users.plan_tier` checked in API middleware |
| Usage counters | Redis counters per feature per billing period |
| Soft limits | Warning at 80% usage; hard block at 100% |
| Upgrade CTA | In-app modal with plan comparison when limit hit |
| Grace period | 3-day grace after downgrade before feature lock |

### 21.4 Revenue Projections

| Period | Free Users | Pro ( $15) | Premium ($29) | Recruiter ($99) | MRR |
|---|---|---|---|---|---|
| Month 6 | 2,700 | 120 | 30 | 0 | $2,670 |
| Month 12 | 9,200 | 550 | 250 | 5 | $15,445 |
| Month 18 | 25,000 | 1,500 | 700 | 20 | $52,830 |

### 21.5 Pricing Strategy Notes

- Annual plans: 20% discount (2 months free)
- Student discount: 50% off Pro for .edu emails
- India pricing: ₹499/mo Pro, ₹999/mo Premium (PPP-adjusted)
- Launch promo: First 500 users get 3 months Pro free
- Payment processor: Stripe (global) + Razorpay (India)

---

## 22. Technical Scalability Roadmap

### 22.1 Scaling Tiers Overview

| Tier | Users | Infrastructure | Monthly Cost (est.) |
|---|---|---|---|
| **Seed** | 1,000 | Single-region, monolith | $200–500 |
| **Growth** | 10,000 | Read replicas, worker scaling | $1,500–3,000 |
| **Scale** | 100,000 | Sharded DB, dedicated AI service | $8,000–15,000 |
| **Platform** | 1,000,000 | Multi-region, microservices | $50,000–100,000 |

### 22.2 Database Scaling

| Tier | Strategy | Details |
|---|---|---|
| 1K | Single PostgreSQL instance | Railway/Supabase; connection pooling via PgBouncer |
| 10K | Primary + 1 read replica | Read-heavy queries (analytics, audit log) offloaded to replica |
| 100K | Partitioning + read replicas | Partition `agent_audit_log` and `outcome_events` by month; 3 read replicas |
| 1M | Citus/sharding + dedicated analytics DB | Shard `users` by hash; separate OLAP store (ClickHouse or TimescaleDB) for analytics |

**Key decisions:**
- Migrate embeddings from BYTEA to **pgvector** at 10K users
- `user_analytics_snapshots` prevents expensive real-time aggregation at scale
- Archive audit logs older than 2 years to cold storage (S3 + Parquet)

### 22.3 AI Inference Scaling

| Tier | Strategy | Details |
|---|---|---|
| 1K | Inline + background workers | Gemini API calls in ARQ workers; ST model loaded in API process |
| 10K | Dedicated AI worker pool | 2–4 GPU/CPU workers for embeddings; Gemini via API with retry |
| 100K | AI service separation | Standalone `ai-service` container; request queue with priority (Premium first) |
| 1M | Multi-model routing + caching | Cache identical ATS scores; Gemini Flash for bulk, Pro for premium; consider self-hosted LLM for embeddings |

**Cost management:**
- Gemini Flash for parsing/scoring (cheap); Pro for roadmaps/coaching (quality)
- Embedding cache: hash resume text → skip re-embedding if unchanged
- Batch embedding generation during off-peak hours

### 22.4 Search Infrastructure

| Tier | Strategy | Details |
|---|---|---|
| 1K | FAISS in-memory (single process) | Rebuild on deploy; < 10K vectors |
| 10K | FAISS persistent + pgvector fallback | Save FAISS index to disk; pgvector for durability |
| 100K | Dedicated vector DB (Qdrant or Pinecone) | Distributed index; filter by user_id |
| 1M | Sharded vector index | Per-region indexes; hybrid search (vector + keyword via Elasticsearch) |

### 22.5 Caching Strategy

| Layer | Tool | TTL | Contents |
|---|---|---|---|
| API response | Redis | 5–60 min | Dashboard data, analytics snapshots, job lists |
| AI results | Redis | 24 hours | ATS scores, match results (keyed by version + job hash) |
| Embeddings | PostgreSQL + memory | Permanent | Stored in DB; hot cache in worker memory |
| Static assets | CDN (Vercel Edge) | Permanent | Frontend JS/CSS, images |
| Session | Redis | 7 days | Refresh tokens, user preferences |

**Cache invalidation triggers:**
- Resume version created → invalidate profile cache + analytics
- Application status changed → invalidate application stats
- Outcome recorded → invalidate recommendation signals + analytics

### 22.6 Infrastructure Evolution

```
1K users:     [Vercel] → [Railway: API + DB + Redis + Worker]
10K users:    [Vercel] → [Load Balancer] → [API × 2] + [Worker × 2] + [PG Primary/Replica] + [Redis]
100K users:   [Vercel] → [ALB] → [API × 4] + [AI Service × 2] + [Worker × 4] + [PG Cluster] + [Qdrant] + [Redis Cluster]
1M users:     [CDN] → [Multi-region ALB] → [API fleet] + [AI fleet] + [Worker fleet] + [Citus] + [Qdrant] + [ClickHouse] + [Redis Cluster]
```

---

## Appendix A: Glossary

| Term | Definition |
|---|---|
| ATS | Applicant Tracking System — software employers use to filter resumes |
| ATS Score | HireLens compatibility score (0–100) predicting resume parseability by ATS |
| Application Package | AI-prepared bundle (tailored resume + cover letter) awaiting user approval |
| Embedding | Dense vector representation of text for semantic similarity |
| FAISS | Facebook AI Similarity Search — library for efficient vector search |
| Human-in-the-Loop | Design pattern requiring explicit user approval before external actions |
| JD | Job Description |
| Outcome Event | User-reported application result (interview, rejection, offer) |
| Recommendation Signal | Learned weight adjusting future job/skill/resume suggestions |
| Resume Profile | Parent entity for a logical resume document |
| Resume Version | Immutable snapshot of a resume at a point in time (v1, v2, v3…) |
| Semantic Match | Similarity based on meaning, not just keyword overlap |
| Skill Gap | A required skill present in a JD but absent from the user's resume |
| Roadmap Module | A single learning unit within a roadmap (skill + resources + project) |

## Appendix B: Open Questions

| # | Question | Owner | Target Resolution |
|---|---|---|---|
| 1 | Which job board APIs to integrate in Phase 2? | Product | Sprint 7 |
| 2 | Stripe vs Razorpay primary for India launch? | Product | Phase 2 |
| 3 | pgvector migration timing — at 5K or 10K users? | Engineering | Sprint 8 |
| 4 | Legal review of automated job application features? | Legal | Phase 3 |
| 5 | Data residency requirements for EU users? | Engineering | Phase 2 |
| 6 | Self-hosted LLM for cost reduction at 100K users? | Engineering | Phase 3 |
| 7 | B2B candidate consent UX design? | Product | Phase 3 |

## Appendix C: Architectural Risks & Pre-Development Recommendations

The following risks should be addressed before or during Sprint 0 to avoid costly rework.

### C.1 Critical Risks (Address Before Sprint 1)

| # | Risk | Impact | Recommendation |
|---|---|---|---|
| R1 | **FAISS in-memory index lost on deploy** | All match scores fail until rebuild; downtime on every deployment | Persist embeddings in PostgreSQL from day 1; rebuild FAISS on startup with health-check gate; plan pgvector migration at 10K users |
| R2 | **Resume versioning not enforced early** | Flat resume model creates migration pain; no improvement tracking | Implement `resume_profiles` + `resume_versions` in Sprint 0 schema; never store editable state on scored snapshots |
| R3 | **Gemini API rate limits / downtime** | Core features (parsing, scoring, roadmaps) unavailable | Implement circuit breaker + graceful degradation (embedding-only scores without narrative); cache ATS results by content hash |
| R4 | **No audit log from day 1** | Cannot debug AI issues or demonstrate trust to users | Create `agent_audit_log` table in Sprint 0; wire logging into AI orchestrator from first Gemini call |
| R5 | **Application status enum too simple** | Cannot power analytics or feedback loop without migration | Use full outcome enum (7 states) from Sprint 0; add `outcome_events` table in Sprint 6 |

### C.2 High Risks (Address During MVP Sprints)

| # | Risk | Impact | Recommendation |
|---|---|---|---|
| R6 | **AI cost explosion at scale** | Gemini costs exceed revenue at 10K users | Token budgeting per request; Flash for scoring, Pro only for roadmaps; per-user daily limits by plan tier; cost dashboard from Sprint 3 |
| R7 | **Resume parsing accuracy** | Garbage-in → garbage-out for all downstream features | Human-in-the-loop verification step after parse; show confidence scores per section; allow easy correction before scoring |
| R8 | **Prompt injection via job descriptions** | LLM manipulation; data leakage | Sanitize all user-provided text; isolate system prompts; validate all JSON outputs with Pydantic; never execute LLM-suggested code |
| R9 | **Analytics computed in real-time** | Dashboard slow at 10K+ users; expensive queries | Use `user_analytics_snapshots` with nightly aggregation from Sprint 6; never compute funnel metrics on raw tables in API request path |
| R10 | **Single-region deployment** | Latency for India users; no disaster recovery | Design for US-East MVP; add CloudFront CDN; plan Mumbai region at 10K users; daily DB backups with tested restore |

### C.3 Medium Risks (Address Post-MVP)

| # | Risk | Impact | Recommendation |
|---|---|---|---|
| R11 | **Feedback loop cold start** | Recommendations don't improve until sufficient outcome data | Use rule-based defaults for first 50 applications; show "learning" indicator; don't promise personalization until 10+ outcomes |
| R12 | **B2B schema drift** | Recruiter features require breaking migrations | Tables created in Sprint 0 but isolated in `b2b/` module; no shared FK constraints that would break job seeker queries |
| R13 | **Human-in-the-loop bypass** | Developer shortcut enables auto-submit | Enforce `approval_status` check in `submit` endpoint; add integration test that verifies 403 without approval; code review gate |
| R14 | **Embedding model version change** | Re-indexing all resumes on model upgrade | Store `model_version` on every embedding; support dual-index during migration; batch re-embedding via worker queue |
| R15 | **GDPR right-to-deletion complexity** | User data in audit logs, embeddings, analytics | Design deletion cascade: user → profiles → versions → embeddings → audit (anonymize, not delete) → analytics (delete) |

### C.4 Pre-Development Checklist

Before writing application code in Sprint 0, confirm:

- [ ] Initial Alembic migration includes all tables from Section 7 (including B2B and audit)
- [ ] `resume_profiles` + `resume_versions` pattern approved (no flat `resumes` table)
- [ ] Gemini API key provisioned with billing alerts at $50, $200, $500
- [ ] S3-compatible storage configured for resume files
- [ ] Redis instance provisioned for cache + job queue
- [ ] Environment variable schema documented in `.env.example`
- [ ] CI pipeline runs lint + test (even if tests are minimal initially)
- [ ] Error code enum defined and shared between backend and frontend
- [ ] Plan tier enum and feature gate middleware designed
- [ ] Agent audit logging utility function spec'd (used by all agents)
- [ ] Human-in-the-loop approval state machine documented (Section 18.3)
- [ ] OpenAPI spec generation configured in FastAPI from day 1

### C.5 Architecture Decision Records (ADRs) to Write

| ADR | Decision | Status |
|---|---|---|
| ADR-001 | Immutable resume versioning over mutable documents | Approved |
| ADR-002 | FAISS (MVP) → pgvector (10K) → Qdrant (100K) vector search evolution | Approved |
| ADR-003 | Gemini Flash for scoring, Pro for generation | Approved |
| ADR-004 | Human-in-the-loop mandatory for all application submissions | Approved |
| ADR-005 | Nightly analytics aggregation over real-time computation | Approved |
| ADR-006 | Rule-based feedback loop (Phase 2) before ML re-ranking (Phase 4) | Approved |
| ADR-007 | B2B tables reserved in Sprint 0, activated Phase 4 | Approved |

---

*End of Document*
