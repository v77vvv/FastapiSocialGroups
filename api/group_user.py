from fastapi import HTTPException, status, APIRouter, Depends
from typing import Annotated, List
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db
from sqlalchemy import select
from handlers.social_auth import get_current_user
from database.schemes import GroupUserCreateScheme, GroupUserResponseScheme
from database.models import GroupUser, Group

router = APIRouter(prefix='/group_user', tags=['Group User'])

@router.post('/', response_model=GroupUserResponseScheme, tags=['Group User'])
async def post(
        scheme: GroupUserCreateScheme,
        current_user: Annotated[dict, Depends(get_current_user)],
        db: AsyncSession = Depends(get_db)
):  
    group_res = await db.execute(select(Group).where(Group.id==scheme.group))
    
    if not group_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Group not found")

    result = await db.execute(
        select(GroupUser).where(GroupUser.group==scheme.group,
                                GroupUser.user==current_user['id'])
    )
    scalar = result.scalar_one_or_none()

    if scalar:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail='U are already a member of this group')

    group_user = GroupUser(user=current_user['id'], **scheme.model_dump())

    db.add(group_user)
    await db.commit()
    await db.refresh(group_user)
    return group_user

@router.get('/', response_model=List[GroupUserResponseScheme], tags=['Group User'])
async def get_list(
        current_user: Annotated[dict, Depends(get_current_user)],
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(GroupUser).where(GroupUser.user==current_user['id']))
    return result.scalars().all()

@router.delete('/{id_}', status_code=status.HTTP_204_NO_CONTENT, tags=['Group User'])
async def delete(
        id_: int,
        current_user: Annotated[dict, Depends(get_current_user)],
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(GroupUser).where(
            GroupUser.id==id_, GroupUser.user == current_user['id']
        )
    )
    scalar = result.scalar_one_or_none()

    if not scalar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="You are not member of this group")

    await db.delete(scalar)
    await db.commit()
    return None