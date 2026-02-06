"""Initial schema with orders table

Revision ID: 001_initial
Revises: 
Create Date: 2026-02-06 14:08:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create orders table"""
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('order_id', UUID(as_uuid=True), nullable=False, comment='Unique order identifier (UUID)'),
        sa.Column('pg_order_id', sa.String(length=64), nullable=True, comment='Payment gateway order ID from HDFC'),
        sa.Column('amount', sa.Integer(), nullable=False, comment='Amount in smallest currency unit (paise for INR)'),
        sa.Column('currency', sa.String(length=8), nullable=False, server_default='INR', comment='Currency code (ISO 4217)'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PENDING', comment='Order status: PENDING, SUCCESS, FAILED, CANCELLED, PROCESSING'),
        sa.Column('raw_payload', sa.JSON(), nullable=True, comment='Original request payload for debugging'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()'), comment='Order creation timestamp'),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()'), comment='Last update timestamp'),
        sa.CheckConstraint('amount > 0', name='check_amount_positive'),
        sa.CheckConstraint("status IN ('PENDING', 'SUCCESS', 'FAILED', 'CANCELLED', 'PROCESSING')", name='check_status_valid'),
        sa.CheckConstraint("currency IN ('INR', 'USD', 'EUR', 'GBP')", name='check_currency_valid'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_id')
    )
    
    # Create indexes
    op.create_index('idx_order_status_created', 'orders', ['status', 'created_at'])
    op.create_index('idx_pg_order_id', 'orders', ['pg_order_id'])
    op.create_index(op.f('ix_orders_order_id'), 'orders', ['order_id'], unique=True)
    op.create_index(op.f('ix_orders_pg_order_id'), 'orders', ['pg_order_id'], unique=False)
    op.create_index(op.f('ix_orders_status'), 'orders', ['status'], unique=False)


def downgrade() -> None:
    """Drop orders table"""
    op.drop_index(op.f('ix_orders_status'), table_name='orders')
    op.drop_index(op.f('ix_orders_pg_order_id'), table_name='orders')
    op.drop_index(op.f('ix_orders_order_id'), table_name='orders')
    op.drop_index('idx_pg_order_id', table_name='orders')
    op.drop_index('idx_order_status_created', table_name='orders')
    op.drop_table('orders')
