import { Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider, useAuth } from './auth';
import Layout from './components/Layout';
import Login from './pages/Login';
import Queue from './pages/Queue';
import Add from './pages/Add';
import Problems from './pages/Problems';
import Dashboard from './pages/Dashboard';
import Settings from './pages/Settings';
import History from './pages/History';

function Gate() {
  const { role, loading } = useAuth();
  if (loading) return <div className="loading">Loading…</div>;
  if (role === 'anonymous') return <Login />;
  const isOwner = role === 'owner';
  return (
    <Routes>
      <Route path="/share/:token" element={<Navigate to="/" replace />} />
      <Route path="/" element={<Layout />}>
        <Route index element={<Queue />} />
        <Route path="problems" element={<Problems />} />
        <Route path="dashboard" element={<Dashboard />} />
        {isOwner && <Route path="add" element={<Add />} />}
        {isOwner && <Route path="settings" element={<Settings />} />}
        {isOwner && <Route path="history" element={<History />} />}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Gate />
    </AuthProvider>
  );
}
