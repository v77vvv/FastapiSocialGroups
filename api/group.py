from fastapi import HTTPException, status, APIRouter, Depends
from typing import Annotated, List
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db
from sqlalchemy import select
from handlers.social_auth import get_current_user
from database.schemes import GroupResponseScheme, GroupCreateScheme
from database.models import Group

router = APIRouter(prefix='/group', tags=['Group'])

@router.post('/', response_model=GroupResponseScheme, tags=['Group'])
async def post(
        scheme: GroupCreateScheme,
        current_user: Annotated[dict, Depends(get_current_user)],
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Group).where(Group.name==scheme.name))
    scalar = result.scalar_one_or_none()

    if scalar:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail='Group with this name already exists')

    group = Group(owner=current_user['id'], **scheme.model_dump())

    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group

@router.get('/', response_model=List[GroupResponseScheme], tags=['Group'])
async def get_list(
        current_user: Annotated[dict, Depends(get_current_user)],
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Group).where(Group.owner==current_user['id']))
    return result.scalars().all()

@router.put('/', response_model=GroupResponseScheme, tags=['Group'])
async def put(
        scheme: GroupCreateScheme,
        current_user: Annotated[dict, Depends(get_current_user)],
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Group).where(Group.owner==current_user['id']))
    scalar = result.scalar_one_or_none()

    if not scalar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='U are not owner of this group')

    update_date = scheme.model_dump(exclude_unset=True)
    for key, value in update_date.items():
        setattr(scalar, key, value)

    await db.commit()
    await db.refresh(scalar)
    return scalar

@router.delete('/{id_}', status_code=status.HTTP_204_NO_CONTENT, tags=['Group'])
async def delete(
        id_: int,
        current_user: Annotated[dict, Depends(get_current_user)],
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Group).where(Group.id==id_, Group.owner == current_user['id'])
    )
    scalar = result.scalar_one_or_none()

    if not scalar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="U cannot delete someone's group")

    await db.delete(scalar)
    await db.commit()
    return None