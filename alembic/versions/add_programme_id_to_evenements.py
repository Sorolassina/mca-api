"""add programme id to evenements

Revision ID: add_programme_id_to_evenements
Revises: change_besoin_id_to_string
Create Date: 2024-03-19 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_programme_id_to_evenements'
down_revision: Union[str, None] = 'change_besoin_id_to_string'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Ajouter la colonne id_prog avec une valeur par défaut de 1
    op.add_column('evenements',
        sa.Column('id_prog', sa.Integer(), nullable=True, server_default='0')
    )
    
    # 2. Créer la contrainte de clé étrangère
    op.create_foreign_key(
        'fk_evenements_programme',
        'evenements', 'programmes',
        ['id_prog'], ['id']
    )
    
    # 3. Créer un index pour améliorer les performances
    op.create_index(
        'ix_evenements_programme',
        'evenements',
        ['id_prog']
    )

def downgrade() -> None:
    # 1. Supprimer l'index
    op.drop_index('ix_evenements_programme', table_name='evenements')
    
    # 2. Supprimer la contrainte de clé étrangère
    op.drop_constraint('fk_evenements_programme', 'evenements', type_='foreignkey')
    
    # 3. Supprimer la colonne
    op.drop_column('evenements', 'id_prog') 