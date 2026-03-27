import React from 'react';

const Pagination = ({ currentPage, totalPages, setCurrentPage }) => {
    if (totalPages <= 1) return null;

    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);

    const pages = [];
    for (let i = startPage; i <= endPage; i++) {
        pages.push(i);
    }

    return (
        <div className="pagination">
            <button 
                className="page-btn" 
                onClick={() => setCurrentPage(currentPage - 1)} 
                disabled={currentPage === 1}
            >
                Previous
            </button>
            
            {startPage > 1 && (
                <>
                    <button className="page-btn" onClick={() => setCurrentPage(1)}>1</button>
                    {startPage > 2 && <span style={{ padding: '12px', color: 'rgba(255,255,255,0.5)' }}>...</span>}
                </>
            )}

            {pages.map(page => (
                <button 
                    key={page}
                    className={`page-btn ${page === currentPage ? 'active' : ''}`}
                    onClick={() => setCurrentPage(page)}
                >
                    {page}
                </button>
            ))}

            {endPage < totalPages && (
                <>
                    {endPage < totalPages - 1 && <span style={{ padding: '12px', color: 'rgba(255,255,255,0.5)' }}>...</span>}
                    <button className="page-btn" onClick={() => setCurrentPage(totalPages)}>{totalPages}</button>
                </>
            )}

            <button 
                className="page-btn" 
                onClick={() => setCurrentPage(currentPage + 1)} 
                disabled={currentPage === totalPages}
            >
                Next
            </button>
        </div>
    );
};

export default Pagination;