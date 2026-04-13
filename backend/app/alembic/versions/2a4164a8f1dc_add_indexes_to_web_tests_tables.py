"""add indexes to web_tests tables

Revision ID: 2a4164a8f1dc
Revises: 2696ce2f76bb
Create Date: 2026-04-13 22:11:43.140338

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '2a4164a8f1dc'
down_revision = '2696ce2f76bb'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('ix_webtest_owner_id', 'webtest', ['owner_id'])
    op.create_index('ix_webtest_status', 'webtest', ['status'])
    op.create_index('ix_webtest_created_at', 'webtest', ['created_at'])
    op.create_index('ix_webtestresult_test_id', 'webtestresult', ['test_id'])


def downgrade():
    op.drop_index('ix_webtestresult_test_id', table_name='webtestresult')
    op.drop_index('ix_webtest_created_at', table_name='webtest')
    op.drop_index('ix_webtest_status', table_name='webtest')
    op.drop_index('ix_webtest_owner_id', table_name='webtest')
