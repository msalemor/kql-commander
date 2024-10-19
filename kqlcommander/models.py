from typing import Any, List
from pydantic import BaseModel


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


class DatabaseTableInfo(BaseModel):
    DatabaseName: str
    TableName: str
    Schema: List[TableSchema]
