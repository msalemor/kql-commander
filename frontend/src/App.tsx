import { useState } from 'react'
// import reactLogo from './assets/react.svg'
// import viteLogo from '/vite.svg'
// import './App.css'

const Default_Settings = {
  system_prompt: "You are an AI that can help generate KQL queries.",
  schema: "storm_events:\nstate,string\nevent_name,string\nstart_date,datetime\n",
  prompt: "Generate a KQL query to find all the funnel clouds in Florida in 2024?"
}

function App() {
  const [settings, setSettings] = useState(Default_Settings)
  //const [count, setCount] = useState(0)

  return (
    <>
      <header className="h-[40px] flex items-center bg-slate-950 text-white">
        <h2 className="text-lg font-bold mx-2 p-0">KQL Commander</h2>
      </header>
      <section className="flex h-[calc(100vh-40px-35px)]">
        <aside className="w-[250px] bg-slate-50 flex flex-col overflow-auto p-3">
          Databases
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
              <textarea className='h-full resize-none outline-none border p-1' />
            </div>
          </div>
          <section className="space-x-2 m-2">
            <button className="bg-blue-600 text-white p-2">Process</button>
            <button className="bg-blue-600 text-white p-2">Execute</button>
          </section>
          <label className='uppercase font-semibold'>Results</label>
          <div className="h-full bg-slate-200"></div>
        </section>
      </section>

      <footer className="h-[35px] flex items-center">
        <div>Hello</div>
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
