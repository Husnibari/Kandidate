# Kandidate

> **The Open Source, Self-Hosted AI Applicant Tracking System.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/Status-Core%20Engine%20Alpha-blue)](https://github.com/AlShabiliBadia/Kandidate)

## The Vision

Hiring tools are expensive and often invade candidate privacy. **Kandidate** is an open-source alternative designed for startups and privacy-conscious recruiters who want full control over their data.

**The Goal:** A system that is accessible to everyone.

- **Self-Hosted:** You own the data and the infrastructure.
- **Cost-Efficient:** Designed to run on minimal resources (Free Tier VPS compatible) using Google Gemini's free tier for analysis.
- **Modular:** Built on a scalable event-driven architecture.

---

## Architecture

Kandidate is not a monolithic script. It is a distributed system designed for reliability and scale.

<div align="center">
  <img src="./docs/images/architecture_diagram.svg" alt="Kandidate Architecture Diagram" width="100%">
</div>

### The Core Engine

The backend is composed of four decoupled microservices communicating via **RabbitMQ**:

| Service                                | Tech Stack          | Role                                                                                                                   |
| :------------------------------------- | :------------------ | :--------------------------------------------------------------------------------------------------------------------- |
| **[Gateway](./services/gateway)**      | FastAPI, Docker Vol | **The Orchestrator.** Handles validation and implements "Fire-and-Forget" ingestion to keep the API responsive.        |
| **[Parser](./services/parser)**        | PyMuPDF             | **The Extractor.** Converts binary files (PDF/DOCX) into raw text and routes them based on success/failure.            |
| **[Analyzer](./services/ai-analyzer)** | Gemini, Instructor  | **The Brain.** Performs semantic analysis. Enforces rate limits to ensure Free Tier compatibility.                     |
| **[Results](./services/results-db)**   | Mongo, Postgres     | **The Vault.** Manages data persistence, syncing unstructured data from MongoDB (ingestion) to PostgreSQL (analytics). |

---

## Key Engineering Decisions

To ensure this tool remains efficient and free to host, specific architectural patterns were implemented:

1.  **Resource-Optimized Hybrid Services:**
    The Results Service combines the API Server and Queue Worker into a single process using threading. This cuts RAM usage in half compared to running separate containers.

2.  **Structured AI:**
    Large Language Models are chaotic. Kandidate uses the **Instructor** library to force Gemini to output strict, validated Pydantic schemas. No hallucinations, just queryable data.

3.  **Backpressure Management:**
    The AI service enforces a 5-second delay and uses `prefetch_count=1` on RabbitMQ. This ensures the system never hits external API rate limits, regardless of load.

---

## Frontend & UI Development

**We are looking for a Frontend Lead.**

If you are a Frontend or UI/UX developer interested in designing the interface for this engine, please check the dedicated repository:

👉 **[Kandidate-frontend](https://github.com/AlShabiliBadia/Kandidate-frontend)**

---

## Quick Start (Backend Engine)

You can spin up the core backend locally using Docker Compose.

### Prerequisites

- Docker & Docker Compose
- Google Gemini API Key (Free Tier available)

### Setup

1.  Clone the repository:

    ```bash
    git clone https://github.com/AlShabiliBadia/Kandidate.git
    cd kandidate
    ```

2.  Configure the environment:

    ```bash
    cp .env.example .env
    # Add your GEMINI_API_KEY in the .env file
    ```

3.  Start the services:

    ```bash
    docker compose up -d --build
    ```

4.  Interact:
    - **API Docs:** `http://localhost:8000/docs`
    - **RabbitMQ:** `http://localhost:15672`

---

## Roadmap

- [x] Core Microservices Architecture (Gateway, Parser, Analyzer, Results)
- [x] Event-Driven Pipeline (RabbitMQ)
- [x] AI Analysis Integration (Gemini + Instructor)
- [ ] **Candidate Management (Edit, Label, Vote)**
- [ ] **Collaboration Suite (Email, Calendar, Team Sync)**
- [ ] **Web Dashboard (Frontend)**

---

## Author

**Architected by Badiea Al-Shabili.**

[Link To Linkedin](https://www.linkedin.com/in/badia-alshabili/)
