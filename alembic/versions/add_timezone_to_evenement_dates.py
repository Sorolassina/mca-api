"""add timezone to evenement dates

Revision ID: add_timezone_to_evenement_dates
Revises: None  # Nous allons laisser Alembic déterminer la dernière révision
Create Date: 2024-03-09 07:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_timezone_to_evenement_dates'
down_revision = '74b74768839f'  # Changé de '923439699dcd' à None 
branch_labels = None
depends_on = None

def upgrade():
    # Convertir les colonnes existantes en type avec timezone
    op.execute("""
        ALTER TABLE evenements 
        ALTER COLUMN date_debut TYPE TIMESTAMP WITH TIME ZONE 
        USING date_debut AT TIME ZONE 'UTC',
        ALTER COLUMN date_fin TYPE TIMESTAMP WITH TIME ZONE 
        USING date_fin AT TIME ZONE 'UTC'
    """)

def downgrade():
    # Revenir au type sans timezone
    op.execute("""
        ALTER TABLE evenements 
        ALTER COLUMN date_debut TYPE TIMESTAMP WITHOUT TIME ZONE 
        USING date_debut AT TIME ZONE 'UTC',
        ALTER COLUMN date_fin TYPE TIMESTAMP WITHOUT TIME ZONE 
        USING date_fin AT TIME ZONE 'UTC'
    """) 