import React, { useState } from 'react';
import { getAPA, getMLA, getChicago, getBibTeX } from '../utils/citations';

const getSourceBadgeClass = (source) => {
    const sourceStr = (source || '').toLowerCase();
    if (sourceStr.includes('openalex')) return 'badge-source-openalex';
    if (sourceStr.includes('crossref')) return 'badge-source-crossref';
    if (sourceStr.includes('arxiv') && !sourceStr.includes('biorxiv') && !sourceStr.includes('medrxiv')) return 'badge-source-arxiv';
    if (sourceStr.includes('doaj')) return 'badge-source-doaj';
    if (sourceStr.includes('biorxiv')) return 'badge-source-biorxiv';
    if (sourceStr.includes('medrxiv')) return 'badge-source-medrxiv';
    if (sourceStr.includes('pmc')) return 'badge-source-pmc';
    if (sourceStr.includes('textbook')) return 'badge-source-textbook';
    return '';
};

const ResultCard = ({ result }) => {
    const authors = result.authors?.map(a => a.name).join(', ') || 'Unknown authors';
    const year = result.publication_year || 'N/A';
    const citations = result.cited_by_count || 0;
    const abstract = result.abstract ? result.abstract.substring(0, 300) + '...' : 'No abstract available';

    return (
        <div className="result-card">
            <div className="result-title">
                {result.url ? (
                    <a href={result.url} target="_blank" rel="noopener noreferrer">
                        {result.title}
                    </a>
                ) : (
                    result.title
                )}
            </div>
            <div className="result-meta">
                <span className="meta-item">👤 {authors}</span>
                <span className="meta-item">📅 {year}</span>
                <span className="meta-item">
                    <span className={`badge badge-source ${getSourceBadgeClass(result.source)}`}>
                        {result.source}
                    </span>
                </span>
                {result.is_open_access && (
                    <span className="badge badge-oa">🔓 OPEN ACCESS</span>
                )}
                <span className="badge badge-citations">📊 {citations} citations</span>
                <span className="badge badge-score">⭐ {result.relevance_score?.toFixed(1) || '0.0'}</span>
            </div>
            <div className="result-abstract">{abstract}</div>
            <div className="result-actions">
                {result.url && (
                    <a href={result.url} target="_blank" rel="noopener noreferrer" className="btn-link">
                        View Article <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M6 11L10 7L6 3" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/></svg>
                    </a>
                )}
                {result.open_access_url && (
                    <a href={result.open_access_url} target="_blank" rel="noopener noreferrer" className="btn-link">
                        Open Access PDF <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M6 11L10 7L6 3" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/></svg>
                    </a>
                )}
                {result.doi && (
                    <a href={`https://doi.org/${result.doi.replace('https://doi.org/', '')}`} target="_blank" rel="noopener noreferrer" className="btn-link-secondary">
                        DOI
                    </a>
                )}
            </div>
        </div>
    );
};

export default ResultCard;