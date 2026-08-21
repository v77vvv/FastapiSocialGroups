import httpx
from config import settings
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated

async def verify_access_token(token: str):
    async with httpx.AsyncClient(timeout=3.0) as client:
        try:
            response = await client.get(
                f'{settings.SOCIAL_AUTH_URL}/profile/',
                headers={'Authorization': f'Bearer {token}'}
            )

        except httpx.RequestError:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Could not connect to auth service')

        if response.status_code == 401:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid or expired token')

        try:
            user_data = response.json()
            return {
                'id': user_data['id']
            }

        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

bearer_scheme = HTTPBearer(auto_error=False)
async def get_current_user(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]
):
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication credentials were not provided')

    elif credentials.scheme.lower() != 'bearer':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token type')

    return await verify_access_token(credentials.credentials)