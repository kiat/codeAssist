import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import { Button } from 'antd'
import axios from 'axios'

const baseURL = "http://localhost:5000"

function App() {
  const [count, setCount] = useState(0)
  const [message, setMessage] = useState("Waiting for message")

  return (
    <>
      <div>
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
      </p>
      <div>
        <Button 
          type="primary" 
          onClick={() => axios.get(baseURL).then((response) => {
            setMessage(response.data);
          })}>Hello Allen</Button>
        <p>{message}</p>
      </div>
    </>
  )
}

export default App
