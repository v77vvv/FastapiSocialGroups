from fastapi import FastAPI
import uvicorn
from api import group, group_user, group_message
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title='Social Stories')
app.include_router(group.router)
app.include_router(group_message.router)
app.include_router(group_user.router)

origins = [
    'http://localhost:3000'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

if __name__ == '__main__':
    uvicorn.run('main:app', reload=True, port=8004)