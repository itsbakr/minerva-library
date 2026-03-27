import React, { useState } from 'react';
import SearchHeader from './components/SearchHeader';
import SearchBar from './components/SearchBar';
import ProviderStatusBadges from './components/ProviderStatusBadges';
import ResultList from './components/ResultList';
import Pagination from './components/Pagination';

const App = () => {
    const [query, setQuery] = useState('');
    const [filters, setFilters] = useState({
        year_min: '',
        year_max: '',
        open_access_only: false
    });
    
    // State for fetching and all 100 results
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [allResults, setAllResults] = useState([]);
    const [searchMetadata, setSearchMetadata] = useState(null);
    
    // Local pagination state
    const [currentPage, setCurrentPage] = useState(1);
    const perPage = 10;

    const handleSearch = async () => {
        if (!query.trim()) {
            setError('Please enter a search query');
            return;
        }

        setLoading(true);
        setError('');
        setAllResults([]);
        setSearchMetadata(null);
        setCurrentPage(1);

        try {
            const params = new URLSearchParams({
                q: query,
                page: 1,
                per_page: 100 // Fetch up to 100 items at once
            });

            if (filters.year_min) params.append('year_min', filters.year_min);
            if (filters.year_max) params.append('year_max', filters.year_max);
            if (filters.open_access_only) params.append('open_access_only', 'true');

            // Replace with your actual backend URL or leave relative if served from same domain
            const response = await fetch(`http://localhost:8000/api/search?${params.toString()}`);
            if (!response.ok) {
                throw new Error('Search failed: ' + response.statusText);
            }

            const data = await response.json();
            
            setAllResults(data.results || []);
            setSearchMetadata({
                total_results: data.total_results,
                search_time: data.search_time,
                databases_searched: data.databases_searched,
                provider_status: data.provider_status
            });

        } catch (err) {
            setError(err.message || 'An error occurred during search.');
        } finally {
            setLoading(false);
        }
    };

    // Calculate pagination slice
    const totalItems = allResults.length;
    const totalPages = Math.ceil(totalItems / perPage);
    const startIndex = (currentPage - 1) * perPage;
    const currentResults = allResults.slice(startIndex, startIndex + perPage);

    return (
        <>
            <SearchHeader />
            <main className="container">
                <div className="hero-section">
                    <h1>Academic Search</h1>
                    <p>Search millions of peer-reviewed articles, preprints, and open textbooks across multiple databases simultaneously.</p>
                </div>
                
                <SearchBar 
                    query={query} 
                    setQuery={setQuery} 
                    handleSearch={handleSearch} 
                    loading={loading}
                    filters={filters}
                    setFilters={setFilters}
                />

                {error && (
                    <div style={{ color: '#ef4444', textAlign: 'center', marginBottom: '20px' }}>
                        {error}
                    </div>
                )}

                <div id="resultsSection">
                    {searchMetadata && !loading && (
                        <div className="results-header">
                            <div className="results-info">
                                <strong>{searchMetadata.total_results}</strong> results found in <strong>{searchMetadata.search_time}s</strong>
                                {searchMetadata.provider_status ? (
                                    <ProviderStatusBadges providerStatus={searchMetadata.provider_status} />
                                ) : (
                                    <div className="databases-badge">
                                        {searchMetadata.databases_searched.map((db, i) => (
                                            <span key={i} className="db-badge">{db}</span>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {!loading && searchMetadata && (
                        <>
                            <ResultList results={currentResults} />
                            <Pagination 
                                currentPage={currentPage} 
                                totalPages={totalPages} 
                                setCurrentPage={setCurrentPage} 
                            />
                        </>
                    )}
                </div>
            </main>
        </>
    );
};

export default App;