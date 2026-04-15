/**
 * Navbar - Navigation bar component with glassmorphism effect.
 */
import Link from 'next/link';
import { useRouter } from 'next/router';

export default function Navbar() {
  const router = useRouter();

  const links = [
    { href: '/', label: '📤 Cargar' },
    { href: '/datasets', label: '📊 Datasets' },
    { href: '/analysis', label: '🔬 Análisis' },
    { href: '/fused', label: '📦 Fusionados' },
  ];

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <Link href="/" className="navbar-brand">
          <div className="navbar-logo">⚡</div>
          <span className="navbar-title">CSV Analytics Platform</span>
        </Link>
        <ul className="navbar-links">
          {links.map(link => (
            <li key={link.href}>
              <Link
                href={link.href}
                className={router.pathname === link.href ? 'active' : ''}
              >
                {link.label}
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  );
}
