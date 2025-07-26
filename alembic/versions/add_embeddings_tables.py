"""Add vector embeddings tables for Supabase

Revision ID: add_embeddings_001
Revises: 
Create Date: 2024-01-01 12:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_embeddings_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create product_embeddings table
    op.create_table('product_embeddings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('restaurant_id', sa.Integer(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('embedding', sa.Text(), nullable=True),  # Supabase handles vector as text
        sa.Column('embedding_model', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_id')
    )
    op.create_index(op.f('ix_product_embeddings_id'), 'product_embeddings', ['id'], unique=False)
    
    # Create conversation_memories table
    op.create_table('conversation_memories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=True),
        sa.Column('restaurant_id', sa.Integer(), nullable=True),
        sa.Column('customer_phone', sa.String(), nullable=True),
        sa.Column('memory_type', sa.String(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('embedding', sa.Text(), nullable=True),  # Supabase handles vector as text
        sa.Column('importance_score', sa.Float(), nullable=True),
        sa.Column('access_count', sa.Integer(), nullable=True),
        sa.Column('last_accessed', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversation_memories_customer_phone'), 'conversation_memories', ['customer_phone'], unique=False)
    op.create_index(op.f('ix_conversation_memories_id'), 'conversation_memories', ['id'], unique=False)
    
    # Create knowledge_base table
    op.create_table('knowledge_base',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('restaurant_id', sa.Integer(), nullable=True),
        sa.Column('question', sa.Text(), nullable=True),
        sa.Column('answer', sa.Text(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('searchable_content', sa.Text(), nullable=True),
        sa.Column('embedding', sa.Text(), nullable=True),  # Supabase handles vector as text
        sa.Column('usage_count', sa.Integer(), nullable=True),
        sa.Column('last_used', sa.DateTime(timezone=True), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_knowledge_base_id'), 'knowledge_base', ['id'], unique=False)
    
    # Create search_logs table
    op.create_table('search_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=True),
        sa.Column('restaurant_id', sa.Integer(), nullable=True),
        sa.Column('query', sa.Text(), nullable=True),
        sa.Column('search_type', sa.String(), nullable=True),
        sa.Column('embedding', sa.Text(), nullable=True),  # Supabase handles vector as text
        sa.Column('results_found', sa.Integer(), nullable=True),
        sa.Column('top_similarity', sa.Float(), nullable=True),
        sa.Column('results_used', sa.JSON(), nullable=True),
        sa.Column('search_time_ms', sa.Integer(), nullable=True),
        sa.Column('embedding_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_search_logs_id'), 'search_logs', ['id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_search_logs_id'), table_name='search_logs')
    op.drop_table('search_logs')
    
    op.drop_index(op.f('ix_knowledge_base_id'), table_name='knowledge_base')
    op.drop_table('knowledge_base')
    
    op.drop_index(op.f('ix_conversation_memories_id'), table_name='conversation_memories')
    op.drop_index(op.f('ix_conversation_memories_customer_phone'), table_name='conversation_memories')
    op.drop_table('conversation_memories')
    
    op.drop_index(op.f('ix_product_embeddings_id'), table_name='product_embeddings')
    op.drop_table('product_embeddings')
    
    # Note: We don't drop the vector extension as it might be used by other applications