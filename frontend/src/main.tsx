import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { setShareToken } from './api';
import './index.css';

function initShareToken(): string | null {
  const m = window.location.pathname.match(/^\/share\/([^/]+)/);
  if (m) {
    localStorage.setItem('shareToken', m[1]);
    return m[1];
  }
  return localStorage.getItem('shareToken');
}

setShareToken(initShareToken());

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
);
