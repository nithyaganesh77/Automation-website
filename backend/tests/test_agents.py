import os
from app.agents.graph import execute_document_workflow
from app.agents.state import DocuMindState
from app.models.all_models import Document


def test_agent_monitoring_endpoint(client, test_org_and_admin):
    headers = {"Authorization": f"Bearer {test_org_and_admin['token']}"}
    response = client.get("/api/v1/agents", headers=headers)
    assert response.status_code == 200
    agents = response.json()
    assert len(agents) == 9
    agent_names = [a["name"] for a in agents]
    assert "Document Intake Agent" in agent_names
    assert "Validation Agent" in agent_names
    assert "Decision Agent" in agent_names


def test_dashboard_metrics_endpoint(client, test_org_and_admin):
    headers = {"Authorization": f"Bearer {test_org_and_admin['token']}"}
    response = client.get("/api/v1/reports/dashboard", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_documents" in data
    assert "total_invoice_value" in data
    assert "monthly_expense_trend" in data
