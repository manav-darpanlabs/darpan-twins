import React from 'react'
import ReactDOM from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import './styles.css'
import ExperimentForm from './routes/ExperimentForm'
import RunProgress from './routes/RunProgress'
import ResultsView from './routes/ResultsView'

const router = createBrowserRouter([
  { path: '/', element: <ExperimentForm /> },
  { path: '/run/:id', element: <RunProgress /> },
  { path: '/results/:id', element: <ResultsView /> },
])

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>
)

