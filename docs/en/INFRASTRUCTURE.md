# 🐱 nekkoflix — Infrastructure Detailed Design

| Item | Content |
|------|------|
| Document version | v1.0 |
| Date created | 2026-03-19 |
| Status | Draft |
| Corresponding high-level design | `docs/ja/BasicDesign.md v1.1` |

---

## Table of Contents

1. Architecture Overview
2. Terraform Design
3. GCP Resource Details
4. Network Details
5. IAM and Security
6. CI/CD Pipeline
7. Required Files
8. Operations
9. Cost Estimate
10. TBD

---

## 1. Architecture Overview

The infrastructure consists of:

- browser clients
- frontend on Cloud Run
- Cloud API Gateway
- backend on Cloud Run
- Vertex AI custom endpoint for cat models and the LightGBM Ranker
- Gemini and Veo3 on Vertex AI
- Cloud Firestore
- Cloud Storage

The main request flow is:

1. Browser sends generation requests through the frontend and API Gateway.
2. Backend persists a generating session record.
3. Vertex AI endpoint returns features and ranker scores.
4. Backend performs UCB-based template selection.
5. Gemini rewrites the prompt.
6. Veo3 generates the video and writes it to GCS.
7. Backend issues a signed URL and updates the session state.

Feedback requests update Firestore with both feedback events and Bandit statistics.

---

## 2. Terraform Design

### Directory and module structure

Terraform is organized by:

- `environments/dev`
- `environments/prod`
- reusable modules for Cloud Run, API Gateway, Vertex AI, Firestore, GCS, IAM, Artifact Registry, and VPC

### State management

- Terraform state is stored in a dedicated GCS bucket such as `nekkoflix-tfstate`
- versioning is enabled for rollback
- public access is disabled
- encryption uses Google-managed keys

The state bucket is created manually once to avoid the bootstrap problem.

### Variables and environment separation

Environment-specific variables define:

- project ID
- region
- environment name
- backend and frontend image URIs
- Vertex endpoint ID
- Gemini and Veo model names
- GCS video bucket name

### Root modules

The environment root module wires together:

- VPC
- Artifact Registry
- GCS
- Firestore
- IAM
- backend Cloud Run
- frontend Cloud Run
- API Gateway

### Execution procedure

Typical flow:

1. create the state bucket once
2. run `terraform init`
3. run `terraform plan`
4. run `terraform apply`
5. optionally target specific modules
6. run `terraform destroy` after the demo if needed

---

## 3. GCP Resource Details

### Cloud Run: Frontend

- serves the Next.js frontend
- can allow public ingress
- scales between `min=0` and a small upper bound

### Cloud Run: Backend

- serves the FastAPI backend
- uses internal-only ingress
- uses Direct VPC egress
- keeps `min-instances=1` to reduce cold starts
- uses a longer timeout for Veo-related processing

### Cloud API Gateway

- validates JWTs
- applies rate limits
- routes requests based on an OpenAPI definition

### Vertex AI Endpoint

- deploys the integrated cat-analysis stack and LightGBM Ranker
- uses a custom prediction routine or custom container
- starts on CPU and can move to GPU if latency requires it

### Cloud Firestore

Collections include:

- `sessions`
- `bandit_table`
- `templates`
- `feedbacks`

### Cloud Storage

- stores generated videos temporarily
- applies lifecycle deletion, such as deleting objects after one day

### Artifact Registry

- stores container images for frontend, backend, and model services

---

## 4. Network Details

### VPC and subnet design

- use a dedicated VPC for internal communication
- provide a Serverless VPC Access connector for Cloud Run

### Direct VPC Egress

- backend traffic to internal Google services is routed through the VPC

### Firewall rules

- allow required egress from Cloud Run to internal GCP services
- deny unnecessary ingress by default

### Private Google Access

- enable access to Google APIs from private workloads where needed

---

## 5. IAM and Security

### Service accounts

Separate service accounts are assumed for:

- frontend
- API Gateway
- backend
- Cloud Build

### IAM bindings

Grant least-privilege access for:

- API Gateway -> backend invocation
- backend -> Vertex AI
- backend -> Firestore
- backend -> GCS
- Cloud Build -> Artifact Registry
- Cloud Build -> Cloud Run deployment

### Secret management

Use Secret Manager or backend-only environment variables for secrets. Do not expose them to the frontend.

---

## 6. CI/CD Pipeline

Cloud Build pipelines are prepared for:

- backend image build and deployment
- frontend image build and deployment
- model image build and endpoint deployment

Dockerfiles are maintained separately for backend, frontend, and model services.

---

## 7. Required Files

The infrastructure-related files include:

- Terraform modules and environment files
- OpenAPI definitions
- Cloud Build YAML files
- helper scripts for backend initialization, Firestore initialization, and model deployment
- `.env.example`, Python config, and Node config files

---

## 8. Operations

### Logging

- backend logs are structured
- request IDs and session IDs should be traceable
- important generation and feedback events should be logged

### Monitoring

- monitor Cloud Run health
- monitor Vertex AI failures and latency
- monitor Firestore access errors
- monitor Veo generation completion time

---

## 9. Cost Estimate

### Hackathon day

The main cost drivers are:

- Cloud Run usage
- Vertex AI endpoint uptime
- Gemini usage
- Veo generation
- storage and Firestore access

### Development period

Ongoing cost is dominated by:

- keeping model endpoints available
- repeated generation tests
- storage and database usage

---

## 10. TBD

- final instance sizing
- final cost cap
- final firewall and private-access settings
- final production and demo environment split
- final model deployment automation level
