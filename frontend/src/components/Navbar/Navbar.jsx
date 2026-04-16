import { useState, useEffect } from 'react'
import { Menu, X, Mic, LogOut, User } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import './Navbar.css'

const navLinks = [
  { label: 'About',    href: '#about' },
  { label: 'Features', href: '#features' },
  { label: 'Languages',href: '#languages' },
  { label: 'How It Works', href: '#how-it-works' },
]

export default function Navbar() {
  const [scrolled,    setScrolled]    = useState(false)
  const [menuOpen,    setMenuOpen]    = useState(false)
  const { user, logout, isAuthenticated } = useAuth()

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40)
    window.addEventListener('scroll', onScroll)
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const handleLogout = () => {
    logout()
    window.location.reload() // Refresh to show auth screen
  }

  return (
    <header className={`navbar ${scrolled ? 'navbar--scrolled' : ''}`}>
      <div className="container navbar__inner">

        {/* Logo */}
        <a href="#hero" className="navbar__logo">
          <span className="navbar__logo-icon"><Mic size={20} /></span>
          <span className="navbar__logo-text">
            Kisaan<span className="highlight">Vaani</span>
          </span>
        </a>

        {/* Desktop links */}
        <nav className="navbar__links">
          {navLinks.map(l => (
            <a key={l.label} href={l.href} className="navbar__link">{l.label}</a>
          ))}
        </nav>

        {/* CTA & User */}
        <div className="navbar__cta">
          {isAuthenticated && user && (
            <div className="navbar__user">
              <span className="navbar__user-name">
                <User size={14} /> {user.name}
              </span>
              <button onClick={handleLogout} className="navbar__logout" title="Logout">
                <LogOut size={16} />
              </button>
            </div>
          )}
          <a href="#hero" className="btn-premium navbar__btn">
            <Mic size={16} /> Try Now
          </a>
          <button
            className="navbar__hamburger"
            onClick={() => setMenuOpen(o => !o)}
            aria-label="Toggle menu"
          >
            {menuOpen ? <X size={28} /> : <Menu size={28} />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="navbar__mobile animate-reveal">
          <div className="navbar__mobile-header">
            <button onClick={() => setMenuOpen(false)} variant="ghost">Close <X size={18} /></button>
          </div>
          
          {isAuthenticated && user && (
            <div className="navbar__user">
              <User size={16} /> {user.name}
            </div>
          )}

          {navLinks.map(l => (
            <a
              key={l.label}
              href={l.href}
              className="navbar__mobile-link"
              onClick={() => setMenuOpen(false)}
            >
              {l.label}
            </a>
          ))}
          
          <a href="#hero" className="btn-premium" onClick={() => setMenuOpen(false)}>
            <Mic size={18} /> Try Now
          </a>

          {isAuthenticated && (
            <button onClick={handleLogout} className="btn-outline-premium">
              <LogOut size={18} /> Logout
            </button>
          )}
        </div>
      )}
    </header>
  )
}
