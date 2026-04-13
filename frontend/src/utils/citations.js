// Utility functions for generating citations from a SearchResult object

const formatAuthors = (authors) => {
    if (!authors || authors.length === 0) return 'Unknown Author';
    return authors.map(a => a.name).join(', ');
};

const formatAuthorsAPA = (authors) => {
    if (!authors || authors.length === 0) return 'Unknown Author';
    return authors.map((a, i) => {
        const parts = a.name.split(' ');
        if (parts.length > 1) {
            const last = parts.pop();
            const initials = parts.map(p => p[0] + '.').join(' ');
            return i === authors.length - 1 && authors.length > 1 
                ? `& ${last}, ${initials}` 
                : `${last}, ${initials}`;
        }
        return a.name;
    }).join(', ');
};

const formatAuthorsMLA = (authors) => {
    if (!authors || authors.length === 0) return 'Unknown Author';
    if (authors.length === 1) {
        const parts = authors[0].name.split(' ');
        if (parts.length > 1) {
            const last = parts.pop();
            return `${last}, ${parts.join(' ')}`;
        }
        return authors[0].name;
    }
    if (authors.length === 2) {
        const parts1 = authors[0].name.split(' ');
        const last1 = parts1.pop();
        return `${last1}, ${parts1.join(' ')}, and ${authors[1].name}`;
    }
    const parts1 = authors[0].name.split(' ');
    const last1 = parts1.pop();
    return `${last1}, ${parts1.join(' ')}, et al`;
};

export const getAPA = (result) => {
    const authors = formatAuthorsAPA(result.authors);
    const year = result.publication_year ? `(${result.publication_year}).` : '(n.d.).';
    const title = result.title ? `${result.title}.` : '';
    const source = result.source ? `*${result.source}*.` : '';
    const url = result.doi ? `https://doi.org/${result.doi}` : (result.url || '');

    return `${authors} ${year} ${title} ${source} ${url}`.trim();
};

export const getMLA = (result) => {
    const authors = formatAuthorsMLA(result.authors);
    const title = result.title ? `"${result.title}."` : '';
    const source = result.source ? `*${result.source}*,` : '';
    const year = result.publication_year ? `${result.publication_year}.` : '';
    const url = result.doi ? `https://doi.org/${result.doi}` : (result.url || '');

    return `${authors}. ${title} ${source} ${year} ${url}`.trim();
};

export const getChicago = (result) => {
    // Similar to MLA but with date at the end for notes/bibliography style
    const authors = formatAuthorsMLA(result.authors);
    const title = result.title ? `"${result.title}."` : '';
    const source = result.source ? `*${result.source}*` : '';
    const year = result.publication_year ? `(${result.publication_year}).` : '';
    const url = result.doi ? `https://doi.org/${result.doi}` : (result.url || '');

    return `${authors}. ${title} ${source} ${year} ${url}`.trim();
};

export const getBibTeX = (result) => {
    const authors = result.authors ? result.authors.map(a => a.name).join(' and ') : 'Unknown';
    const id = result.id ? result.id.replace(/[^a-zA-Z0-9]/g, '') : 'unknown';
    const title = result.title || '';
    const year = result.publication_year || '';
    const publisher = result.source || '';
    const url = result.doi ? `https://doi.org/${result.doi}` : (result.url || '');

    return `@article{${id},
  title={${title}},
  author={${authors}},
  year={${year}},
  publisher={${publisher}},
  url={${url}}
}`;
};