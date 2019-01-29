import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


# Table for users of item catalog
class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(300), nullable=False)
    email = Column(String(300), nullable=False)


# Table for database items
class ItemsDB(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True)
    itemName = Column(String(300), nullable=False)
    description = Column(String(), nullable=False)
    category = Column(String(300), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.itemName,
            'category': self.category,
            'description': self.description
        }

engine = create_engine('sqlite:///ItemsDB.db')
Base.metadata.create_all(engine)
