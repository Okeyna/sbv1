import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../useAuth';

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/">StudyBuddy</Link>
      </div>
      <div className="navbar-links">
        {user ? (
          <>
            <span className="user-email">{user.email}</span>
            <button onClick={handleLogout} className="btn-logout">
              Logout
            </button>
          </>
        ) : (
          <>
            <Link to="/login" className="btn-login">Login</Link>
            <Link to="/register" className="btn-register">Register</Link>
          </>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
