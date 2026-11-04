"""add_data_rights_and_consent_models

Revision ID: cf29860092de
Revises: d417279d3854
Create Date: 2026-11-03 18:26:09.164098

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cf29860092de'
down_revision: Union[str, Sequence[str], None] = 'd417279d3854'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema with defensive checks."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if 'data_rights_requests' not in existing_tables:
        op.create_table('data_rights_requests',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('organization_id', sa.String(length=36), nullable=False),
            sa.Column('user_id', sa.String(length=36), nullable=False),
            sa.Column('request_type', sa.String(length=50), nullable=False),
            sa.Column('status', sa.String(length=50), nullable=False),
            sa.Column('details', sa.JSON(), nullable=False),
            sa.Column('requested_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('processed_by', sa.String(length=36), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('data_rights_requests', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_data_rights_requests_organization_id'), ['organization_id'], unique=False)
            batch_op.create_index(batch_op.f('ix_data_rights_requests_request_type'), ['request_type'], unique=False)
            batch_op.create_index(batch_op.f('ix_data_rights_requests_status'), ['status'], unique=False)
            batch_op.create_index(batch_op.f('ix_data_rights_requests_user_id'), ['user_id'], unique=False)

    if 'organization_settings' in existing_tables:
        settings_cols = {c['name'] for c in inspector.get_columns('organization_settings')}
        with op.batch_alter_table('organization_settings', schema=None) as batch_op:
            if 'tenant_disable_external_ai' not in settings_cols:
                batch_op.add_column(sa.Column('tenant_disable_external_ai', sa.Boolean(), nullable=False, server_default=sa.text('0')))
            if 'consent_withdrawn' not in settings_cols:
                batch_op.add_column(sa.Column('consent_withdrawn', sa.Boolean(), nullable=False, server_default=sa.text('0')))
            if 'consent_withdrawn_at' not in settings_cols:
                batch_op.add_column(sa.Column('consent_withdrawn_at', sa.DateTime(timezone=True), nullable=True))
            if 'retention_policy_days' not in settings_cols:
                batch_op.add_column(sa.Column('retention_policy_days', sa.Integer(), nullable=False, server_default=sa.text('365')))
            if 'data_rights_contact_email' not in settings_cols:
                batch_op.add_column(sa.Column('data_rights_contact_email', sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if 'organization_settings' in existing_tables:
        settings_cols = {c['name'] for c in inspector.get_columns('organization_settings')}
        with op.batch_alter_table('organization_settings', schema=None) as batch_op:
            for col in ['data_rights_contact_email', 'retention_policy_days', 'consent_withdrawn_at', 'consent_withdrawn', 'tenant_disable_external_ai']:
                if col in settings_cols:
                    batch_op.drop_column(col)

    if 'data_rights_requests' in existing_tables:
        with op.batch_alter_table('data_rights_requests', schema=None) as batch_op:
            batch_op.drop_index(batch_op.f('ix_data_rights_requests_user_id'))
            batch_op.drop_index(batch_op.f('ix_data_rights_requests_status'))
            batch_op.drop_index(batch_op.f('ix_data_rights_requests_request_type'))
            batch_op.drop_index(batch_op.f('ix_data_rights_requests_organization_id'))
        op.drop_table('data_rights_requests')
