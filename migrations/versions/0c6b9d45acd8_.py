"""empty message

Revision ID: 0c6b9d45acd8
Revises: 
Create Date: 2024-05-24 19:07:28.932088

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0c6b9d45acd8'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('fav_breeds', sa.JSON(none_as_null=256), nullable=False))
        batch_op.drop_column('breed_3_img_url')
        batch_op.drop_column('breed_4_img_url')
        batch_op.drop_column('breed_2_img_url')
        batch_op.drop_column('breed_1_img_url')
        batch_op.drop_column('breed_4')
        batch_op.drop_column('breed_2')
        batch_op.drop_column('breed_5_img_url')
        batch_op.drop_column('breed_3')
        batch_op.drop_column('breed_5')
        batch_op.drop_column('breed_1')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('breed_1', sa.VARCHAR(length=100), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('breed_5', sa.VARCHAR(length=100), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('breed_3', sa.VARCHAR(length=100), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('breed_5_img_url', sa.VARCHAR(length=200), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('breed_2', sa.VARCHAR(length=100), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('breed_4', sa.VARCHAR(length=100), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('breed_1_img_url', sa.VARCHAR(length=200), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('breed_2_img_url', sa.VARCHAR(length=200), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('breed_4_img_url', sa.VARCHAR(length=200), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('breed_3_img_url', sa.VARCHAR(length=200), autoincrement=False, nullable=True))
        batch_op.drop_column('fav_breeds')

    # ### end Alembic commands ###
