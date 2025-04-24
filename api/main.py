from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
import uvicorn
from db import get_db
from fastapi_utils import json_http_resp

app = FastAPI(default_response_class=JSONResponse)
DB = get_db()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get('/repos/sorted')
def sorted_repos(by: str = 'stars'):
    repos = list(DB['repos'].find().sort(by, -1).limit(50))
    return json_http_resp(repos)


@app.get('/repos/{repo_id}')
def get_repo(repo_id: int):
    doc = DB['repos'].find_one({ '_id': repo_id })
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return dict(doc)


if __name__ == '__main__':
    uvicorn.run(app, host='localhost', port=8081)