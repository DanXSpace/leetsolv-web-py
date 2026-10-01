import { useState } from 'react';
import { api } from '../api';

export default function Login() {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');

  async function login() {
    setBusy(true);
    setErr('');
    try {
      const { authorize_url } = await api.loginUrl();
      window.location.href = authorize_url;
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'login failed');
      setBusy(false);
    }
  }

  return (
    <div className="login-wrap">
      <div className="login-card">
        <h1 className="brand-lg">leetsolv</h1>
        <p className="sub">Spaced repetition for LeetCode.</p>
        {err && <p className="error">{err}</p>}
        <button className="primary big" onClick={login} disabled={busy}>
          {busy ? 'Redirecting…' : 'Continue with GitHub'}
        </button>
      </div>
    </div>
  );
}
