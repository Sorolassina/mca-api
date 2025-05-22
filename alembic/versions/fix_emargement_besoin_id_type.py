"""remove besoin_id from emargements

Revision ID: fix_emargement_besoin_id_type
Revises: add_programme_id_to_evenements
Create Date: 2024-03-19 11:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = 'fix_emargement_besoin_id_type'
down_revision: Union[str, None] = 'add_programme_id_to_evenements'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Vérifier si la contrainte existe avant de la supprimer
    connection = op.get_bind()
    constraint_exists = connection.execute(
        text("""
            SELECT 1 FROM information_schema.table_constraints 
            WHERE constraint_name = 'emargements_besoin_id_fkey' 
            AND table_name = 'emargements'
        """)
    ).scalar()
    
    if constraint_exists:
        op.drop_constraint('emargements_besoin_id_fkey', 'emargements', type_='foreignkey')
    
    # Supprimer la colonne besoin_id
    op.drop_column('emargements', 'besoin_id')

def downgrade() -> None:
    # Recréer la colonne besoin_id (en tant que String pour correspondre au type dans BesoinEvenement)
    op.add_column('emargements',
        sa.Column('besoin_id', sa.String(50), nullable=True)
    )
    # Recréer la contrainte de clé étrangère
    op.create_foreign_key(
        'emargements_besoin_id_fkey',
        'emargements', 'besoins_evenement',
        ['besoin_id'], ['id'],
        ondelete='CASCADE'
    ) 