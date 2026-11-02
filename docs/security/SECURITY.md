# DocuMind AI — Security, Compliance & Governance

## 1. Multi-Tenant Data Isolation
Every data-access path in the DocuMind AI backend guarantees tenant isolation:
- Tenant membership is verified on every API call from the JWT claim and cross-checked against the database `organization_members` table.
- Query filters explicitly enforce `organization_id == auth_ctx.organization_id`.
- Tenant boundary penetration tests are automated in `backend/tests/test_tenant_isolation.py`.

## 2. Authentication & Secrets
- Passwords are encrypted with `bcrypt` using 12 salt rounds.
- Tokens follow the JSON Web Token (JWT) standard with `HS256` HMAC signing.
- Short-lived access tokens (expire in 24 hours) with longer-lived refresh tokens.
- No production secrets or external API keys are hard-coded into the repository. All keys are injected through environment variables or secure settings.

## 3. Defense Against Prompt Injection
- Document contents extracted by OCR and document parsers are strictly treated as **untrusted data payloads**.
- LLM prompt templates wrap extracted document text in isolated user data delimiters (`Document Text:\n{text}`).
- System instructions strictly prohibit the LLM from taking tool execution instructions or executing code contained within the invoice text.

## 4. File Validation & Execution Safety
- Files are validated against allowed MIME types and file extensions (`pdf`, `png`, `jpg`, `jpeg`, `docx`, `xlsx`).
- Upload sizes are strictly limited to 25MB.
- File paths are generated using UUID prefixes to prevent directory traversal attacks (`../`).
- Uploaded files are never executed as binaries or shell scripts.

## 5. Immutable Audit Logging
- Every administrative action, document upload, status modification, and reviewer decision creates an immutable audit record in `audit_logs` storing:
  - Organization ID
  - User ID / Actor
  - Action code
  - Entity type & ID
  - IP Address
  - JSON payload details & diffs
