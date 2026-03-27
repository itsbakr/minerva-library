import React from 'react';

const SearchHeader = () => {
    return (
        <header className="header">
            <div className="logo-section">
                <img src="https://upload.wikimedia.org/wikipedia/commons/e/e0/Minerva_University_logo.png" alt="Minerva University" style={{ filter: 'brightness(0) invert(1)' }} />
                <h2 style={{ fontSize: '1.2em', fontWeight: '500', letterSpacing: '1px' }}>LIBRARY</h2>
            </div>
            <nav className="nav-links">
                <a href="#">About</a>
                <a href="#">Advanced Search</a>
                <a href="#">Help</a>
            </nav>
        </header>
    );
};

export default SearchHeader;