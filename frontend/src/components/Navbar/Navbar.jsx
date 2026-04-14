import { useState, useEffect } from 'react'
import { Menu, X, Mic } from 'lucide-react'
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

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40)
    window.addEventListener('scroll', onScroll)
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

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

        {/* CTA */}
        <div className="navbar__cta">
          <a href="#hero" className="btn-primary navbar__btn">
            <Mic size={16} /> Try Now
          </a>
          <button
            className="navbar__hamburger"
            onClick={() => setMenuOpen(o => !o)}
            aria-label="Toggle menu"
          >
            {menuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="navbar__mobile">
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
          <a href="#hero" className="btn-primary" onClick={() => setMenuOpen(false)}>
            <Mic size={16} /> Try Now
          </a>
        </div>
      )}
    </header>
  )
}
