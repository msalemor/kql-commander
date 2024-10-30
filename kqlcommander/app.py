import logging
import os

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException
from openai import AsyncAzureOpenAI
from settings import get_settings_instance
from kqlhelper import exec_query, kql_databases, kql_table_schema, kql_tables, kql_tree
from models import *
from dotenv import load_dotenv

load_dotenv()
settings = get_settings_instance()
if settings.endpoint is None or settings.key is None or settings.version is None or settings.chat_model is None:
    logging.error("Missing required environment variables.")
    exit(1)

client = AsyncAzureOpenAI(azure_endpoint=settings.endpoint,
                          api_key=settings.key,
                          api_version=settings.version)

app = FastAPI()

# Enable CORS
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/databases", response_model=list[Database])
async def get_databases():
    return await kql_databases()


@app.get("/api/tables/{db}", response_model=list[Table])
async def get_tables(db: str):
    return await kql_tables()


@app.get("/api/schema/{db}/{table_name}", response_model=list[TableSchema])
async def get_schema(db: str = 'ContosoSales', table_name='Customers'):
    return await kql_table_schema()


@app.get("/api/tree", response_model=Tree)
async def get_tree():
    return await kql_tree()


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not request.messages or len(request.messages) == 0:
        raise HTTPException(
            status_code=400, detail="Messages property required")

    response = await client.chat.completions.create(
        model=settings.chat_model,
        messages=request.messages,
        temperature=request.temperature
    )

    return ChatResponse(content=response.choices[0].message.content)


@app.post("/api/execute")
async def execute(request: ExecuteRequest):
    if not request.query:
        raise HTTPException(status_code=404, detail="Item not found")
    try:
        rows = await exec_query(db='ContosoSales', query=request.query)
        # presult = rows.primary_results[0]
        # return DataRows(table_name=presult.table_name,
        #                   table_id=presult.table_id,
        #                   table_kind=presult.table_kind,
        #                   columns=presult.columns,
        #                   raw_rows=presult.raw_rows)
        if rows and rows.primary_results:
            return rows.primary_results[0]
        else:
            return []
    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=400)

app.mount("/", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    # asyncio.run(sample())
    import uvicorn
    uvicorn.run(app=app)
