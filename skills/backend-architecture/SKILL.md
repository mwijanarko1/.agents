---
name: backend-architecture
description: Backend design patterns, API design, database schemas, auth, and observability.
---

# Backend & Architecture

## Architecture Guidelines

### Component Design
- **Server-First Strategy:** Default to React Server Components (RSC) for data fetching. Use Client Components (`'use client'`) only for interactivity or browser APIs.
- **Composition over Inheritance:** Use `children` prop and slots to avoid deep prop drilling and "God Components."
- **Presentational vs. Container:**
  - *Presentational:* Stateless, UI-only, receives data via props.
  - *Container:* Manages state, fetches data, passes to Presentational.
- **Strict Interfaces:** Define TypeScript interfaces for all props. Export interfaces from the component file.
- **Headless UI:** Decouple logic from rendering. Use hooks for complex behavior (e.g., `useToggle`, `useForm`) to keep JSX clean.
- **Error Boundaries:** Wrap feature roots in Error Boundaries to prevent full app crashes.

### Data Flow
- **Unidirectional:** Data flows down (Props), events flow up (Callbacks).
- **Source of Truth Hierarchy:**
  1. **URL State:** (Search params, dynamic routes) for shareable state.
  2. **Server State:** (React Query/SWR) for async data.
  3. **Local State:** (`useState`/`useReducer`) for UI interaction.
  4. **Global State:** (Zustand/Context) ONLY for app-wide settings (theme, user session). Avoid using Redux/Context for caching server data.
- **Boundary Validation:** Validate all external data entering the system (API responses, URL params) using Zod schemas immediately at the entry point.

### API Design (RESTful)
- **Resource Oriented:** URLs represent resources (nouns), methods represent actions (verbs).
  - `GET /users` (List), `POST /users` (Create), `GET /users/:id` (Detail).
- **Service Layer Pattern:** API Routes (`route.ts`) must not contain business logic. They should validate input, call a Service/Controller function, and return a standardized response.
- **Type Safety (End-to-End):**
  - Share Types/DTOs between Client and Server.
  - Enforce Zod validation on Request Bodies and Query Params.
- **Standardized Responses:**
  - Success: `{ data: T, meta?: Meta }`
  - Error: `{ code: string, message: string, errors?: ValidationErrors }`
- **Status Codes:** Use correct semantic codes (200 OK, 201 Created, 400 Bad Request, 401 Unauth, 403 Forbidden, 422 Validation Error, 500 Server Error).

## Backend Development Guidelines

### Database Schema (Relational/SQL)
- **Naming Conventions:**
  - Tables: Plural, `snake_case` (e.g., `users`, `order_items`).
  - Columns: `snake_case` (e.g., `first_name`, `is_active`).
- **Primary Keys:** Use `UUID` (v4) or `CUID2` for ID fields to prevent enumeration attacks and assist migration. Avoid auto-incrementing integers.
- **Timestamps:** Every table must have `created_at` (default now) and `updated_at` (auto-update).
- **Integrity:** Enforce Foreign Key constraints. Define explicit `ON DELETE` behaviors (CASCADE, SET NULL, or RESTRICT).
- **Indexing:**
  - Index all Foreign Keys.
  - Index columns frequently used in `WHERE`, `ORDER BY`, or `JOIN` clauses.
  - Use composite indexes for frequent multi-column queries.
- **Null Safety:** Default to `NOT NULL` unless optionality is strictly required by domain logic.

### Authentication (Identity)
- **Delegation:** Do not roll custom crypto. Use established libraries (NextAuth/Auth.js) or managed services (Clerk, Supabase Auth).
- **Session Management:**
  - Use HttpOnly, Secure, SameSite cookies for session tokens.
  - Implement token rotation for long-lived sessions.
- **Passwords:** If handling credentials locally (discouraged), use `bcrypt` or `argon2` with adequate work factors. Never store plain text.

### Authorization (Access Control)
- **Layered Defense:**
  1. **Edge/Middleware:** Validate presence of session/token.
  2. **Application Layer:** Role-Based Access Control (RBAC) checks in service methods.
  3. **Data Layer:** Row Level Security (RLS) policies within the database engine itself.
- **Principle of Least Privilege:** Default to `deny-all` and explicitly grant permissions.
- **Multi-Tenancy:** Ensure every query includes a `tenant_id` or `user_id` filter clause to prevent data leakage between users.

### Error Handling
- **Centralized Handler:** Implementation of a global error interceptor to catch unhandled exceptions.
- **Classification:** Distinguish between `Operational Errors` (invalid input, network down - handle gracefully) and `Programmer Errors` (bugs - crash/alert).
- **Sanitization:** NEVER leak stack traces or raw database errors to the client in production. Map to generic, user-friendly messages.
- **Standardization:** Return standard error objects: `{ "error": "InternalCode", "message": "Human readable", "details": {} }`.

### Logging & Observability
- **Structured Logging:** Log as JSON, not plain text, to enable querying (e.g., `{ level: "error", userId: "123", message: "Failed payment" }`).
- **Levels:** Strictly use Log Levels (`DEBUG`, `INFO`, `WARN`, `ERROR`).
- **PII Redaction:** Automatically scrub sensitive fields (passwords, emails, credit cards) before writing logs.
- **Correlation:** Generate a `Request-ID` (Correlation ID) at the entry point and propagate it through all downstream function calls/logs for tracing.
