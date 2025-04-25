from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
import uvicorn
from db import get_db
from fastapi_utils import json_http_resp

app = FastAPI(default_response_class=JSONResponse)
DB = get_db()

@app.get("/")
def read_root():
    return 'Hi world!'

@app.get('/repos/sorted')
def sorted_repos(by: str = 'stars'):
    if not DB['repos'].find_one({by: {"$exists": True}}):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"<<{by}>> field not found!")
    fields = {'_id', 'full_name', 'url', 'stars','forks'}
    repos = list(DB['repos'].find({}, fields).sort(by, -1).limit(50))
    return json_http_resp(repos)


@app.get('/repos/{repo_id}')
def get_repo(repo_id: int):
    doc = DB['repos'].find_one({ '_id': repo_id })
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Repo #{repo_id} does not exists!')
    return dict(doc)


if __name__ == '__main__':
    uvicorn.run(app, host='localhost', port=8081)