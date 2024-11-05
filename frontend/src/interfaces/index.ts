export interface IMessage {
    role: string
    content: string
}

export interface TableSchema {
    ColumnName: string
    DataType: string
}


export interface TableInfo {
    TableName: string
    Schema: TableSchema[]
}


export interface DatabaseTree {
    DatabaseName: string
    Tables: TableInfo[]
}

export interface ITree {
    DatabasesTree: DatabaseTree[]
    IsCached?: boolean
}

export interface IPrimaryResults {
    table_name: string
    table_id: string
    table_kind: string
    columns: {
        column_name: string
        column_type: string
        ordinal: number
    }[],
    raw_rows: any[][]
}