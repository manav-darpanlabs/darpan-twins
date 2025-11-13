import { jsx as _jsx } from "react/jsx-runtime";
import React from 'react';
import ReactDOM from 'react-dom/client';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import './styles.css';
import ExperimentForm from './routes/ExperimentForm';
import RunProgress from './routes/RunProgress';
import ResultsView from './routes/ResultsView';
const router = createBrowserRouter([
    { path: '/', element: _jsx(ExperimentForm, {}) },
    { path: '/run/:id', element: _jsx(RunProgress, {}) },
    { path: '/results/:id', element: _jsx(ResultsView, {}) },
]);
ReactDOM.createRoot(document.getElementById('root')).render(_jsx(React.StrictMode, { children: _jsx(RouterProvider, { router: router }) }));
