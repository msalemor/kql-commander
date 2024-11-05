import axios from 'axios'
import { useEffect, useState } from 'react'
import { FaSpinner } from 'react-icons/fa' // Import spinner icon
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import 'react-data-grid/lib/styles.css'
import DataGrid from 'react-data-grid'
import { IPrimaryResults, ITree } from './interfaces'
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
  const [tree, setTree] = useState<ITree>({ DatabasesTree: [] })
  const [showschema, setShowschema] = useState(true)
  const [columns, setColumns] = useState<any[]>([])
  const [rows, setRows] = useState<any[]>([])
  const [query, setQuery] = useState('')
  const [processingTree, setProcessingTree] = useState(false);
  const [processingChatCompletion, setProcessingChatCompletion] = useState(false);
  const [executing, setExecuting] = useState(false) // New state for execute button

  const getTree = async (use_cache: boolean = true) => {
    if (processingTree) return;
    try {
      setProcessingTree(true)
      const re = await axios.get<ITree>(`${TREE_URL}?use_cache=${use_cache}`)
      setTree(re.data)

      const regex = /System./g;
      const json_data = JSON.stringify(re.data, null, 2).replace(regex, "")
      settings.schema = json_data
      setSettings({ ...settings })

      if (use_cache && re.data.IsCached) {
        setProcessingTree(false); //We don't want the 'Processing...' footer when silently refreshing the tree
        const refresh = await axios.get<ITree>(`${TREE_URL}?use_cache=false`)
        const cleanedRefreshData = removeIsCached(refresh.data);
        const cleanedReData = removeIsCached(re.data);
        if (JSON.stringify(cleanedRefreshData) !== JSON.stringify(cleanedReData)) {
          console.info("Tree has been updated.")
          setTree(refresh.data)
        }
      }
    } catch (e) {
      console.error(e)
    } finally {
      setProcessingTree(false)
    }
  }

  const removeIsCached = (obj: ITree) => {
    const { IsCached, ...rest } = obj;
    return rest;
  };

  const getChatCompletion = async () => {
    setProcessingChatCompletion(true);
    try {
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
      const json_data: any = JSON.parse(re.data.content)
      setSettings({ ...settings, completion: json_data.query + "\n\n" + json_data.explanation })
      setQuery(json_data.query)

      if (json_data.query)
        await execute(json_data.query)
    } catch (e) {
      console.info(e)
    } finally {
      setProcessingChatCompletion(false);
    }
  }

  const execute = async (queryParam: string = query) => {
    setExecuting(true)
    try {
      setColumns([])
      setRows([])
      const payload = { db: '', query: queryParam }
      const re = await axios.post<IPrimaryResults>(EXECUTE_URL, payload)
      let grid_data = re.data
      if (grid_data && grid_data.columns && grid_data.columns.length > 0) {
        const columns = grid_data.columns.map(x => ({ key: x.column_name, name: x.column_name, resizable: true, width: 100 }))
        const rows: any = []
        grid_data.raw_rows.map((x, idx) => {
          let row: any = {}
          row['id'] = idx
          for (let i = 0; i < grid_data.columns.length; i++) {
            row[grid_data.columns[i].column_name] = x[i]
          }
          rows.push(row)
        })
        setColumns(columns)
        setRows(rows)
      }
    } catch (e) {
      console.error(e)
    } finally {
      setExecuting(false);
    }
  }

  useEffect(() => {
    if (tree)
      getTree()
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
            {tree.DatabasesTree.map((x, idx) => (
              <li key={'db-' + idx}>
                {x.DatabaseName}
                <ul>
                  {x.Tables.map((table, tableIdx) => (
                    <li key={'table-' + tableIdx}>
                      {table.TableName}
                      <ul>
                        {showschema && table.Schema.map((s, schemaIdx) => (
                          <li key={'schema-' + schemaIdx}>{s.ColumnName}-{s.DataType.replace("System.", "")}</li>
                        ))}
                      </ul>
                    </li>
                  ))}
                </ul>
              </li>
            ))}
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
              <div className='h-full bg-slate-800 text-white p-2 overflow-auto'>
                <Markdown className='' remarkPlugins={[remarkGfm]}>{settings.completion}</Markdown>
              </div>
            </div>
          </div>
          <section className="flex space-x-2 m-2">
            <button
              className={`p-2 flex items-center ${processingChatCompletion ? 'bg-gray-400' : 'bg-blue-600'} text-white`}
              onClick={getChatCompletion}
              disabled={processingChatCompletion}
            >
              {processingChatCompletion && <FaSpinner className="animate-spin mr-2" />}
              {processingChatCompletion ? 'Processing...' : 'Process'}
            </button>
            <button
              className={`p-2 flex items-center ${executing ? 'bg-gray-400' : 'bg-blue-600'} text-white`}
              onClick={() => execute()}
              disabled={executing}
            >
              {executing && <FaSpinner className="animate-spin mr-2" />}
              {executing ? 'Executing...' : 'Execute'}
            </button>
          </section>
          <label className='uppercase font-semibold'>Results</label>
          <DataGrid columns={columns} rows={rows} className='h-full w-[calc(100vw-380px)]' />
        </section>
      </section>
      <footer className={"h-[35px] flex items-center " + (processingTree ? "bg-red-600 text-white" : "")}>
        <div>{processingTree && <span>Processing ...</span>}</div>
      </footer>
    </>
  )
}

export default App
