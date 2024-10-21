import asyncio
from datetime import datetime
import logging

from azure.kusto.data import KustoConnectionStringBuilder
from azure.kusto.data.aio import KustoClient

from cacheservice import cache, get_cache
from models import Database, DatabaseTableInfo, DatabaseTree, Table, TableInfo, TableSchema, Tree


KUSTO_CLUSTER = "https://help.kusto.windows.net/"
kcsb = KustoConnectionStringBuilder.with_az_cli_authentication(KUSTO_CLUSTER)


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
        list.append(TableSchema(ColumnName=row[0], DataType=row[2]))
    list.sort(key=lambda x: x.ColumnName)
    return list


async def get_dbschema_info(db: str = 'ContosoSales', table_name='Customers'):
    query = f"{table_name} | getschema"
    rows = await exec_query(db, query)
    list = []
    for row in rows.primary_results[0]:
        list.append(TableSchema(ColumnName=row[0], DataType=row[2]))
    list.sort(key=lambda x: x.ColumnName)
    return DatabaseTableInfo(DatabaseName=db, TableName=table_name, Schema=list)


async def get_schema_info(db: str = 'ContosoSales', table_name='Customers'):
    query = f"{table_name} | getschema"
    rows = await exec_query(db, query)
    list = []
    for row in rows.primary_results[0]:
        list.append(TableSchema(ColumnName=row[0], DataType=row[2]))
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
    cache_data = await get_cache('tree')
    if cache_data is None:
        # Databases
        list = []
        databases = await kql_databases()
        for db in databases:

            print("Processing database", db.DatabaseName)
            tables = await kql_tables(db.DatabaseName)
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
    databases = await kql_databases()
    tables = await kql_tables(databases[0])
    schema = await kql_table_schema(databases[0], tables[0])
    # await get_data()
    # await get_schema()
