import React from 'react';

const SearchBar = ({ query, setQuery, handleSearch, loading, filters, setFilters }) => {
    const handleKeyDown = (e) => {
        if (e.key === 'Enter') {
            handleSearch();
        }
    };

    return (
        <section className="search-section">
            <div className="search-box">
                <input 
                    type="text" 
                    className="search-input" 
                    placeholder="Search academic papers, books, primary sources..." 
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={handleKeyDown}
                />
                <button className="search-btn" onClick={handleSearch} disabled={loading}>
                    {loading ? 'Searching...' : (
                        <>
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <circle cx="11" cy="11" r="8"></circle>
                                <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                            </svg>
                            Search
                        </>
                    )}
                </button>
            </div>
            
            <div className="filters">
                <div className="filter-group">
                    <label>Min Year</label>
                    <input 
                        type="number" 
                        placeholder="e.g. 2020" 
                        min="1900" 
                        max="2026"
                        value={filters.year_min}
                        onChange={(e) => setFilters({ ...filters, year_min: e.target.value })}
                    />
                </div>
                <div className="filter-group">
                    <label>Max Year</label>
                    <input 
                        type="number" 
                        placeholder="e.g. 2025" 
                        min="1900" 
                        max="2026"
                        value={filters.year_max}
                        onChange={(e) => setFilters({ ...filters, year_max: e.target.value })}
                    />
                </div>
                <label className="checkbox-label" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <input 
                        type="checkbox" 
                        checked={filters.open_access_only}
                        onChange={(e) => setFilters({ ...filters, open_access_only: e.target.checked })}
                    />
                    Open Access Only
                </label>
            </div>
        </section>
    );
};

export default SearchBar;