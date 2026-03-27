import React from 'react';

const ProviderStatusBadges = ({ providerStatus }) => {
    if (!providerStatus || providerStatus.length === 0) return null;

    return (
        <div className="provider-status">
            {providerStatus.map((provider, index) => {
                let statusIcon = '?';
                switch (provider.status) {
                    case 'ok': statusIcon = '✓'; break;
                    case 'error': statusIcon = '✗'; break;
                    case 'timeout': statusIcon = '⏱'; break;
                    case 'partial': statusIcon = '⚠'; break;
                    default: break;
                }

                return (
                    <span 
                        key={index} 
                        className={`provider-badge status-${provider.status}`}
                        title={provider.error_message || ''}
                    >
                        {statusIcon} {provider.name} 
                        {provider.results_count > 0 && ` (${provider.results_count})`}
                        {provider.response_time && <span className="provider-response-time"> {provider.response_time}s</span>}
                    </span>
                );
            })}
        </div>
    );
};

export default ProviderStatusBadges;