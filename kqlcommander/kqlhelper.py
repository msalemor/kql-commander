import asyncio
from datetime import datetime
import logging

from azure.kusto.data import KustoConnectionStringBuilder
from azure.kusto.data.aio import KustoClient

from cacheservice import load_key, save_key
from settings import get_settings_instance
from models import Database, DatabaseTableInfo, DatabaseTree, Table, TableInfo, TableSchema, Tree


settings = get_settings_instance()
kcsb = KustoConnectionStringBuilder.with_az_cli_authentication(
    settings.cluster)


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


async def kql_databases():
    db = ''
    query = ".show databases"
    rows = await exec_query(db, query)
    list = [Database(DatabaseName=row[0]) for row in rows.primary_results[0]]
    list.sort(key=lambda x: x.DatabaseName)
    return list


async def kql_tables(db: str):
    query = ".show tables"
    rows = await exec_query(db, query)
    list = [Table(TableName=row[0]) for row in rows.primary_results[0]]
    list.sort(key=lambda x: x.TableName)
    return list


async def kql_table_schema(db: str = 'ContosoSales', table_name='Customers'):
    query = f"{table_name} | getschema"
    rows = await exec_query(db, query)
    list = []
    for row in rows.primary_results[0]:
        list.append(TableSchema(ColumnName=row[0], DataType=row[3]))
    list.sort(key=lambda x: x.ColumnName)
    return list


async def get_dbschema_info(db: str = 'ContosoSales', table_name='Customers'):
    query = f"{table_name} | getschema"
    rows = await exec_query(db, query)
    list = []
    for row in rows.primary_results[0]:
        list.append(TableSchema(ColumnName=row[0], DataType=row[3]))
    list.sort(key=lambda x: x.ColumnName)
    return DatabaseTableInfo(DatabaseName=db, TableName=table_name, Schema=list)


async def get_schema_info(db: str = 'ContosoSales', table_name='Customers'):
    query = f"{table_name} | getschema"
    rows = await exec_query(db, query)
    list = []
    for row in rows.primary_results[0]:
        list.append(TableSchema(ColumnName=row[0], DataType=row[3]))
    list.sort(key=lambda x: x.ColumnName)
    return TableInfo(TableName=table_name, Schema=list)


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


async def kql_tree():
    cache_data = await load_key('./cache.dat', 'tree')
    if cache_data is None:
        databases = await kql_databases()
        
        # Create tasks for processing each database
        db_tasks = []
        for db in databases:
            db_tasks.append(process_database(db))
        
        # Wait for all database processing tasks to complete
        db_results = await asyncio.gather(*db_tasks)
        
        tree = Tree(DatabasesTree=db_results)
        await save_key('./cache.dat', 'tree', tree)
        return tree
    else:
        return cache_data

async def process_database(db):
    print("Processing database", db.DatabaseName)
    tables = await kql_tables(db.DatabaseName)
    
    # Create tasks for processing each table
    table_tasks = []
    for table in tables:
        table_tasks.append(process_table(db.DatabaseName, table))
    
    # Wait for all table processing tasks to complete
    table_list = await asyncio.gather(*table_tasks)
    
    return DatabaseTree(DatabaseName=db.DatabaseName, Tables=table_list)

async def process_table(db_name, table):
    print("Processing table:", table.TableName)
    table_info = await get_schema_info(db_name, table.TableName)
    return table_info

async def get_data():
    async with KustoClient(kcsb) as client:
        db = "ContosoSales"
        query = "Customers | take 10"

        response = await client.execute(db, query)
        print_rows(response)


async def sample():
    databases = await kql_databases()
    tables = await kql_tables(databases[0])
    schema = await kql_table_schema(databases[0], tables[0])
    # await get_data()
    # await get_schema()
