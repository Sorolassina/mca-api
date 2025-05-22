"""change besoin evenement id to string

Revision ID: change_besoin_id_to_string
Revises: 74b74768839f
Create Date: 2024-03-07 15:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'change_besoin_id_to_string'
down_revision: Union[str, None] = 'add_timezone_to_evenement_dates'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Supprimer la contrainte de clé étrangère sur la table emargements
    op.drop_constraint('emargements_besoin_id_fkey', 'emargements', type_='foreignkey')
    
    # 2. Modifier le type de la colonne besoin_id dans emargements
    op.alter_column('emargements', 'besoin_id',
                    existing_type=sa.Integer(),
                    type_=sa.String(50),
                    postgresql_using="besoin_id::text",
                    existing_nullable=True)
    
    # 3. Créer une table temporaire avec la nouvelle structure
    op.create_table(
        'besoins_evenement_new',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('titre', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('date_evenement', sa.Date(), nullable=False),
        sa.Column('nb_jours', sa.Integer(), nullable=True),
        sa.Column('lieu', sa.String(100), nullable=True),
        sa.Column('is_participant', sa.Boolean(), nullable=True),
        sa.Column('nom', sa.String(50), nullable=False),
        sa.Column('prenom', sa.String(50), nullable=False),
        sa.Column('email', sa.String(100), nullable=False),
        sa.Column('besoins_principaux', sa.Text(), nullable=False),
        sa.Column('attentes', sa.Text(), nullable=True),
        sa.Column('niveau_connaissance', sa.String(20), nullable=False),
        sa.Column('objectifs', sa.Text(), nullable=True),
        sa.Column('contraintes', sa.Text(), nullable=True),
        sa.Column('rgpd_consent', sa.Boolean(), nullable=False),
        sa.Column('rgpd_consent_date', sa.Date(), nullable=True),
        sa.Column('date_soumission', sa.Date(), server_default=sa.text('CURRENT_DATE'), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['evenements.id'], ondelete='CASCADE')
    )

    # 4. Copier les données en convertissant l'ID
    op.execute("""
        INSERT INTO besoins_evenement_new (
            id, event_id, titre, description, date_evenement, nb_jours, lieu,
            is_participant, nom, prenom, email, besoins_principaux, attentes,
            niveau_connaissance, objectifs, contraintes, rgpd_consent,
            rgpd_consent_date, date_soumission
        )
        SELECT 
            'besoin_' || event_id::text || '_' || id::text,
            event_id, titre, description, date_evenement, nb_jours, lieu,
            is_participant, nom, prenom, email, besoins_principaux, attentes,
            niveau_connaissance, objectifs, contraintes, rgpd_consent,
            rgpd_consent_date, date_soumission
        FROM besoins_evenement
    """)

    # 5. Mettre à jour les références dans la table emargements
    op.execute("""
        UPDATE emargements e
        SET besoin_id = 'besoin_' || b.event_id::text || '_' || b.id::text
        FROM besoins_evenement b
        WHERE e.besoin_id = b.id::text
    """)

    # 6. Supprimer l'ancienne table
    op.drop_table('besoins_evenement')

    # 7. Renommer la nouvelle table
    op.rename_table('besoins_evenement_new', 'besoins_evenement')

    # 8. Recréer la contrainte de clé étrangère
    op.create_foreign_key(
        'emargements_besoin_id_fkey',
        'emargements', 'besoins_evenement',
        ['besoin_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # 1. Supprimer la contrainte de clé étrangère
    op.drop_constraint('emargements_besoin_id_fkey', 'emargements', type_='foreignkey')

    # 2. Créer une table temporaire avec l'ancienne structure
    op.create_table(
        'besoins_evenement_old',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('titre', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('date_evenement', sa.Date(), nullable=False),
        sa.Column('nb_jours', sa.Integer(), nullable=True),
        sa.Column('lieu', sa.String(100), nullable=True),
        sa.Column('is_participant', sa.Boolean(), nullable=True),
        sa.Column('nom', sa.String(50), nullable=False),
        sa.Column('prenom', sa.String(50), nullable=False),
        sa.Column('email', sa.String(100), nullable=False),
        sa.Column('besoins_principaux', sa.Text(), nullable=False),
        sa.Column('attentes', sa.Text(), nullable=True),
        sa.Column('niveau_connaissance', sa.String(20), nullable=False),
        sa.Column('objectifs', sa.Text(), nullable=True),
        sa.Column('contraintes', sa.Text(), nullable=True),
        sa.Column('rgpd_consent', sa.Boolean(), nullable=False),
        sa.Column('rgpd_consent_date', sa.Date(), nullable=True),
        sa.Column('date_soumission', sa.Date(), server_default=sa.text('CURRENT_DATE'), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['evenements.id'], ondelete='CASCADE')
    )

    # 3. Copier les données en extrayant l'ID numérique
    op.execute("""
        INSERT INTO besoins_evenement_old (
            event_id, titre, description, date_evenement, nb_jours, lieu,
            is_participant, nom, prenom, email, besoins_principaux, attentes,
            niveau_connaissance, objectifs, contraintes, rgpd_consent,
            rgpd_consent_date, date_soumission
        )
        SELECT 
            event_id, titre, description, date_evenement, nb_jours, lieu,
            is_participant, nom, prenom, email, besoins_principaux, attentes,
            niveau_connaissance, objectifs, contraintes, rgpd_consent,
            rgpd_consent_date, date_soumission
        FROM besoins_evenement
    """)

    # 4. Mettre à jour les références dans la table emargements
    op.execute("""
        UPDATE emargements e
        SET besoin_id = (regexp_matches(e.besoin_id, '_([0-9]+)$'))[1]::integer
        WHERE e.besoin_id IS NOT NULL
    """)

    # 5. Modifier le type de la colonne besoin_id dans emargements
    op.alter_column('emargements', 'besoin_id',
                    existing_type=sa.String(50),
                    type_=sa.Integer(),
                    postgresql_using="besoin_id::integer",
                    existing_nullable=True)

    # 6. Supprimer la table actuelle
    op.drop_table('besoins_evenement')

    # 7. Renommer l'ancienne table
    op.rename_table('besoins_evenement_old', 'besoins_evenement')

    # 8. Recréer la contrainte de clé étrangère
    op.create_foreign_key(
        'emargements_besoin_id_fkey',
        'emargements', 'besoins_evenement',
        ['besoin_id'], ['id'],
        ondelete='CASCADE'
    ) 