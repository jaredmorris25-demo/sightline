"""initial schema

Revision ID: 5d17857927af
Revises:
Create Date: 2026-04-06 23:31:26.393941

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5d17857927af'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('locations',
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('slug', sa.String(length=255), nullable=False),
    sa.Column('geometry', geoalchemy2.types.Geometry(srid=4326, dimension=2, from_text='ST_GeomFromEWKT', name='geometry', nullable=False), nullable=False),
    sa.Column('location_type', sa.Enum('park', 'reserve', 'marine', 'urban', 'rural', name='locationtype'), nullable=False),
    sa.Column('country', sa.String(length=100), nullable=True),
    sa.Column('region', sa.String(length=255), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('slug')
    )
    op.create_index('ix_locations_geometry', 'locations', ['geometry'], unique=False, postgresql_using='gist')
    op.create_index('ix_locations_slug', 'locations', ['slug'], unique=False)
    op.create_table('species',
    sa.Column('common_name', sa.String(length=255), nullable=True),
    sa.Column('scientific_name', sa.String(length=255), nullable=False),
    sa.Column('kingdom', sa.String(length=100), nullable=True),
    sa.Column('phylum', sa.String(length=100), nullable=True),
    sa.Column('class', sa.String(length=100), nullable=True),
    sa.Column('order', sa.String(length=100), nullable=True),
    sa.Column('family', sa.String(length=100), nullable=True),
    sa.Column('genus', sa.String(length=100), nullable=True),
    sa.Column('inaturalist_id', sa.String(length=100), nullable=True),
    sa.Column('gbif_id', sa.String(length=100), nullable=True),
    sa.Column('ala_id', sa.String(length=100), nullable=True),
    sa.Column('conservation_status', sa.String(length=20), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('scientific_name')
    )
    op.create_index('ix_species_scientific_name', 'species', ['scientific_name'], unique=False)
    op.create_table('users',
    sa.Column('display_name', sa.String(length=255), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('auth_provider', sa.String(length=50), nullable=True),
    sa.Column('auth_provider_id', sa.String(length=255), nullable=True),
    sa.Column('bio', sa.Text(), nullable=True),
    sa.Column('location_home', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, dimension=2, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
    sa.Column('avatar_url', sa.String(length=2048), nullable=True),
    sa.Column('role', sa.Enum('observer', 'curator', 'admin', name='userrole'), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_auth_provider_id', 'users', ['auth_provider_id'], unique=False)
    op.create_index('ix_users_email', 'users', ['email'], unique=False)
    op.create_index('ix_users_location_home', 'users', ['location_home'], unique=False, postgresql_using='gist')
    op.create_table('groups',
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('slug', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('group_type', sa.Enum('class', 'team', 'org', 'campaign', 'open', name='grouptype'), nullable=False),
    sa.Column('owner_id', sa.UUID(), nullable=False),
    sa.Column('is_public', sa.Boolean(), nullable=False),
    sa.Column('join_policy', sa.Enum('open', 'invite', 'approval', name='joinpolicy'), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('slug')
    )
    op.create_index('ix_groups_slug', 'groups', ['slug'], unique=False)
    op.create_table('group_memberships',
    sa.Column('group_id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('role', sa.Enum('member', 'moderator', 'admin', name='memberrole'), nullable=False),
    sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_group_memberships_group_id', 'group_memberships', ['group_id'], unique=False)
    op.create_index('ix_group_memberships_user_id', 'group_memberships', ['user_id'], unique=False)
    op.create_table('sightings',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('group_id', sa.UUID(), nullable=True),
    sa.Column('species_id', sa.UUID(), nullable=False),
    sa.Column('observed_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('geometry', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, dimension=2, from_text='ST_GeomFromEWKT', name='geometry', nullable=False), nullable=False),
    sa.Column('location_description', sa.Text(), nullable=True),
    sa.Column('count', sa.Integer(), nullable=True),
    sa.Column('behaviour_notes', sa.Text(), nullable=True),
    sa.Column('visibility', sa.Enum('private', 'group', 'public', name='visibility'), nullable=False),
    sa.Column('verified', sa.Boolean(), nullable=False),
    sa.Column('verified_by', sa.UUID(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['species_id'], ['species.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['verified_by'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_sightings_geometry', 'sightings', ['geometry'], unique=False, postgresql_using='gist')
    op.create_index('ix_sightings_group_id', 'sightings', ['group_id'], unique=False)
    op.create_index('ix_sightings_observed_at', 'sightings', ['observed_at'], unique=False)
    op.create_index('ix_sightings_species_id', 'sightings', ['species_id'], unique=False)
    op.create_index('ix_sightings_user_id', 'sightings', ['user_id'], unique=False)
    op.create_table('ingest_records',
    sa.Column('source_format', sa.Enum('dwc', 'csv', 'shapefile', 'json', 'pdf', 'api', name='sourceformat'), nullable=False),
    sa.Column('source_system', sa.String(length=255), nullable=True),
    sa.Column('source_reference', sa.String(length=512), nullable=True),
    sa.Column('raw_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('group_id', sa.UUID(), nullable=True),
    sa.Column('submitted_by', sa.UUID(), nullable=False),
    sa.Column('submitted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('mapped_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('mapping_confidence', sa.Float(), nullable=True),
    sa.Column('mapping_notes', sa.Text(), nullable=True),
    sa.Column('canonical_sighting_id', sa.UUID(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['canonical_sighting_id'], ['sightings.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['submitted_by'], ['users.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ingest_records_canonical_sighting_id', 'ingest_records', ['canonical_sighting_id'], unique=False)
    op.create_index('ix_ingest_records_submitted_by', 'ingest_records', ['submitted_by'], unique=False)
    op.create_table('media',
    sa.Column('sighting_id', sa.UUID(), nullable=True),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.Enum('draft', 'attached', 'processing', 'ready', name='mediastatus'), nullable=False),
    sa.Column('blob_url', sa.String(length=2048), nullable=True),
    sa.Column('cdn_url', sa.String(length=2048), nullable=True),
    sa.Column('media_type', sa.Enum('photo', 'audio', 'video', name='mediatype'), nullable=False),
    sa.Column('file_size', sa.BigInteger(), nullable=True),
    sa.Column('mime_type', sa.String(length=100), nullable=True),
    sa.Column('exif_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('observed_at_device', sa.DateTime(timezone=True), nullable=True),
    sa.Column('exif_lat', sa.Float(), nullable=True),
    sa.Column('exif_lng', sa.Float(), nullable=True),
    sa.Column('gps_stripped', sa.Boolean(), nullable=False),
    sa.Column('synced_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['sighting_id'], ['sightings.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_media_sighting_id', 'media', ['sighting_id'], unique=False)
    op.create_index('ix_media_user_id', 'media', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_media_user_id', table_name='media')
    op.drop_index('ix_media_sighting_id', table_name='media')
    op.drop_table('media')
    op.drop_index('ix_ingest_records_submitted_by', table_name='ingest_records')
    op.drop_index('ix_ingest_records_canonical_sighting_id', table_name='ingest_records')
    op.drop_table('ingest_records')
    op.drop_index('ix_sightings_user_id', table_name='sightings')
    op.drop_index('ix_sightings_species_id', table_name='sightings')
    op.drop_index('ix_sightings_observed_at', table_name='sightings')
    op.drop_index('ix_sightings_group_id', table_name='sightings')
    op.drop_index('ix_sightings_geometry', table_name='sightings', postgresql_using='gist')
    op.drop_table('sightings')
    op.drop_index('ix_group_memberships_user_id', table_name='group_memberships')
    op.drop_index('ix_group_memberships_group_id', table_name='group_memberships')
    op.drop_table('group_memberships')
    op.drop_index('ix_groups_slug', table_name='groups')
    op.drop_table('groups')
    op.drop_index('ix_users_location_home', table_name='users', postgresql_using='gist')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_auth_provider_id', table_name='users')
    op.drop_table('users')
    op.drop_index('ix_species_scientific_name', table_name='species')
    op.drop_table('species')
    op.drop_index('ix_locations_slug', table_name='locations')
    op.drop_index('ix_locations_geometry', table_name='locations', postgresql_using='gist')
    op.drop_table('locations')
    # Drop custom enum types
    sa.Enum(name='mediastatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='mediatype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='sourceformat').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='visibility').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='memberrole').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='joinpolicy').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='grouptype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='locationtype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='userrole').drop(op.get_bind(), checkfirst=True)
