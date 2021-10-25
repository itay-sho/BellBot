from fastapi import FastAPI
import json

app = FastAPI()


def load_secrets() -> dict:
    with open('../intercom-agi/secrets.json') as f:
        return json.loads(f.read())


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/shit")
async def shit():
    return {'return': 'ok'}
