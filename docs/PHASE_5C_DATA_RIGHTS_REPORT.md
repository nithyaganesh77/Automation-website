# DOCUMIND AI — PHASE 5C: CONSENT WITHDRAWAL AND DATA RIGHTS REPORT

**Execution Date**: 2026-11-03  
**Status**: IMPLEMENTED & TESTED SUCCESSFULLY  
**Architecture Role**: Senior Security & Privacy Engineer, AI Architect  
**Commit Reference**: `dfb0b86` (Working Tree Active)  

---

## 1. Executive Summary

In compliance with DPDP (Digital Personal Data Protection Act, India), GDPR data subject rights, and enterprise SaaS customer sovereignty mandates, **Phase 5C** introduces full self-serve consent withdrawal, tenant-level AI air-gap preferences, data portability export, right-to-be-forgotten deletion workflows, and retention policy controls to DocuMind AI.

All implementations strictly adhere to:
1. **Inviolability of Global Privacy Mode**: Global `DISABLE_EXTERNAL_AI=True` can never be overridden by tenant-level settings.
2. **Historical Integrity**: Consent withdrawal disables external AI processing for future documents without deleting historical accounting records.
3. **Strict Tenant Isolation**: Cross-tenant data access, export extraction, and deletion requests are physically bounded by tenant identifier checks.
4. **Zero-Leakage Air-Gap**: Tenant consent withdrawal triggers local deterministic extraction with 0 external AI tokens and $0.00 cost, verified via low-level socket interception.

---

## 2. Implemented Architecture & Data Model

### 2.1 Database Schema Additions (`backend/app/models/all_models.py`)

#### `OrganizationSetting` Enhancements:
- `tenant_disable_external_ai`: `Boolean`, default `False`. Tenant-specific toggle to force air-gapped deterministic processing.
- `consent_withdrawn`: `Boolean`, default `False`. Tracks explicit withdrawal of consent by tenant administrators.
- `consent_withdrawn_at`: `DateTime(timezone=True)`. Timestamp of withdrawal.
- `retention_policy_days`: `Integer`, default `365`. Configurable data retention period.
- `data_rights_contact_email`: `String(255)`. Designated privacy officer contact.

#### New Entity: `DataRightsRequest`:
```python
class DataRightsRequest(Base):
    __tablename__ = "data_rights_requests"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    request_type = Column(String(50), nullable=False, index=True) # CONSENT_WITHDRAWAL, CONSENT_GRANTED, DATA_EXPORT, DATA_DELETION, RETENTION_UPDATE
    status = Column(String(50), default="PENDING", nullable=False, index=True) # PENDING, PROCESSING, COMPLETED, REJECTED
    details = Column(JSON, default=dict, nullable=False)
    requested_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    processed_by = Column(String(36), nullable=True)
    notes = Column(Text, nullable=True)
```

### 2.2 Inviolability Hierarchy Formula
```text
effective_external_ai_disabled = settings.DISABLE_EXTERNAL_AI or org_setting.tenant_disable_external_ai or org_setting.consent_withdrawn
```
If the host administrator sets `DISABLE_EXTERNAL_AI=True`, external AI is permanently suppressed. A tenant cannot opt into external AI if the global setting is disabled.

---

## 3. API Endpoints (`backend/app/api/v1/compliance.py`)

| Method | Endpoint | RBAC Required | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/compliance/consent/withdraw` | `Admin`, `Super Admin`, `Organization Owner` | Withdraws consent for cloud AI processing; future uploads run deterministically. Documents preserved. |
| `POST` | `/api/v1/compliance/consent/grant` | `Admin`, `Super Admin`, `Organization Owner` | Re-grants consent (subject to global host policy). |
| `GET` | `/api/v1/compliance/consent/status` | Authenticated User | Inspects tenant consent and external AI processing status. |
| `GET` | `/api/v1/compliance/preferences` | Authenticated User | Retrieves tenant privacy preferences and effective AI status. |
| `PATCH` | `/api/v1/compliance/preferences` | `Admin`, `Super Admin`, `Organization Owner` | Updates tenant privacy toggles and privacy contact email. |
| `POST` | `/api/v1/compliance/export` | Authenticated User | Generates tenant-isolated JSON bundle containing invoices, line items, documents, suppliers, and audit trails. |
| `POST` | `/api/v1/compliance/deletion-request` | `Admin`, `Super Admin`, `Organization Owner` | Initiates deletion request. Requires confirmation phrase `"DELETE ALL TENANT DATA"`. |
| `POST` | `/api/v1/compliance/deletion-request/{id}/execute` | `Admin`, `Super Admin`, `Organization Owner` | Purges tenant documents, invoices, line items, and suppliers. Logs final cryptographic audit entry. |
| `GET` | `/api/v1/compliance/retention-policy` | Authenticated User | Returns organization retention period (default: 365 days) and policy explanation. |
| `PATCH` | `/api/v1/compliance/retention-policy` | `Admin`, `Super Admin`, `Organization Owner` | Configures retention period between 30 and 3650 days. |
| `GET` | `/api/v1/compliance/requests` | Authenticated User | Lists all data rights requests submitted by tenant. |

---

## 4. Empirical Test Verification

Tests implemented in [`backend/tests/test_compliance_data_rights.py`](file:///d:/git/automation/backend/tests/test_compliance_data_rights.py):

| Test Case | Verification Criteria | Status |
| :--- | :--- | :--- |
| `test_consent_withdrawal_and_re_grant` | Verifies withdrawal status updates, creates `DataRightsRequest`, logs `CUSTOMER_CONSENT_WITHDRAWN` audit event with `historical_documents_preserved: True`, and allows subsequent re-granting. | **PASSED** |
| `test_prevention_of_external_ai_after_consent_withdrawal` | Monkeypatches `socket.socket.connect` to assert zero outbound network calls. Ingests document under withdrawn tenant; verifies pipeline completes locally with `extracted_tokens == 0` and `estimated_cost_usd == 0.0`. | **PASSED** |
| `test_global_privacy_mode_cannot_be_bypassed_by_tenant` | Sets global `DISABLE_EXTERNAL_AI = True`; tenant attempts `tenant_disable_external_ai = False`. Verifies `effective_external_ai_disabled` remains `True`. | **PASSED** |
| `test_tenant_data_export_and_isolation` | Requests export for Tenant A; verifies Tenant A's invoices are returned and Tenant B's invoices are absent. | **PASSED** |
| `test_data_deletion_lifecycle_and_boundary` | Tests confirmation phrase validation (`400 Bad Request` on mismatch). Verifies Tenant B cannot execute Tenant A's deletion (`404 Not Found`). Executes deletion for Tenant A; verifies Tenant A's documents purged while Tenant B's documents remain intact. | **PASSED** |
| `test_retention_policy_management` | Verifies Viewer/Reviewer roles cannot modify retention (`403 Forbidden`). Enforces 30–3650 day bounds. Allows Admin updates. | **PASSED** |

### Test Suite Summary:
- **Phase 5C Tests**: 6 passed in 11.67s.
- **Full Backend Regression Suite**: 22 passed in 17.76s.

---

## 5. Status Categorization

- **Implemented**: Tenant privacy models, compliance API router, LangGraph node integration, audit logging, export engine, deletion engine, retention policy.
- **Tested Successfully**: All 6 compliance tests, 22/22 backend test suite.
- **Tested with Limitations**: None.
- **Blocked**: None.
- **Requires Manual Action**: Front-end settings UI toggle integration (covered in Phase 5J).

