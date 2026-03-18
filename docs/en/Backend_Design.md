# 🐱 nekkoflix — Backend Detailed Design

| Item | Content |
|------|------|
| Document version | v1.1 |
| Date created | 2026-03-19 |
| Status | Draft |
| Corresponding high-level design | `docs/ja/BasicDesign.md v1.1` |
| Reference implementation document | `docs/ja/IMPLEMENTATION.md` |

---

## Table of Contents

1. Directory and File Structure
2. Main File Responsibilities
3. Architecture Visualization
4. Dependencies
5. Configuration Management
6. Application Entry Point
7. Schema Definitions
8. Router Design
9. Service-Layer Design
10. Exception and Error Handling
11. Logging
12. Class Diagram and Dependencies
13. Sequence Diagram
14. Session State Transition
15. Asynchronous Design Policy
16. Dependency Injection Pattern
17. Development Environment Setup
18. Coding Conventions
19. Test Design
20. TBD

---

## 1. Directory and File Structure

The backend is organized around:

- `app.py`, `config.py`, `exceptions.py`, `logging_config.py`
- `models/` for request, response, internal, and Firestore schemas
- `routers/` for `generate`, `feedback`, and `health`
- `services/` for cat-model access, Bandit logic, state-key generation, Gemini, Veo, Firestore, and orchestration
- `tests/` for unit and integration tests

The design policy is a thin router layer and a thick service layer.

---

## 2. Main File Responsibilities

Representative responsibilities:

- `src/app.py`: create FastAPI app, register middleware, routers, and exception handlers
- `src/config.py`: type-safe settings loading via `pydantic-settings`
- `src/exceptions.py`: custom error hierarchy
- `src/models/*`: request, response, internal, and Firestore schemas
- `src/routers/generate.py`: validate input and delegate to orchestrator
- `src/routers/feedback.py`: convert reactions to rewards and trigger Bandit updates
- `src/services/orchestrator.py`: coordinate the full `/generate` flow
- `src/services/cat_model/client.py`: call Vertex AI endpoint
- `src/services/bandit/*`: select and update templates
- `src/services/state_key/builder.py`: convert model outputs into a state key
- `src/services/gemini/*`: build prompts and call Gemini
- `src/services/veo/*`: request generation, poll long-running operations, and issue signed URLs
- `src/services/firestore/client.py`: generic Firestore CRUD wrapper

---

## 3. Architecture Visualization

The dependency direction is:

- FastAPI app -> routers
- routers -> orchestrator or focused services
- orchestrator -> cat model, state-key builder, Bandit, Gemini, Veo, Firestore
- Bandit repository -> Firestore client
- Gemini prompt builder and state-key builder remain pure and side-effect free where possible

The external dependencies are:

- Vertex AI custom endpoint
- Gemini
- Veo3
- Firestore
- GCS

---

## 4. Dependencies

Main Python dependencies:

- `fastapi`
- `uvicorn`
- `pydantic-settings`
- `google-cloud-aiplatform`
- `google-cloud-firestore`
- `google-cloud-storage`
- `structlog`
- `httpx`

Development dependencies:

- `pytest`
- `pytest-asyncio`
- `pytest-cov`
- `pytest-mock`
- `mypy`
- `ruff`
- `pre-commit`

The project assumes Python 3.11 with strict typing and linting.

---

## 5. Configuration Management

All environment variables are managed centrally in `config.py`.

Typical settings include:

- GCP project and region
- Vertex endpoint ID and timeout
- Gemini model and timeout
- Veo model, timeout, and polling interval
- GCS bucket name and signed URL expiration
- Firestore database ID
- Bandit exploration parameter
- environment and log level

The settings object is cached as a singleton.

---

## 6. Application Entry Point

`app.py` is responsible for:

- creating the FastAPI application
- registering middleware
- registering routers
- installing exception handlers
- initializing logging

The application follows an app-factory style.

---

## 7. Schema Definitions

Schema groups:

- request schemas for `/generate` and `/feedback`
- response schemas for generation, feedback, and health
- internal dataclasses such as `CatFeatures`, `BanditSelection`, and `GenerationContext`
- Firestore document schemas for persisted collections

The API layer uses Pydantic, while internal flow may use lighter dataclasses.

---

## 8. Router Design

### `generate.py`

- validates request input
- calls the orchestrator
- returns a structured generation response

### `feedback.py`

- accepts `session_id` and `reaction`
- converts reaction to numeric reward
- records feedback and updates the Bandit table

### `health.py`

- provides a lightweight health endpoint for Cloud Run

---

## 9. Service-Layer Design

### Orchestrator

Coordinates the end-to-end `/generate` flow:

1. create session
2. store initial Firestore record
3. call the cat-model endpoint
4. build the state key
5. select a template via Bandit logic
6. rewrite the prompt with Gemini
7. generate a video with Veo3
8. issue a signed URL
9. update final session state

### Cat-model client

- sends base64 image and audio to Vertex AI
- parses the returned structured prediction

### Bandit layer

- `base.py` defines the abstraction
- `ucb.py` implements UCB1-based selection and update logic
- `repository.py` isolates Firestore access to `bandit_table` and `templates`

### State-key builder

Produces a deterministic state-key string from model outputs such as emotion labels, meow labels, attentive score, and pose-derived signals.

### Gemini layer

- `prompt_builder.py` assembles the final instruction to Gemini
- `client.py` handles request, timeout, and error wrapping

### Veo layer

- `client.py` submits generation requests and polls the long-running operation
- `signed_url.py` issues time-limited GCS URLs

### Firestore client

Provides generic CRUD operations for:

- `sessions`
- `bandit_table`
- `templates`
- `feedbacks`

---

## 10. Exception and Error Handling

The backend defines an application-specific exception hierarchy.

Representative categories include:

- input validation errors
- Vertex AI communication failures
- Gemini failures
- Veo generation failures
- Firestore access errors
- unexpected internal errors

Each error is mapped to an HTTP status code and a stable error code.

---

## 11. Logging

Structured logging is handled with `structlog`.

Logs should include:

- session ID
- endpoint name
- selected template ID
- state key
- elapsed time for major external calls
- error code and message when failures occur

---

## 12. Class Diagram and Dependencies

The key rule is dependency direction:

- routers depend on services
- services depend on interfaces or infrastructure clients
- repositories isolate database access
- pure transformation logic is separated from I/O

This keeps the orchestration flow testable and allows algorithm replacement without large interface changes.

---

## 13. Sequence Diagram

The detailed request sequence matches the high-level flow:

frontend -> router -> orchestrator -> Firestore -> Vertex AI -> Bandit -> Gemini -> Veo -> GCS -> response

The feedback sequence is:

frontend -> router -> reward conversion -> Firestore feedback write -> Bandit table update -> response

---

## 14. Session State Transition

Typical session states:

- `generating`
- `done`
- `failed`

The backend records state transitions in Firestore so the frontend and operators can inspect generation progress and failures.

---

## 15. Asynchronous Design Policy

- use async where external I/O benefits from concurrency
- keep pure logic synchronous
- use explicit polling intervals for Veo long-running operations
- tune worker and timeout settings for Cloud Run

The design separates CPU-light orchestration from network-bound external service calls.

---

## 16. Dependency Injection Pattern

The orchestrator receives dependencies through its constructor so tests can replace:

- Vertex AI client
- Bandit implementation
- Gemini client
- Veo client
- Firestore client

This supports isolated unit testing and easier future refactoring.

---

## 17. Development Environment Setup

Typical local setup includes:

1. install `uv`
2. install dependencies
3. configure pre-commit
4. fill in `.env`
5. run the backend locally or through `docker-compose`

---

## 18. Coding Conventions

The backend follows the implementation guide, including:

- strict typing
- clear naming
- separation between routing and business logic
- constants in uppercase
- explicit error handling
- linting and formatting via Ruff and typing checks via mypy

---

## 19. Test Design

### Test targets

- state-key generation
- UCB logic
- prompt building
- reward conversion
- Firestore wrapper behavior
- orchestrator integration with mocked external services

### Test policy

- unit tests for pure logic
- integration tests with mocked cloud services
- shared fixtures in `conftest.py`

---

## 20. TBD

- final state-key thresholds
- final reward mapping values
- final Firestore schema details
- exact retry policies for external services
- final production-grade observability settings
