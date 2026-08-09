from pydantic import BaseModel, Field
from datetime import date

class GroupResponseScheme(BaseModel):
    id: int
    name: str
    owner: int
    created_date: date

class GroupCreateScheme(BaseModel):
    name: str = Field(min_length=1, max_length=30)


class GroupUserResponseScheme(BaseModel):
    id: int
    group: int
    user: int
    created_date: date

class GroupUserCreateScheme(BaseModel):
    group: int


class GroupMessageResponseScheme(BaseModel):
    id: int
    group: int
    user: int
    message: str
    sent_date: date

class GroupMessageCreateScheme(BaseModel):
    group: int
    message: str = Field(min_length=1, max_length=5000)

class GroupMessageUpdateScheme(BaseModel):
    message: str = Field(min_length=1, max_length=5000)