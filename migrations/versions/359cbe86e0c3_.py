"""empty message

Revision ID: 359cbe86e0c3
Revises: 
Create Date: 2019-12-16 20:03:51.281664

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '359cbe86e0c3'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.Column('first', sa.String(length=128), nullable=True),
    sa.Column('last', sa.String(length=128), nullable=True),
    sa.Column('email', sa.String(length=64), nullable=True),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.Column('phone', sa.Integer(), nullable=True),
    sa.Column('qualified', sa.Boolean(), nullable=True),
    sa.Column('data', sa.String(length=32768), nullable=True),
    sa.Column('points', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_Users_email'), 'Users', ['email'], unique=True)
    op.create_index(op.f('ix_Users_points'), 'Users', ['points'], unique=False)
    op.create_index(op.f('ix_Users_qualified'), 'Users', ['qualified'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_Users_qualified'), table_name='Users')
    op.drop_index(op.f('ix_Users_points'), table_name='Users')
    op.drop_index(op.f('ix_Users_email'), table_name='Users')
    op.drop_table('Users')
    # ### end Alembic commands ###
