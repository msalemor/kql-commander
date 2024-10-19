from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException
import asyncio
import logging
from typing import Any, List
from azure.kusto.data import KustoConnectionStringBuilder
from azure.kusto.data.aio import KustoClient
from pydantic import BaseModel

KUSTO_CLUSTER = "https://help.kusto.windows.net/"
kcsb = KustoConnectionStringBuilder.with_az_cli_authentication(KUSTO_CLUSTER)


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


def print_rows(rows):
    for row in rows.primary_results[0]:
        print(row[0], " ", row)


async def exec_query(db, query):
    try:
        async with KustoClient(kcsb) as client:
            rows = await client.execute(db, query)
            return rows
    except:
        logging.error("Unable to query")
        return []


class ExecuteRequest(BaseModel):
    db: str
    query: str


class DataRows(BaseModel):
    table_name: str
    table_id: int
    table_kind: str
    columns: Any
    raw_rows: List[Any]


class Database(BaseModel):
    DatabaseName: str


class Table(BaseModel):
    TableName: str = 'SecurityLogs'


class TableSchema(BaseModel):
    ColumnName: str
    DataType: str


class TableInfo(BaseModel):
    TableName: str
    Schema: List[TableSchema]


class DatabaseTree(BaseModel):
    DatabaseName: str
    Tables: List[TableInfo]


class Tree(BaseModel):
    DatabasesTree: List[DatabaseTree]


@app.get("/api/databases", response_model=list[Database])
async def get_databases():
    db = ''
    query = ".show databases"
    rows = await exec_query(db, query)
    list = [Database(DatabaseName=row[0]) for row in rows.primary_results[0]]
    list.sort(key=lambda x: x.DatabaseName)
    return list


@app.get("/api/tables/{db}", response_model=list[Table])
async def get_tables(db: str):
    query = ".show tables"
    rows = await exec_query(db, query)
    list = [Table(TableName=row[0]) for row in rows.primary_results[0]]
    list.sort(key=lambda x: x.TableName)
    return list


@app.get("/api/schema/{db}/{table_name}", response_model=list[TableSchema])
async def get_schema(db: str = 'ContosoSales', table_name='Customers'):
    query = f"{table_name} | getschema"
    rows = await exec_query(db, query)
    list = []
    for row in rows.primary_results[0]:
        list.append(TableSchema(ColumnName=row[0], DataType=row[2]))
    list.sort(key=lambda x: x.ColumnName)
    return list


async def get_schema_info(db: str = 'ContosoSales', table_name='Customers'):
    query = f"{table_name} | getschema"
    rows = await exec_query(db, query)
    list = []
    for row in rows.primary_results[0]:
        list.append(TableSchema(ColumnName=row[0], DataType=row[2]))
    list.sort(key=lambda x: x.ColumnName)
    return TableInfo(TableName=table_name, Schema=list)


async def get_dbschema_info(db: str = 'ContosoSales', table_name='Customers'):
    query = f"{table_name} | getschema"
    rows = await exec_query(db, query)
    list = []
    for row in rows.primary_results[0]:
        list.append(TableSchema(ColumnName=row[0], DataType=row[2]))
    list.sort(key=lambda x: x.ColumnName)
    return DatabaseTableInfo(DatabaseName=db, TableName=table_name, Schema=list)


async def get_table_schemas(db: str, tables: list) -> list:
    start_time = datetime.now()
    tasks = []
    for table in tables:
        if table and bool(table.TableName):
            t = asyncio.create_task(get_schema_info(db, table.TableName))
            tasks.append(t)
    results = await asyncio.gather(*tasks)
    time_diff = (datetime.now() - start_time).total_seconds()
    print("Processing time:", time_diff)
    return results


class DatabaseTableInfo(BaseModel):
    DatabaseName: str
    TableName: str
    Schema: List[TableSchema]


async def get_dbtable_schemas(databases: list, tables: list) -> list:
    start_time = datetime.now()
    tasks = []
    for db in databases:
        for table in tables:
            if table and bool(table.TableName):
                t = asyncio.create_task(get_dbschema_info(db, table.TableName))
                tasks.append(t)
    results = await asyncio.gather(*tasks)
    time_diff = (datetime.now() - start_time).total_seconds()
    print("Processing time:", time_diff)
    return results


async def cache(key, json_data):
    await asyncio.sleep(.01)
    print("saving to cache:", key, json_data)


async def get_cache(key: str) -> str:
    await asyncio.sleep(.01)
    return None


@app.get("/api/tree", response_model=Tree)
async def get_tree():
    cache_data = await get_cache('tree')
    if cache_data is None:
        # Databases
        list = []
        databases = await get_databases()
        for db in databases:

            print("Processing database", db.DatabaseName)
            tables = await get_tables(db.DatabaseName)
            table_list = []

            # NOTE: Perf - process all table schemas concurrently
            table_infos = await get_table_schemas(db.DatabaseName, tables)
            for table_info in table_infos:
                print("Processing table:", table_info.TableName)
                table_list.append(table_info)
            list.append(DatabaseTree(
                DatabaseName=db.DatabaseName, Tables=table_list))

        tree = Tree(DatabasesTree=list)
        cache('tree', tree)
        return tree
    else:
        return Tree.model_validate_json(cache_data)


async def get_data():
    async with KustoClient(kcsb) as client:
        db = "ContosoSales"
        query = "Customers | take 10"

        response = await client.execute(db, query)
        print_rows(response)


async def sample():
    databases = await get_databases()
    tables = await get_tables(databases[0])
    schema = await get_schema(databases[0], tables[0])
    # await get_data()
    # await get_schema()


@app.post("/api/chat")
async def chat():
    return {'message': 'OK'}


@app.post("/api/execute")
async def execute(request: ExecuteRequest):
    if not request.db or not request.query:
        raise HTTPException(status_code=404, detail="Item not found")
    rows = await exec_query(db=request.db, query=request.query)
    # presult = rows.primary_results[0]
    # return DataRows(table_name=presult.table_name,
    #                   table_id=presult.table_id,
    #                   table_kind=presult.table_kind,
    #                   columns=presult.columns,
    #                   raw_rows=presult.raw_rows)
    return rows.primary_results

app.mount("/", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    # asyncio.run(sample())
    import uvicorn
    uvicorn.run(app=app)
