"""add_onboarding_and_subscription_models

Revision ID: d417279d3854
Revises: c706f8d0d5b0
Create Date: 2026-11-03 13:42:55.178902

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd417279d3854'
down_revision: Union[str, Sequence[str], None] = 'c706f8d0d5b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema incrementally from c706f8d0d5b0 with defensive checks."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # 1. Add onboarding columns to organizations
    if 'organizations' in existing_tables:
        org_cols = {c['name'] for c in inspector.get_columns('organizations')}
        with op.batch_alter_table('organizations', schema=None) as batch_op:
            if 'legal_name' not in org_cols:
                batch_op.add_column(sa.Column('legal_name', sa.String(length=255), nullable=True))
            if 'gstin' not in org_cols:
                batch_op.add_column(sa.Column('gstin', sa.String(length=15), nullable=True))
            if 'pan' not in org_cols:
                batch_op.add_column(sa.Column('pan', sa.String(length=10), nullable=True))
            if 'address' not in org_cols:
                batch_op.add_column(sa.Column('address', sa.Text(), nullable=True))
            if 'city' not in org_cols:
                batch_op.add_column(sa.Column('city', sa.String(length=100), nullable=True))
            if 'state' not in org_cols:
                batch_op.add_column(sa.Column('state', sa.String(length=100), nullable=True))
            if 'pincode' not in org_cols:
                batch_op.add_column(sa.Column('pincode', sa.String(length=10), nullable=True))
            if 'phone' not in org_cols:
                batch_op.add_column(sa.Column('phone', sa.String(length=20), nullable=True))
            if 'onboarding_completed' not in org_cols:
                batch_op.add_column(sa.Column('onboarding_completed', sa.Boolean(), server_default='0', nullable=False))
            if 'onboarding_step' not in org_cols:
                batch_op.add_column(sa.Column('onboarding_step', sa.String(length=50), server_default='NOT_STARTED', nullable=False))

    # 2. Add tokens & cost to documents
    if 'documents' in existing_tables:
        doc_cols = {c['name'] for c in inspector.get_columns('documents')}
        with op.batch_alter_table('documents', schema=None) as batch_op:
            if 'extracted_tokens' not in doc_cols:
                batch_op.add_column(sa.Column('extracted_tokens', sa.Integer(), server_default='0', nullable=False))
            if 'estimated_cost_usd' not in doc_cols:
                batch_op.add_column(sa.Column('estimated_cost_usd', sa.Numeric(precision=10, scale=6), server_default='0.0', nullable=False))

    # 3. Add telemetry & provider settings to organization_settings
    if 'organization_settings' in existing_tables:
        settings_cols = {c['name'] for c in inspector.get_columns('organization_settings')}
        with op.batch_alter_table('organization_settings', schema=None) as batch_op:
            if 'primary_provider' not in settings_cols:
                batch_op.add_column(sa.Column('primary_provider', sa.String(length=50), server_default='gemini', nullable=False))
            if 'fallback_provider' not in settings_cols:
                batch_op.add_column(sa.Column('fallback_provider', sa.String(length=50), server_default='groq', nullable=False))
            if 'monthly_budget_usd' not in settings_cols:
                batch_op.add_column(sa.Column('monthly_budget_usd', sa.Numeric(precision=10, scale=2), server_default='0.0', nullable=False))
            if 'gemini_api_key_masked' not in settings_cols:
                batch_op.add_column(sa.Column('gemini_api_key_masked', sa.String(length=50), nullable=True))
            if 'groq_api_key_masked' not in settings_cols:
                batch_op.add_column(sa.Column('groq_api_key_masked', sa.String(length=50), nullable=True))

    # 4. Create new organization_invitations table
    if 'organization_invitations' not in existing_tables:
        op.create_table('organization_invitations',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('organization_id', sa.String(length=36), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('role', sa.String(length=50), nullable=False),
            sa.Column('token', sa.String(length=100), nullable=False),
            sa.Column('status', sa.String(length=50), nullable=False),
            sa.Column('invited_by_user_id', sa.String(length=36), nullable=True),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['invited_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('organization_invitations', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_organization_invitations_email'), ['email'], unique=False)
            batch_op.create_index(batch_op.f('ix_organization_invitations_organization_id'), ['organization_id'], unique=False)
            batch_op.create_index(batch_op.f('ix_organization_invitations_status'), ['status'], unique=False)
            batch_op.create_index(batch_op.f('ix_organization_invitations_token'), ['token'], unique=True)

    # 5. Create new subscriptions table
    if 'subscriptions' not in existing_tables:
        op.create_table('subscriptions',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('organization_id', sa.String(length=36), nullable=False),
            sa.Column('plan_tier', sa.String(length=50), nullable=False),
            sa.Column('status', sa.String(length=50), nullable=False),
            sa.Column('billing_cycle', sa.String(length=20), nullable=False),
            sa.Column('monthly_document_limit', sa.Integer(), nullable=False),
            sa.Column('max_users_limit', sa.Integer(), nullable=False),
            sa.Column('current_period_documents_used', sa.Integer(), nullable=False),
            sa.Column('price_amount', sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column('currency', sa.String(length=10), nullable=False),
            sa.Column('razorpay_customer_id', sa.String(length=100), nullable=True),
            sa.Column('razorpay_subscription_id', sa.String(length=100), nullable=True),
            sa.Column('trial_ends_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=True),
            sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('subscriptions', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_subscriptions_organization_id'), ['organization_id'], unique=True)
            batch_op.create_index(batch_op.f('ix_subscriptions_status'), ['status'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if 'subscriptions' in existing_tables:
        with op.batch_alter_table('subscriptions', schema=None) as batch_op:
            batch_op.drop_index(batch_op.f('ix_subscriptions_status'))
            batch_op.drop_index(batch_op.f('ix_subscriptions_organization_id'))
        op.drop_table('subscriptions')

    if 'organization_invitations' in existing_tables:
        with op.batch_alter_table('organization_invitations', schema=None) as batch_op:
            batch_op.drop_index(batch_op.f('ix_organization_invitations_token'))
            batch_op.drop_index(batch_op.f('ix_organization_invitations_status'))
            batch_op.drop_index(batch_op.f('ix_organization_invitations_organization_id'))
            batch_op.drop_index(batch_op.f('ix_organization_invitations_email'))
        op.drop_table('organization_invitations')

    if 'organization_settings' in existing_tables:
        settings_cols = {c['name'] for c in inspector.get_columns('organization_settings')}
        with op.batch_alter_table('organization_settings', schema=None) as batch_op:
            for col in ['groq_api_key_masked', 'gemini_api_key_masked', 'monthly_budget_usd', 'fallback_provider', 'primary_provider']:
                if col in settings_cols:
                    batch_op.drop_column(col)

    if 'documents' in existing_tables:
        doc_cols = {c['name'] for c in inspector.get_columns('documents')}
        with op.batch_alter_table('documents', schema=None) as batch_op:
            for col in ['estimated_cost_usd', 'extracted_tokens']:
                if col in doc_cols:
                    batch_op.drop_column(col)

    if 'organizations' in existing_tables:
        org_cols = {c['name'] for c in inspector.get_columns('organizations')}
        with op.batch_alter_table('organizations', schema=None) as batch_op:
            for col in ['onboarding_step', 'onboarding_completed', 'phone', 'pincode', 'state', 'city', 'address', 'pan', 'gstin', 'legal_name']:
                if col in org_cols:
                    batch_op.drop_column(col)
