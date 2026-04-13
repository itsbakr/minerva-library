import React from 'react';

const SearchHeader = ({ currentView, setCurrentView }) => {
    return (
        <header className="header">
            <div 
                className="logo-section" 
                onClick={() => setCurrentView('search')}
                style={{ cursor: 'pointer' }}
                title="Go to Home"
            >
                <img src="https://upload.wikimedia.org/wikipedia/commons/e/e0/Minerva_University_logo.png" alt="Minerva University" style={{ filter: 'brightness(0) invert(1)' }} />
                <h2 style={{ fontSize: '1.2em', fontWeight: '500', letterSpacing: '1px' }}>LIBRARY</h2>
            </div>
            <nav className="nav-links">
                <button 
                    onClick={() => setCurrentView('analytics')}
                    className={`btn-link ${currentView === 'analytics' ? 'active' : ''}`}
                    style={{ 
                        background: 'transparent', 
                        border: 'none', 
                        color: currentView === 'analytics' ? '#FFD700' : '#ffffff',
                        fontSize: '14px',
                        fontWeight: '500',
                        cursor: 'pointer',
                        padding: '8px 12px'
                    }}
                >
                    Analytics
                </button>
            </nav>
        </header>
    );
};

export default SearchHeader;