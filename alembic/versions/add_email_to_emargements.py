"""add email column to emargements

Revision ID: add_email_to_emargements
Revises: fix_emargement_besoin_id_type
Create Date: 2024-03-19 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_email_to_emargements'
down_revision: Union[str, None] = 'fix_emargement_besoin_id_type'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Ajouter la colonne email à la table emargements
    op.add_column('emargements',
        sa.Column('email', sa.String(100), nullable=True)
    )

def downgrade() -> None:
    # Supprimer la colonne email
    op.drop_column('emargements', 'email') 