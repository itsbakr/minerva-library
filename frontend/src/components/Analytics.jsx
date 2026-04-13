import React, { useState, useEffect } from 'react';

const Analytics = () => {
    const [stats, setStats] = useState(null);
    const [history, setHistory] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchAnalytics = async () => {
            try {
                setLoading(true);
                // Fetch stats and history concurrently
                const [statsRes, historyRes] = await Promise.all([
                    fetch('http://localhost:8000/api/search/stats'),
                    fetch('http://localhost:8000/api/search/history?limit=20')
                ]);

                if (!statsRes.ok) throw new Error('Failed to fetch stats');
                if (!historyRes.ok) throw new Error('Failed to fetch history');

                setStats(await statsRes.json());
                setHistory(await historyRes.json());
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        fetchAnalytics();
    }, []);

    if (loading) {
        return <div className="container" style={{ textAlign: 'center', marginTop: '40px' }}>Loading analytics...</div>;
    }

    if (error) {
        return <div className="container" style={{ color: '#ef4444', textAlign: 'center', marginTop: '40px' }}>Error: {error}</div>;
    }

    return (
        <main className="container" style={{ maxWidth: '1000px' }}>
            <div className="hero-section" style={{ marginBottom: '40px' }}>
                <h1 style={{ fontSize: '3em' }}>Search Analytics</h1>
                <p>View aggregated search statistics and recent activity across the Minerva Library platform.</p>
            </div>

            {stats && (
                <section className="search-section" style={{ display: 'flex', justifyContent: 'space-around', flexWrap: 'wrap', gap: '20px' }}>
                    <div style={{ textAlign: 'center', background: 'rgba(255, 255, 255, 0.05)', padding: '20px', borderRadius: '8px', minWidth: '200px' }}>
                        <h3 style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.9em', marginBottom: '10px' }}>Total Searches</h3>
                        <p style={{ fontSize: '2em', fontWeight: 'bold', color: '#FFD700' }}>{stats.total_searches}</p>
                    </div>
                    <div style={{ textAlign: 'center', background: 'rgba(255, 255, 255, 0.05)', padding: '20px', borderRadius: '8px', minWidth: '200px' }}>
                        <h3 style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.9em', marginBottom: '10px' }}>Avg Search Time</h3>
                        <p style={{ fontSize: '2em', fontWeight: 'bold', color: '#FFD700' }}>{stats.average_search_time}s</p>
                    </div>
                </section>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '40px', marginTop: '40px' }}>
                {/* Popular Queries */}
                <div>
                    <h2 style={{ marginBottom: '20px', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '10px' }}>Most Common Queries</h2>
                    <ul style={{ listStyle: 'none', padding: 0 }}>
                        {stats?.most_common_queries?.map((item, idx) => (
                            <li key={idx} style={{ padding: '12px 0', borderBottom: '1px solid rgba(255,255,255,0.05)', display: 'flex', justifyContent: 'space-between' }}>
                                <span>{item.query}</span>
                                <span style={{ background: 'rgba(255, 215, 0, 0.2)', color: '#FFD700', padding: '2px 8px', borderRadius: '12px', fontSize: '0.8em' }}>{item.count}</span>
                            </li>
                        ))}
                    </ul>
                </div>

                {/* Recent History */}
                <div>
                    <h2 style={{ marginBottom: '20px', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '10px' }}>Recent Searches</h2>
                    <ul style={{ listStyle: 'none', padding: 0 }}>
                        {history?.searches?.map((item, idx) => {
                            const date = new Date(item.timestamp);
                            return (
                                <li key={idx} style={{ padding: '12px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                                        <strong>"{item.query}"</strong>
                                        <span style={{ fontSize: '0.8em', color: 'rgba(255,255,255,0.5)' }}>{date.toLocaleDateString()} {date.toLocaleTimeString()}</span>
                                    </div>
                                    <div style={{ fontSize: '0.8em', color: 'rgba(255,255,255,0.7)' }}>
                                        Found {item.results_count} results in {item.search_time}s
                                    </div>
                                </li>
                            );
                        })}
                    </ul>
                </div>
            </div>
        </main>
    );
};

export default Analytics;