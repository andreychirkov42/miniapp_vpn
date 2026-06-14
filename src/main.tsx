import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import { initTheme } from './lib/theme'
import './index.css'

// До первого рендера — чтобы не было вспышки светлой темы на тёмных устройствах.
initTheme()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
