/** Mount the browser application with shared query caching, routing, and translations. */
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router';
import App from './App';
import './i18n';
import './styles/app.css';

const queryClient = new QueryClient();
const root = document.getElementById('root');
if (!root) throw new Error('Application root element is missing.');

createRoot(root).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
