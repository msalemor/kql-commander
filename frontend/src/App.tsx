import axios from 'axios'
import { useEffect, useState } from 'react'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import 'react-data-grid/lib/styles.css'
import DataGrid from 'react-data-grid'
// import reactLogo from './assets/react.svg'
// import viteLogo from '/vite.svg'
// import './App.css'

const Default_Settings = {
  system_prompt: `You are an AI that can help generate KQL queries. 

Use the following schema:
<SCHEMA>

Rule:
- Include the database name in the query in the format: database("databasename").tablename
- Provide an explanation for the command.
- Output in valid JSON format using the following format:
{
"query"://
"explanation"://
}
- No epilogue or prologue.
`,
  schema: "...retrieving",
  prompt: "List the first 10 customers in London?",
  completion: ""
}

const BASE_URL = import.meta.env.VITE_BASE_URL
const TREE_URL = BASE_URL + import.meta.env.VITE_TREE_URL
const CHAT_COMPLETION_URL = BASE_URL + import.meta.env.VITE_COMPLETION_URL
const EXECUTE_URL = BASE_URL + import.meta.env.VITE_EXECUTE_URL


interface IMessage {
  role: string
  content: string
}

interface TableSchema {
  ColumnName: string
  DataType: string
}


interface TableInfo {
  TableName: string
  Schema: TableSchema[]
}


interface DatabaseTree {
  DatabaseName: string
  Tables: TableInfo[]
}

interface Tree {
  DatabasesTree: DatabaseTree[]
}

export function getKQLQuery(completion: string) {
  const regex = /```kql\s*([\s\S]*?)\s*```/;
  const match = completion.match(regex);
  if (match && match[1]) {
    return match[1].trim();
  } else {
    console.log("No KQL query found.");
    return ""
  }
}

function App() {
  const [settings, setSettings] = useState(Default_Settings)
  const [tree, setTree] = useState<Tree>({ DatabasesTree: [] })
  const [showschema, setShowschema] = useState(true)
  const [columns, setColumns] = useState<any[]>([])
  const [rows, setRows] = useState<any[]>([])
  const [query, setQuery] = useState('')
  const [processing, setProcessing] = useState(false)

  const getTree = async () => {
    if (processing) return;
    try {
      setProcessing(true)
      //alert('test')
      const re = await axios.get<Tree>(TREE_URL)
      //console.info(JSON.stringify(re.data))
      setTree(re.data)

      const regex = /System./g;
      const json_data = JSON.stringify(re.data, null, 2).replace(regex, "")
      settings.schema = json_data
      setSettings({ ...settings })
      //alert(tree)
    } catch (e) {
      console.error(e)
    } finally {
      setProcessing(false)
    }

  }

  const getChatCompletion = async () => {
    if (processing) return;
    try {
      setProcessing(true)
      const messages = [
        {
          role: 'system',
          content: settings.system_prompt.replace('<SCHEMA>', settings.schema)
        },
        {
          role: 'user',
          content: settings.prompt
        }
      ]
      const payload = {
        messages,
        temperature: 0.1,
        chat_model: 'gpt-4o'
      }

      const re = await axios.post(CHAT_COMPLETION_URL, payload)
      //settings.completion = re.data.content
      const json_data: any = JSON.parse(re.data.content)
      setSettings({ ...settings, completion: json_data.query + "\n\n" + json_data.explanation })
      setQuery(json_data.query)

      console.info("query:\n" + json_data.query)
      if (json_data.query)
        await execute()
    } catch (e) {
      console.info(e)
    } finally {
      setProcessing(false)
    }
  }

  interface PrimaryResults {
    table_name: string,
    table_id: number,
    tabke_kind: string,
    columns: {
      column_name: string,
      column_type: string,
      ordinal: number
    }[],
    raw_rows: any[][]
  }

  const execute = async () => {
    try {
      setColumns([])
      setRows([])
      const payload = { db: '', query }
      const re = await axios.post<PrimaryResults>(EXECUTE_URL, payload)
      let grid_data = re.data
      if (grid_data && grid_data.columns && grid_data.columns.length > 0) {
        //console.info(JSON.stringify(grid_data.columns, null, 2))
        const columns = grid_data.columns.map(x => ({ key: x.column_name, name: x.column_name, resizable: true, width: 100 }))
        //console.info(JSON.stringify(columns, null, 2))
        const rows: any = []
        grid_data.raw_rows.map((x, idx) => {
          let row: any = {}
          row['id'] = idx
          for (let i = 0; i < grid_data.columns.length; i++) {
            row[grid_data.columns[i].column_name] = x[i]
          }
          rows.push(row)
        })
        //console.info(JSON.stringify(rows, null, 2))
        setColumns(columns)
        setRows(rows)
      }
    }
    catch (e) {
      console.error(e)
    }
  }

  useEffect(() => {
    if (tree)
      getTree()

    console.info(JSON.stringify(tree))
  }, [])

  return (
    <>
      <header className="h-[40px] flex items-center bg-slate-950 text-white">
        <h2 className="text-lg font-bold mx-2 p-0">KQL Commander</h2>
      </header>
      <section className="flex h-[calc(100vh-40px-35px)]">
        <aside className="min-w-[350px] bg-slate-50 flex flex-col overflow-auto p-3">
          <span className="uppercase font-bold">Databases</span>
          <button
            className='bg-blue-600 text-white'
            onClick={() => setShowschema(!showschema)}
          >
            {showschema && <span>Hide Schema</span>}
            {!showschema && <span>Show Schema</span>}
          </button>
          <ul className='text-sm'>
            {tree.DatabasesTree.map((x, idx) => <li key={'db-' + idx}>
              {x.DatabaseName}
              <ul>
                {x.Tables.map(table => <li>
                  {table.TableName}
                  <ul>
                    {showschema && table.Schema.map(s => <li>{s.ColumnName}-{s.DataType.replace("System.", "")}</li>)}
                  </ul>
                </li>)}
              </ul>
            </li>)}
          </ul>
        </aside>
        <section className="w-full bg-slate-100 flex flex-col p-3">
          <div className='flex'>
            <div className='flex flex-col w-3/4'>
              <label className='uppercase font-semibold'>System Prompt</label>
              <textarea rows={3} className="p-1 resize-none outline-none border"
                onChange={(e) => {
                  setSettings((prevSettings) => ({ ...prevSettings, system_prompt: e.target.value }));
                }}
                value={settings.system_prompt}
              />
              <label className='uppercase font-semibold'>Schema</label>
              <textarea rows={8} className="p-1 resize-none outline-none border"
                onChange={(e) => {
                  setSettings((prevSettings) => ({ ...prevSettings, schema: e.target.value }));
                }}
                value={settings.schema}
              />
              <label className='uppercase font-semibold'>Prompt</label>
              <textarea rows={6} className="p-1 resize-none outline-none border"
                onChange={(e) => {
                  setSettings((prevSettings) => ({ ...prevSettings, prompt: e.target.value }));
                }}
                value={settings.prompt}
              />
            </div>
            <div className='w-1/4 flex flex-col mx-2'>
              <label className='uppercase font-semibold'>Completion</label>
              {/* <textarea className='h-full resize-none outline-none border p-1' 
              
              /> */}
              <div className='h-full bg-slate-800 text-white p-2 overflow-auto'>
                <Markdown className='' remarkPlugins={[remarkGfm]}>{settings.completion}</Markdown>
              </div>

            </div>
          </div>
          <section className="space-x-2 m-2">
            <button className="bg-blue-600 text-white p-2"
              onClick={getChatCompletion}
            >Process</button>
            <button className="bg-blue-600 text-white p-2"
              onClick={execute}
            >Execute</button>
          </section>
          <label className='uppercase font-semibold'>Results</label>

          <DataGrid columns={columns} rows={rows} className='h-full w-[calc(100vw-380px)]' />
        </section>
      </section>

      <footer className={"h-[35px] flex items-center " + (processing ? "bg-red-600 text-white" : "")}>
        <div>{processing && <span>Processing ...</span>}</div>
      </footer>
      {/* <div>
        <a href="https://vitejs.dev" target="_blank">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>Vite + React</h1>
      <div className="card">
        <button onClick={() => setCount((count) => count + 1)}>
          count is {count}
        </button>
        <p>
          Edit <code>src/App.tsx</code> and save to test HMR
        </p>
      </div>
      <p className="read-the-docs">
        Click on the Vite and React logos to learn more
      </p> */}
    </>
  )
}

export default App
