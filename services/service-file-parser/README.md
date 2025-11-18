# Service: File Parser

This microservice acts as the Extraction Layer of the pipeline. It consumes raw job submissions, accesses the files from the shared Docker volume, and converts binary formats (PDF/DOCX) into clean, analyzable text for the AI service.

## Logic Flow (The "Router" Pattern)

This service implements a Partial Failure strategy. If a user uploads 5 files and 1 is corrupt, we do not fail the entire job.

**Consumer:** Listens to QUEUE_JOB_INTAKE.

**Validation:** Uses Pydantic to ensure the message contains valid file paths and Job IDs.

**Processing Loop:** Iterates through the file list:

- **PDFs:** Extracted using PyMuPDF (Fitz).
- **DOCX:** Extracted using python-docx.

**Split Routing:**

- ✅ **Success:** Aggregated into a batch and published to QUEUE_AI_ANALYSIS.
- ❌ **Failure:** Individual errors (e.g., corrupted file) are published immediately to QUEUE_RESULTS_STORAGE so the user sees the error, while the rest of the job continues to AI.

## Tech Stack

- **PDF Engine:** PyMuPDF
- **Word Engine:** python-docx
- **Validation:** Pydantic
- **Messaging:** Pika (RabbitMQ)
- **Validation:** Pydantic

## Input / Output Contracts

### Consumes (QUEUE_JOB_INTAKE)

Receives the job details and the paths to the files stored on the shared volume.

```json
{
  "job_id": "job_123",
  "correlation_id": "abc-xyz",
  "jd_text": "Looking for Python dev...",
  "use_delay": true,
  "expected_file_count": 2,
  "file_paths": [
    {
      "cv_id": "job_123_001",
      "file_path": "/shared_volume/uploads/resume1.pdf",
      "original_filename": "resume1.pdf"
    }
  ]
}
```

### Produces - Success Path (QUEUE_AI_ANALYSIS)

Sends a batch of clean text to the AI service.

```json
{
  "job_id": "job_123",
  "correlation_id": "abc-xyz",
  "jd_text": "Looking for Python dev...",
  "use_delay": true,
  "cvs": [
    {
      "cv_id": "job_123_001",
      "filename": "resume1.pdf",
      "original_filename": "resume1.pdf",
      "text": "Extracted raw text content..."
    }
  ]
}
```

### Produces - Error Path (QUEUE_RESULTS_STORAGE)

Sends individual failures directly to the DB service (skipping AI).

```json
{
  "job_id": "job_123",
  "correlation_id": "abc-xyz",
  "cv_id": "job_123_002",
  "original_filename": "corrupt.docx",
  "status": "error",
  "error": "File corrupted or unreadable"
}
```
