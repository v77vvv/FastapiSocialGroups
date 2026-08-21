from fastapi import HTTPException, status, APIRouter, Depends
from typing import Annotated, List
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db
from sqlalchemy import select
from handlers.social_auth import get_current_user
from database.schemes import GroupMessageCreateScheme, GroupMessageResponseScheme, GroupMessageUpdateScheme
from database.models import GroupUser, GroupMessage

router = APIRouter(prefix='/group_message', tags=['Group Message'])

@router.post('/', response_model=GroupMessageResponseScheme, tags=['Group Message'])
async def post(
        scheme: GroupMessageCreateScheme,
        current_user: Annotated[dict, Depends(get_current_user)],
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(GroupUser).where(
            GroupUser.id == scheme.group,
            GroupUser.user == current_user['id']
        )
    )
    scalar = result.scalar_one_or_none()

    if not scalar:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You are not a member of this group'
        )

    group_message = GroupMessage(user=current_user['id'], **scheme.model_dump())

    db.add(group_message)
    await db.commit()
    await db.refresh(group_message)
    return group_message

@router.get('/', response_model=List[GroupMessageResponseScheme], tags=['Group Message'])
async def get_list(
        current_user: Annotated[dict, Depends(get_current_user)],
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(GroupMessage).where(GroupMessage.user==current_user['id'])
    )
    return result.scalars().all()

@router.put('/{id_}', response_model=GroupMessageResponseScheme, tags=['Group Message'])
async def put(
        id_: int,
        scheme: GroupMessageUpdateScheme,
        current_user: Annotated[dict, Depends(get_current_user)],
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(GroupMessage).where(GroupMessage.id == id_, GroupMessage.user == current_user['id'])
    )
    scalar = result.scalar_one_or_none()

    if not scalar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='U are not owner of this message')

    update_data = scheme.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(scalar, key, value)

    await db.commit()
    await db.refresh(scalar)
    return scalar

@router.delete('/{id_}', status_code=status.HTTP_204_NO_CONTENT, tags=['Group Message'])
async def delete(
        id_: int,
        current_user: Annotated[dict, Depends(get_current_user)],
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(GroupMessage).where(
            GroupMessage.id==id_, GroupMessage.user == current_user['id']
        )
    )
    scalar = result.scalar_one_or_none()

    if not scalar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="You cannot delete someone's message")

    await db.delete(scalar)
    await db.commit()
    return None