import { NavLink, Outlet } from 'react-router-dom';
import { api, setShareToken } from '../api';
import { useAuth } from '../auth';

export default function Layout() {
  const { role, login, refresh } = useAuth();
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

  async function signIn() {
    // Leave the read-only mentor view and return to the owner login screen.
    localStorage.removeItem('shareToken');
    setShareToken(null);
    await refresh();
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
          <div className="who">
            <span className="badge badge-mentor">Read-only</span>
            <button className="link" onClick={signIn}>
              Sign in
            </button>
          </div>
        )}
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
