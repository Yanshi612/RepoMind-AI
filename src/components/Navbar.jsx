import { Link } from 'react-router-dom';

const Navbar = () => {
  return (
    <nav
      className="sticky top-0 z-50 w-full px-8 py-4 flex justify-between items-center"
      style={{
        background: 'rgba(7, 8, 15, 0.85)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.07)',
      }}
    >
      {/* Logo */}
      <Link to="/" className="flex items-center gap-2.5">
        <div
          className="w-7 h-7 rounded-lg flex-shrink-0"
          style={{
            background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%)',
          }}
        />
        <span className="text-white font-bold text-lg leading-none">
          RepoMind
        </span>
        <span className="gradient-text font-bold text-lg leading-none">AI</span>
      </Link>

      {/* Nav Links */}
      <div className="flex items-center space-x-6">
        <Link
          to="/"
          className="text-sm text-gray-400 hover:text-white transition-colors"
        >
          Home
        </Link>
        <Link
          to="/dashboard"
          className="text-sm text-gray-400 hover:text-white transition-colors"
        >
          Dashboard
        </Link>
        <Link
          to="/repository"
          className="text-sm text-gray-400 hover:text-white transition-colors"
        >
          Repository
        </Link>
        <Link
          to="/analysis"
          className="text-sm text-gray-400 hover:text-white transition-colors"
        >
          Analysis
        </Link>

        {/* CTA Button */}
        <Link
          to="/repository"
          className="px-4 py-2 rounded-lg text-sm font-semibold text-white hover:opacity-90 transition-opacity"
          style={{
            background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
          }}
        >
          Get Started
        </Link>
      </div>
    </nav>
  );
};

export default Navbar;