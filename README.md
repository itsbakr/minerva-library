# 🔍 Minerva Library Search API

A unified search interface that simultaneously searches multiple academic databases (OpenAlex, CrossRef, and more) and returns deduplicated, ranked results through a single API endpoint.
<img width="1676" height="1072" alt="image" src="https://github.com/user-attachments/assets/29891fd2-fd50-44d2-9220-4b56dbdf2d71" />

Built as part of Minerva University's work-study program to improve student research efficiency.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg?style=flat&logo=FastAPI)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg?style=flat&logo=python)](https://www.python.org)

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Technology Stack](#-technology-stack)
- [Getting Started](#-getting-started)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [Development](#-development)
- [Testing](#-testing)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [Troubleshooting](#-troubleshooting)

---

## ✨ Features

### Current Features

- **🔎 Unified Search**: Search multiple academic databases with a single query
- **⚡ Parallel API Calls**: Searches databases simultaneously for fast results (<2 seconds)
- **🎯 Smart Ranking**: Advanced relevance scoring with phrase matching, coverage analysis, and quality signals
- **🔄 Intelligent Deduplication**: Merges duplicate records from multiple sources for richer metadata
- **📊 Provider Status Tracking**: Real-time visibility into which databases returned results, response times, and errors
- **⏱️ Timeout Handling**: Graceful degradation - if one provider is slow, others continue
- **📅 Advanced Filtering**: Filter by publication year, open access status, and more
- **📚 Rich Metadata**: Titles, authors, abstracts, DOIs, citation counts, and full-text links
- **🌐 Open Access Detection**: Identifies freely available articles via Unpaywall enrichment
- **📈 Structured Logging**: Detailed logs for debugging and monitoring provider performance
- **🗄️ Multiple Databases**: 
  - OpenAlex (250+ million scholarly works)
  - CrossRef (140+ million scholarly records)
  - Unpaywall (DOI-based open access enrichment)
  - More coming soon (EBSCO, JSTOR)


### Coming Soon

- 🔐 EBSCO and JSTOR integration (pending institutional credentials)
- 💾 Search history and bookmarking
- 📥 Citation export (APA, MLA, Chicago)
- 🎨 React frontend interface
- 🔖 User accounts and saved searches
- 📱 Mobile-responsive design
<img width="1670" height="1110" alt="image" src="https://github.com/user-attachments/assets/b2a130a3-dac4-4a57-bc59-98ab6231be61" />

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│              Student Search Request                  │
│         "climate change agriculture"                 │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│         Query Optimization Engine                    │
│  • Boolean logic: "climate change" AND agriculture   │
│  • Synonym expansion                                 │
│  • Database-specific formatting                      │
└──────────────────┬──────────────────────────────────┘
                   ↓
        ┌──────────┴──────────┬──────────────┐
        ↓                     ↓              ↓
┌──────────────┐  ┌──────────────┐  ┌─────────────┐
│ OpenAlex API │  │ CrossRef API │  │  JSTOR API  │
│  (Parallel)  │  │  (Parallel)  │  │  (Coming)   │
└──────┬───────┘  └──────┬───────┘  └──────┬──────┘
       └──────────┬───────┴────────────────┘
                  ↓
┌─────────────────────────────────────────────────────┐
│         Result Aggregation & Processing              │
│  • Combine results from all databases                │
│  • Merge duplicates (DOI + fuzzy title matching)     │
│  • Enrich with Unpaywall open access data            │
│  • Rank by advanced relevance algorithm              │
│  • Track provider status & response times            │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│         Unified Search Results (JSON)                │
│  • Sorted by relevance score                         │
│  • Merged metadata from multiple sources             │
│  • Provider status for observability                 │
│  • ~1-2 second response time                         │
└─────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

### Backend
- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern, fast web framework for building APIs
- **[Python 3.11+](https://www.python.org/)** - Programming language
- **[httpx](https://www.python-httpx.org/)** - Async HTTP client for API calls
- **[Pydantic](https://pydantic-docs.helpmanual.io/)** - Data validation using Python type annotations
- **[Uvicorn](https://www.uvicorn.org/)** - Lightning-fast ASGI server

### APIs Integrated
- **[OpenAlex](https://openalex.org/)** - Open scholarly metadata (free, no auth required)
- **[CrossRef](https://www.crossref.org/)** - Scholarly metadata and DOI resolution (free, no auth required)
- **[Unpaywall](https://unpaywall.org/)** - Open access discovery via DOI enrichment (free, email required)
- **EBSCO Discovery Service** - Institutional databases (pending credentials)
- **JSTOR** - Historical and humanities content (pending credentials)

### Development Tools
- **Git** - Version control
- **Virtual Environment** - Dependency isolation
- **Auto-generated API Docs** - Swagger UI + ReDoc

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Git
- Internet connection (for API calls)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/minerva-library-search.git
cd minerva-library-search
```

2. **Create virtual environment**
```bash
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the development server**
```bash
uvicorn app.main:app --reload
```

5. **Open your browser**
- API documentation: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

---

## 📖 API Documentation

### Base URL
```
http://localhost:8000
```

### Endpoints

#### `GET /api/search`

Search across all academic databases with unified results.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `q` | string | ✅ Yes | - | Search query (keywords, phrases) |
| `page` | integer | No | 1 | Page number (min: 1) |
| `per_page` | integer | No | 20 | Results per page (min: 1, max: 100) |
| `year_min` | integer | No | - | Minimum publication year (1900-2025) |
| `year_max` | integer | No | - | Maximum publication year (1900-2025) |
| `open_access_only` | boolean | No | false | Return only open access articles |

**Example Requests:**

```bash
# Basic search
curl "http://localhost:8000/api/search?q=machine+learning&per_page=10"

# Search with year filter
curl "http://localhost:8000/api/search?q=climate+change&year_min=2020&year_max=2025"

# Open access only
curl "http://localhost:8000/api/search?q=neural+networks&open_access_only=true"

# Pagination
curl "http://localhost:8000/api/search?q=quantum+computing&page=2&per_page=20"
```

**Example Response:**

```json
{
  "query": "climate change",
  "total_results": 9,
  "results": [
    {
      "id": "https://openalex.org/W4213327538",
      "title": "Climate Change 2013 – The Physical Science Basis",
      "authors": [
        {
          "name": "Intergovernmental Panel on Climate Change",
          "affiliation": null
        }
      ],
      "abstract": "This latest Fifth Assessment Report of the IPCC...",
      "publication_year": 2014,
      "source": "OpenAlex+CrossRef",
      "doi": "10.1017/cbo9781107415324",
      "url": "https://doi.org/10.1017/cbo9781107415324",
      "is_open_access": true,
      "open_access_url": "https://escholarship.org/content/qt2j42x9fh/qt2j42x9fh.pdf",
      "cited_by_count": 11567,
      "relevance_score": 145.8
    }
  ],
  "search_time": 1.47,
  "databases_searched": ["OpenAlex", "CrossRef", "Unpaywall (OA enrichment)"],
  "provider_status": [
    {
      "name": "OpenAlex",
      "status": "ok",
      "results_count": 15,
      "response_time": 0.823,
      "error_message": null
    },
    {
      "name": "CrossRef",
      "status": "ok",
      "results_count": 12,
      "response_time": 1.156,
      "error_message": null
    },
    {
      "name": "Unpaywall",
      "status": "ok",
      "results_count": 3,
      "response_time": 2.341,
      "error_message": null
    }
  ]
}
```

**Provider Status Values:**
- `ok` - Provider responded successfully
- `error` - Provider encountered an error (see error_message)
- `timeout` - Provider exceeded timeout threshold (30s)
- `partial` - Provider returned incomplete results

#### `GET /health`

Health check endpoint to verify API is running.

**Example Request:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy"
}
```

---

## 📁 Project Structure

```
minerva-library-search/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── models.py              # Pydantic models for request/response
│   │   └── search.py              # Search endpoint implementation
│   └── services/
│       ├── __init__.py
│       ├── openalex.py            # OpenAlex API integration
│       ├── crossref.py            # CrossRef API integration
│       ├── aggregator.py          # Combines results from all APIs
│       └── [future services]      # EBSCO, JSTOR, Unpaywall
├── .gitignore
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

### Key Files Explained

**`app/main.py`**
- FastAPI application initialization
- CORS middleware configuration
- Router registration

**`app/api/models.py`**
- Pydantic models for data validation
- `SearchResult`, `SearchResponse`, `Author` models

**`app/api/search.py`**
- `/api/search` endpoint implementation
- Query parameter validation
- Error handling

**`app/services/openalex.py`**
- OpenAlex API client
- Response parsing and normalization
- Abstract reconstruction from inverted index

**`app/services/crossref.py`**
- CrossRef API client
- XML/JSON response handling
- Metadata extraction

**`app/services/aggregator.py`**
- Parallel API call orchestration with timeout handling
- Smart deduplication with record merging (DOI + fuzzy title matching)
- Advanced relevance ranking with phrase matching and quality signals
- Provider status tracking and structured logging

---

## 💻 Development

### Running in Development Mode

```bash
# With auto-reload (detects file changes)
uvicorn app.main:app --reload

# Custom host and port
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# With log level
uvicorn app.main:app --reload --log-level debug
```

### Adding a New Database API

To add a new database (e.g., Unpaywall):

1. **Create service file**: `app/services/unpaywall.py`

```python
import httpx
from typing import List, Optional
from app.api.models import SearchResult

class UnpaywallService:
    BASE_URL = "https://api.unpaywall.org/v2"
    
    async def search(
        self,
        query: str,
        page: int = 1,
        per_page: int = 20,
        **filters
    ) -> tuple[List[SearchResult], int]:
        """Search Unpaywall for open access articles"""
        # Implementation here
        pass
```

2. **Update aggregator**: `app/services/aggregator.py`

```python
from app.services.unpaywall import UnpaywallService

class SearchAggregator:
    async def search_all(self, ...):
        unpaywall = UnpaywallService()
        
        tasks = [
            openalex.search(...),
            crossref.search(...),
            unpaywall.search(...)  # Add new service
        ]
        # Rest of implementation
```

3. **Test the integration**

```bash
curl "http://localhost:8000/api/search?q=test&per_page=5"
```

---

## 🧪 Testing

### Manual Testing

**Test basic search:**
```bash
curl "http://localhost:8000/api/search?q=artificial+intelligence&per_page=5"
```

**Test with filters:**
```bash
curl "http://localhost:8000/api/search?q=machine+learning&year_min=2023&open_access_only=true"
```

**Test pagination:**
```bash
curl "http://localhost:8000/api/search?q=climate+change&page=2&per_page=10"
```

### Using the Interactive API Docs

1. Open http://localhost:8000/docs
2. Click on `/api/search` endpoint
3. Click "Try it out"
4. Enter parameters and click "Execute"
5. View the response below

---

## 🗺️ Roadmap

### Phase 1: Core Functionality
- [x] FastAPI backend setup
- [x] OpenAlex API integration
- [x] CrossRef API integration
- [x] Unpaywall API integration (OA enrichment)
- [x] Parallel search execution with timeout handling
- [x] Smart deduplication with record merging
- [x] Advanced relevance ranking algorithm
- [x] Year filtering
- [x] Open access detection and enrichment
- [x] Provider status tracking and observability
- [x] Structured logging for debugging

### Phase 2: Additional Databases & Quality Improvements
- [x] Unpaywall API integration for OA enrichment
- [x] Improved deduplication with fuzzy title matching (>92% similarity)
- [x] Record merging for richer metadata
- [x] DOI normalization across providers
- [ ] EBSCO Discovery Service integration (pending credentials)
- [ ] JSTOR XML Gateway integration (pending credentials)

### Phase 3: Advanced Features (Weeks 5-6)
- [ ] Search history (database + endpoints)
- [ ] Bookmark functionality
- [ ] Citation export (APA, MLA, Chicago)
- [ ] Redis caching for common queries
- [ ] Advanced filtering (peer-reviewed, content type)

### Phase 4: Frontend Development (Weeks 7-9)
- [ ] React + Next.js frontend
- [ ] Search interface with filters
- [ ] Result cards with metadata
- [ ] Integration with Minerva Forum
- [ ] Responsive mobile design

### Phase 5: Optimization & Polish (Weeks 10-12)
- [ ] Performance optimization
- [ ] Comprehensive testing
- [ ] User testing (10-15 students)
- [ ] Documentation completion
- [ ] Production deployment

---

## 🤝 Contributing

### Workflow

1. **Create a branch** for your feature
```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes** and commit
```bash
git add .
git commit -m "Add: description of your changes"
```

3. **Push to GitHub**
```bash
git push origin feature/your-feature-name
```

4. **Create a Pull Request** on GitHub

### Commit Message Guidelines

- **feat**: New feature or functionality
- **fix**: Bug fix
- **update**: Modify existing functionality
- **refactor**: Code restructuring without changing behavior
- **docs**: Documentation changes
- **test**: Add or update tests

Example: `feat: Unpaywall API integration for open access detection`

---

## 📊 Monitoring & Logs

### Viewing Logs

The application uses structured logging to track all provider interactions. When running the server, you'll see detailed logs:

```
2026-01-18 10:30:45 - app.services.aggregator - INFO - Search started: query='climate change', page=1
2026-01-18 10:30:46 - app.services.aggregator - INFO - Provider OpenAlex: status=ok, results=15, response_time=0.823s
2026-01-18 10:30:47 - app.services.aggregator - INFO - Provider CrossRef: status=ok, results=12, response_time=1.156s
2026-01-18 10:30:49 - app.services.aggregator - INFO - Unpaywall: enriched 3 results with OA data, response_time=2.341s
2026-01-18 10:30:49 - app.services.aggregator - INFO - Search complete: 18 final results from 3 databases
```

### Provider Status in API Response

Every search response includes `provider_status` array showing:
- Which providers were queried
- Response time for each
- Number of results returned
- Any errors or timeouts

**Example in UI:**
- ✓ Green badge = Provider succeeded
- ✗ Red badge = Provider error  
- ⏱ Orange badge = Provider timeout
- ⚠ Yellow badge = Partial results

### Key Metrics to Monitor

- **Response Time**: Should be <3s for most queries
- **Provider Success Rate**: Check how often each provider times out
- **Result Quality**: Check `relevance_score` distribution
- **Deduplication Rate**: Monitor `merged X → Y results` in logs

---

## 🐛 Troubleshooting

### Common Issues

#### Issue: `ModuleNotFoundError: No module named 'app'`
**Solution**: Make sure you're running uvicorn from the project root directory.
```bash
cd minerva-library-search
uvicorn app.main:app --reload
```

#### Issue: `ConnectionError` when calling APIs
**Solution**: Check your internet connection and verify API endpoints are accessible.
```bash
# Test OpenAlex directly
curl "https://api.openalex.org/works?search=test&per_page=5"
```

#### Issue: Slow response times (>5 seconds)
**Solution**: 
1. Check network connection
2. Reduce `per_page` parameter
3. Check `provider_status` in API response to identify slow providers
4. Review server logs for timeout warnings
5. Individual providers have 30s timeout - slow providers won't block entire search

#### Issue: `RuntimeWarning: coroutine was never awaited`
**Solution**: Make sure you're using `await` with async functions:
```python
# ❌ Wrong
results = service.search(query)

# ✅ Correct
results = await service.search(query)
```

#### Issue: Empty results for common queries
**Solution**: 
1. Check `provider_status` in API response to see which providers failed
2. Look for timeout or error status indicators
3. Check API status pages:
   - OpenAlex: https://docs.openalex.org/
   - CrossRef: https://status.crossref.org/
   - Unpaywall: https://unpaywall.org/products/api

#### Issue: Provider shows "timeout" or "error" status
**Solution**:
1. **Timeout**: Provider took >30 seconds to respond
   - Check your internet connection
   - Try again - provider may be temporarily slow
   - Other providers will still return results
2. **Error**: Provider returned an error
   - Check server logs for detailed error message
   - Hover over error badge in UI to see error details
   - Verify API endpoint is accessible: check status pages above

### Getting Help

1. Check the [API Documentation](#-api-documentation)
2. Review error messages in terminal
3. Check FastAPI docs: http://localhost:8000/docs
4. Contact team members via Slack/Discord

---

## 📧 Contact

**Project Lead**: Ahmed Bakr
- Email: bakr@uni.minerva.edu
- GitHub: [@itsbakr](https://github.com/itsbakr)

**Institution**: Minerva University
- Website: https://www.minerva.edu
- Location: San Francisco, CA

---

## 🌟 Star History

If you find this project useful, please consider giving it a star on GitHub! ⭐

---

**Built with ❤️ at Minerva University**
