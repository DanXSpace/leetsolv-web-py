import { NavLink, Outlet } from 'react-router-dom';
import { api } from '../api';
import { useAuth } from '../auth';

export default function Layout() {
  const { role, login } = useAuth();
  const isOwner = role === 'owner';

  async function logout() {
    try {
      await api.logout();
    } catch {
      // ignore
    }
    document.cookie = 'leetsolv_session=; Max-Age=0; path=/';
    window.location.href = '/';
  }

  const linkClass = ({ isActive }: { isActive: boolean }) => (isActive ? 'active' : '');

  return (
    <div className="app">
      <header className="topbar">
        <span className="brand">leetsolv</span>
        <nav className="nav">
          <NavLink to="/" end className={linkClass}>
            Review
          </NavLink>
          <NavLink to="/problems" className={linkClass}>
            Problems
          </NavLink>
          <NavLink to="/dashboard" className={linkClass}>
            Dashboard
          </NavLink>
          {isOwner && (
            <NavLink to="/add" className={linkClass}>
              Add
            </NavLink>
          )}
          {isOwner && (
            <NavLink to="/history" className={linkClass}>
              History
            </NavLink>
          )}
          {isOwner && (
            <NavLink to="/settings" className={linkClass}>
              Settings
            </NavLink>
          )}
        </nav>
        <div className="spacer" />
        {isOwner ? (
          <div className="who">
            <span className="login">{login}</span>
            <button className="link" onClick={logout}>
              Log out
            </button>
          </div>
        ) : (
          <span className="badge badge-mentor">Read-only</span>
        )}
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
