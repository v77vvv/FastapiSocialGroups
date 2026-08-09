from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Date, ForeignKey, String
from .connection import Base
from typing import List
from datetime import date

class Group(Base):
    __tablename__ = 'group'

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    name: Mapped[str] = mapped_column(String(30), nullable=False)
    owner: Mapped[int] = mapped_column(nullable=False)
    created_date: Mapped[date] = mapped_column(Date, default=date.today)

    group_user: Mapped[List['GroupUser']] = relationship(back_populates='user_group',
                                                         cascade='all, delete-orphan')
    group_message: Mapped[List['GroupMessage']] = relationship(back_populates='message_group',
                                                         cascade='all, delete-orphan')

    def __repr__(self):
        return f'Group(id={self.id}, owner={self.owner})'

class GroupUser(Base):
    __tablename__ = 'group_user'

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    group: Mapped[Group] = mapped_column(ForeignKey('group.id', ondelete='CASCADE'), nullable=False)
    user: Mapped[int] = mapped_column(nullable=False)
    created_date: Mapped[date] = mapped_column(Date, default=date.today)

    user_group: Mapped[Group] = relationship(back_populates='group_user')

    def __repr__(self):
        return f'GroupUser(id={self.id}, group={self.group.id}, user={self.user})'

class GroupMessage(Base):
    __tablename__ = 'group_message'

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    group: Mapped[Group] = mapped_column(ForeignKey('group.id', ondelete='CASCADE'), nullable=False)
    user: Mapped[int] = mapped_column(nullable=False)
    message: Mapped[str] = mapped_column(String(5000), nullable=False)
    sent_date: Mapped[date] = mapped_column(Date, default=date.today)

    message_group: Mapped[Group] = relationship(back_populates='group_message')

    def __repr__(self):
        return f'GroupMessage(id={self.id}, group={self.group.id}, user={self.user})'