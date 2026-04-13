import React from 'react';

const SearchBar = ({ 
    query, setQuery, handleSearch, loading, 
    filters, setFilters,
    availableSources, selectedSources, setSelectedSources,
    sortBy, setSortBy
}) => {
    const handleKeyDown = (e) => {
        if (e.key === 'Enter') {
            handleSearch();
        }
    };

    const toggleSource = (source) => {
        if (selectedSources.includes(source)) {
            setSelectedSources(selectedSources.filter(s => s !== source));
        } else {
            setSelectedSources([...selectedSources, source]);
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
            
            <div className="filters" style={{ display: 'flex', flexWrap: 'wrap', gap: '20px', alignItems: 'flex-end' }}>
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
                <label className="checkbox-label" style={{ display: 'flex', alignItems: 'center', gap: '8px', paddingBottom: '10px' }}>
                    <input 
                        type="checkbox" 
                        checked={filters.open_access_only}
                        onChange={(e) => setFilters({ ...filters, open_access_only: e.target.checked })}
                    />
                    Open Access Only
                </label>

                {availableSources && availableSources.length > 0 && (
                    <div className="filter-group" style={{ marginLeft: 'auto' }}>
                        <label>Sort By</label>
                        <select 
                            value={sortBy} 
                            onChange={(e) => setSortBy(e.target.value)}
                            style={{
                                padding: '10px',
                                background: 'rgba(255, 255, 255, 0.1)',
                                border: '1px solid rgba(255, 255, 255, 0.2)',
                                borderRadius: '4px',
                                color: '#fff',
                                outline: 'none'
                            }}
                        >
                            <option value="relevance" style={{color: '#000'}}>Relevance</option>
                            <option value="newest" style={{color: '#000'}}>Newest First</option>
                            <option value="citations" style={{color: '#000'}}>Most Cited</option>
                        </select>
                    </div>
                )}
            </div>

            {availableSources && availableSources.length > 0 && (
                <div style={{ marginTop: '20px', paddingTop: '15px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                    <label style={{ display: 'block', marginBottom: '10px', fontSize: '0.9em', color: 'rgba(255,255,255,0.7)' }}>Filter by Source:</label>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
                        {availableSources.map(source => (
                            <label key={source} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85em', cursor: 'pointer' }}>
                                <input 
                                    type="checkbox" 
                                    checked={selectedSources.includes(source)}
                                    onChange={() => toggleSource(source)}
                                />
                                {source}
                            </label>
                        ))}
                    </div>
                </div>
            )}
        </section>
    );
};

export default SearchBar;