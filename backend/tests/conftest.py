import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.session import Base, get_db
from app.main import app
import uuid
from app.models.all_models import Organization, User, OrganizationMember, OrganizationSetting
from app.core.security import hash_password, create_access_token

TEST_DATABASE_URL = "sqlite:///./test_documind.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_org_and_admin(db_session):
    unique_suffix = uuid.uuid4().hex[:6]
    org = Organization(name=f"Test Corp {unique_suffix}", slug=f"test-corp-{unique_suffix}")
    db_session.add(org)
    db_session.flush()

    user = User(
        email=f"admin_{unique_suffix}@testcorp.com",
        hashed_password=hash_password("Secret123!"),
        full_name="Test Admin",
        is_active=True,
        is_superuser=True
    )
    db_session.add(user)
    db_session.flush()

    member = OrganizationMember(organization_id=org.id, user_id=user.id, role="Admin")
    db_session.add(member)

    setting = OrganizationSetting(organization_id=org.id, currency="INR")
    db_session.add(setting)

    db_session.commit()

    token = create_access_token(user.id, org.id, "Admin")
    return {"org": org, "user": user, "token": token}
