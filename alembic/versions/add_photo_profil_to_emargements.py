"""add photo_profil column to emargements

Revision ID: add_photo_profil_to_emargements
Revises: add_email_to_emargements
Create Date: 2024-03-20 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_photo_profil_to_emargements'
down_revision: Union[str, None] = 'add_email_to_emargements'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Ajouter la colonne photo_profil à la table emargements
    op.add_column('emargements',
        sa.Column('photo_profil', sa.String(), nullable=True)
    )

def downgrade() -> None:
    # Supprimer la colonne photo_profil
    op.drop_column('emargements', 'photo_profil') 