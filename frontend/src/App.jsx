import React, { useState } from 'react';
import SearchHeader from './components/SearchHeader';
import SearchBar from './components/SearchBar';
import ProviderStatusBadges from './components/ProviderStatusBadges';
import ResultList from './components/ResultList';
import Pagination from './components/Pagination';
import Analytics from './components/Analytics';

const App = () => {
    const [currentView, setCurrentView] = useState('search');
    
    const [query, setQuery] = useState('');
    const [filters, setFilters] = useState({
        year_min: '',
        year_max: '',
        open_access_only: false
    });
    
    // Client-side filtering & sorting state
    const [selectedSources, setSelectedSources] = useState([]);
    const [sortBy, setSortBy] = useState('relevance'); // 'relevance', 'newest', 'citations'
    
    // State for fetching and all 100 results
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [allResults, setAllResults] = useState([]);
    const [searchMetadata, setSearchMetadata] = useState(null);
    
    // Local pagination state
    const [currentPage, setCurrentPage] = useState(1);
    const perPage = 10;

    // Reset pagination when filters or sort changes
    React.useEffect(() => {
        setCurrentPage(1);
    }, [selectedSources, sortBy]);

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
        setSelectedSources([]); // Reset source filters on new search

        try {
            const params = new URLSearchParams({
                q: query,
                page: 1,
                per_page: 100 // Fetch up to 100 items at once
            });

            if (filters.year_min) params.append('year_min', filters.year_min);
            if (filters.year_max) params.append('year_max', filters.year_max);
            if (filters.open_access_only) params.append('open_access_only', 'true');

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

    // Client-side processing: Filter -> Sort -> Paginate
    let processedResults = [...allResults];

    // 1. Filter by selected sources
    if (selectedSources.length > 0) {
        processedResults = processedResults.filter(r => selectedSources.includes(r.source));
    }

    // 2. Sort results
    processedResults.sort((a, b) => {
        if (sortBy === 'newest') {
            const yearA = a.publication_year || 0;
            const yearB = b.publication_year || 0;
            return yearB - yearA;
        } else if (sortBy === 'citations') {
            const citeA = a.cited_by_count || 0;
            const citeB = b.cited_by_count || 0;
            return citeB - citeA;
        }
        // Default: relevance
        return (b.relevance_score || 0) - (a.relevance_score || 0);
    });

    // 3. Calculate pagination slice
    const totalItems = processedResults.length;
    const totalPages = Math.ceil(totalItems / perPage);
    const startIndex = (currentPage - 1) * perPage;
    const currentResults = processedResults.slice(startIndex, startIndex + perPage);

    // Derived available sources from results for the filter UI
    const availableSources = [...new Set(allResults.map(r => r.source))].filter(Boolean).sort();

    return (
        <>
            <SearchHeader currentView={currentView} setCurrentView={setCurrentView} />
            
            {currentView === 'analytics' ? (
                <Analytics />
            ) : (
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
                        availableSources={availableSources}
                        selectedSources={selectedSources}
                        setSelectedSources={setSelectedSources}
                        sortBy={sortBy}
                        setSortBy={setSortBy}
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
                                    <strong>{searchMetadata.total_results}</strong> total matches in <strong>{searchMetadata.search_time}s</strong> (showing top {allResults.length})
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
                                {processedResults.length > 0 ? (
                                    <>
                                        <ResultList results={currentResults} />
                                        <Pagination 
                                            currentPage={currentPage} 
                                            totalPages={totalPages} 
                                            setCurrentPage={setCurrentPage} 
                                        />
                                    </>
                                ) : (
                                    <div className="empty-state">
                                        <h2>No results found for current filters</h2>
                                        <p>Try selecting different sources.</p>
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                </main>
            )}
        </>
    );
};

export default App;