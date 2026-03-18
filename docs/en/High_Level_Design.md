# 🐱 nekkoflix — High-Level Design

| Item | Content |
|------|------|
| Document version | v1.1 |
| Date created | 2026-03-19 |
| Status | Draft |
| Corresponding requirements document | `docs/ja/requirements_v1.md` |

---

## Table of Contents

1. System Architecture
2. Component Design
3. Processing Flow
4. API Design
5. Screen Design
6. Logical Data Design
7. Infrastructure Design
8. Security Design
9. Error Design
10. CI/CD Design
11. Non-functional Requirements in Concrete Form
12. TBD

---

## 1. System Architecture

The system is composed of:

- Browser frontend with Next.js / React on Cloud Run
- Cloud API Gateway for JWT validation, rate limiting, and routing
- Backend API with FastAPI on Cloud Run
- Vertex AI Custom Endpoint integrating four cat-analysis models and a LightGBM Ranker
- Gemini on Vertex AI for prompt rewriting
- Veo3.1-fast for video generation
- Cloud Firestore for persistence
- Cloud Storage for temporary generated-video storage

### Design policy summary

| Policy | Content |
|---|---|
| Fully synchronous processing | `POST /generate` keeps the HTTP connection until a video URL is returned |
| Cloud API Gateway | Separate authentication and rate limiting from the backend |
| Temporary use of GCS | Veo writes to GCS internally; the backend returns a signed URL |
| Direct VPC | Communication from the backend to internal Google services remains inside the VPC |
| In-process UCB Bandit | Minimize latency by handling exploration logic inside the backend |
| Integrated LightGBM Ranker | Keep ranking inference inside the same Vertex AI endpoint as the cat models |

---

## 2. Component Design

### 2.1 Frontend

Responsibilities:

- screen rendering and routing
- microphone, camera, file-upload, and context-input handling
- sending HTTP requests with ID tokens
- loading and progress display
- video playback through a signed URL
- feedback submission

### 2.2 Cloud API Gateway

Responsibilities:

- JWT validation
- rate limiting
- routing to backend endpoints
- OpenAPI-based API management

### 2.3 Backend API

Responsibilities:

- session management
- calling the Vertex AI cat-model endpoint
- generating the state key
- selecting a template through UCB Bandit logic
- requesting prompt rewriting from Gemini
- requesting video generation from Veo3
- issuing a signed URL for the generated video
- receiving feedback and updating reward data

### 2.4 Vertex AI cat-model endpoint + LightGBM Ranker

Integrated models:

- `IsolaHGVIS/Cat-Meow-Classification`
- `semihdervis/cat-emotion-classifier`
- `usyd-community/vitpose-plus-plus-small`
- `openai/clip-vit-base-patch32`
- trained LightGBM Ranker

The endpoint outputs both extracted features and ranking scores for the 11 templates in one request.

### 2.5 Bandit

The LightGBM Ranker handles exploitation by predicting scores. The UCB Bandit layer adds an exploration bonus and determines the final selected template.

### 2.6 Gemini

Gemini receives:

- selected template prompt
- current state key
- user context set by the owner

and rewrites them into a final Veo prompt.

### 2.7 Veo3

Veo3 generates the final mp4 video, stores it in GCS, and the backend returns a signed URL to the frontend.

---

## 3. Processing Flow

### 3.1 `POST /generate`

1. Frontend sends input data to API Gateway.
2. Backend creates a session and stores `status=generating`.
3. Backend requests inference from Vertex AI.
4. Backend generates the state key.
5. UCB adds an exploration bonus to ranker scores and selects a template.
6. Gemini rewrites the prompt.
7. Veo3 generates a video and returns a GCS object URI.
8. Backend issues a signed URL.
9. Backend updates the session to `status=done`.
10. Frontend receives `video_url`, `session_id`, `state_key`, and `template_id`.

### 3.2 `POST /feedback`

1. Frontend sends `session_id` and `reaction`.
2. Backend converts the reaction into a numeric reward.
3. Firestore stores the feedback.
4. The Bandit table updates cumulative reward, selection count, and mean reward.

### 3.3 Experience Mode fallback

If microphone or camera input fails in Experience Mode, the UI automatically switches from real-time input to prepared sample input and notifies the user.

---

## 4. API Design

### Endpoints

| Method | Path | Summary | Auth |
|---|---|---|---|
| `GET` | `/health` | Health check | None |
| `POST` | `/generate` | Main generation flow | ID token required |
| `POST` | `/feedback` | Feedback recording and Bandit update | ID token required |

### Main request and response fields

- `/generate` accepts `mode`, `image_base64`, `audio_base64`, and `user_context`
- `/generate` returns `session_id`, `video_url`, `state_key`, `template_id`, and `template_name`
- `/feedback` accepts `session_id` and `reaction`
- `/feedback` returns `reward` and `updated_template_id`
- `/health` returns `status=ok` and a timestamp

---

## 5. Screen Design

Main screens:

- top screen for mode selection
- Experience Mode input screen
- Production Mode input screen
- loading/result screen
- playback and feedback screen
- error screen

The output screen displays:

- the generated state key
- selected template
- generation progress
- playback UI
- three-choice feedback buttons

---

## 6. Logical Data Design

Main Firestore collections:

- `sessions`
- `bandit_table`
- `templates`
- `feedbacks`

Each session stores the current status, selected template, state key, user context, timestamps, and result metadata.

The Bandit table stores cumulative reward, selection count, and derived mean reward for each template.

---

## 7. Infrastructure Design

Planned GCP resources include:

- Cloud Run for frontend and backend
- Cloud API Gateway
- Vertex AI endpoint
- Firestore
- Cloud Storage
- Artifact Registry
- VPC and Serverless VPC Access

Environment variables include project and region settings, endpoint IDs, Gemini and Veo model names, bucket names, signed-URL expiration, and environment name.

Generated videos are stored in GCS temporarily and deleted automatically according to lifecycle policy.

---

## 8. Security Design

- Authentication is handled with Google ID tokens and API Gateway validation.
- Secrets are managed only on the backend.
- Uploaded files are processed server-side and removed after use.

---

## 9. Error Design

Representative error categories include:

- invalid input
- Vertex AI timeout
- Veo generation failure
- internal server error

Timeouts are explicitly designed for Vertex AI, Gemini, Veo polling, and storage access. Experience Mode includes fallback behavior for input failures.

---

## 10. CI/CD Design

Cloud Build is used for:

- frontend container build and deployment
- backend container build and deployment
- model container build and manual endpoint deployment

Terraform manages the infrastructure layer separately.

---

## 11. Non-functional Requirements in Concrete Form

### Performance

- keep cat-state analysis responsive
- tolerate Veo generation latency with explicit loading UI
- reduce backend round trips through endpoint integration

### Availability

- avoid cold starts for critical services
- keep demo operation stable during the hackathon

### Extensibility

- allow replacement of cat models
- allow future replacement of the Bandit algorithm
- allow library growth through Firestore-managed templates

---

## 12. TBD

- exact state-key generation logic
- final reward mapping
- final exploration parameter values
- final deployment sizing and scaling thresholds
- details of mobile support and presentation polish
