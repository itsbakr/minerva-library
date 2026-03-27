import React from 'react';
import ResultCard from './ResultCard';

const ResultList = ({ results }) => {
    if (!results || results.length === 0) {
        return (
            <div className="empty-state">
                <h2>No results found</h2>
                <p>Try adjusting your search query or filters</p>
            </div>
        );
    }

    return (
        <div>
            {results.map((result, index) => (
                <ResultCard key={result.id || index} result={result} />
            ))}
        </div>
    );
};

export default ResultList;