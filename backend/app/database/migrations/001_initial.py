"""Initial database migration

Revision ID: 001
Revises: 
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Execute the schema.sql file
    with open('app/database/schema.sql', 'r') as f:
        schema_sql = f.read()
    
    # Split by statements and execute
    statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
    
    connection = op.get_bind()
    for statement in statements:
        if statement:
            connection.execute(sa.text(statement))

def downgrade() -> None:
    # Drop all tables in reverse order
    op.drop_table('data_operations')
    op.drop_table('blink_data_2025_03')
    op.drop_table('blink_data_2025_02') 
    op.drop_table('blink_data_2025_01')
    op.drop_table('blink_data')
    op.drop_table('blink_sessions')
    op.drop_table('users')
    
    # Drop extension
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')