"""
Fishing Organizations Database with Claude AI Research Assistant
A web-based application for managing fishing organizations with AI-powered research.
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import Optional, List
from contextlib import contextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import anthropic

# ============================================================================
# Configuration
# ============================================================================

DATABASE_PATH = "fishing_organizations.db"
ANTHROPIC_MODEL = "claude-sonnet-4-5-20250929"  # Cost-effective for research

app = FastAPI(
    title="Fishing Organizations Database",
    description="AI-powered fishing organizations research and management",
    version="1.0.0"
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Database Models
# ============================================================================

class Organization(BaseModel):
    id: Optional[int] = None
    name: str
    org_type: str
    focus_area: str
    state_region: str
    website: Optional[str] = None
    contact: Optional[str] = None
    membership: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class ResearchRequest(BaseModel):
    query: str
    state: Optional[str] = None
    org_type: Optional[str] = None

class ResearchResult(BaseModel):
    organizations: List[Organization]
    summary: str
    sources_searched: int

# Tournament models
class Tournament(BaseModel):
    id: Optional[int] = None
    name: str
    event_date: str
    event_time: Optional[str] = None
    end_date: Optional[str] = None
    state: str
    location: str
    species: Optional[str] = None
    entry_fee: Optional[str] = None
    rules_summary: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    contact_website: Optional[str] = None
    organizer: Optional[str] = None
    description: Optional[str] = None
    max_participants: Optional[int] = None
    prize_info: Optional[str] = None
    source: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class TournamentResearchRequest(BaseModel):
    query: str
    state: Optional[str] = None
    species: Optional[str] = None

class TournamentResearchResult(BaseModel):
    tournaments: List[Tournament]
    summary: str
    sources_searched: int

# Series models
class Series(BaseModel):
    id: Optional[int] = None
    name: str
    year: Optional[int] = None
    description: Optional[str] = None
    total_events: Optional[int] = None
    best_of: Optional[int] = None
    participation_points: Optional[float] = 0
    status: Optional[str] = "active"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class SeriesTournament(BaseModel):
    id: Optional[int] = None
    series_id: Optional[int] = None
    tournament_id: Optional[int] = None
    event_name: str
    event_number: Optional[int] = None
    event_date: Optional[str] = None

class SeriesCategory(BaseModel):
    id: Optional[int] = None
    series_id: Optional[int] = None
    name: str
    category_group: Optional[str] = None
    scoring_type: Optional[str] = "points"
    sort_order: Optional[int] = 0

class SeriesParticipant(BaseModel):
    id: Optional[int] = None
    series_id: Optional[int] = None
    boat_name: Optional[str] = None
    captain: Optional[str] = None
    angler_name: Optional[str] = None
    participant_type: Optional[str] = "boat"
    boat_type: Optional[str] = None

class SeriesPoint(BaseModel):
    id: Optional[int] = None
    series_id: Optional[int] = None
    series_tournament_id: Optional[int] = None
    participant_id: Optional[int] = None
    category_id: Optional[int] = None
    points: float
    notes: Optional[str] = None

# ============================================================================
# Database Setup
# ============================================================================

def init_database():
    """Initialize SQLite database with organizations table."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS organizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            org_type TEXT,
            focus_area TEXT,
            state_region TEXT,
            website TEXT,
            contact TEXT,
            membership TEXT,
            description TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create index for faster searches
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_state ON organizations(state_region)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_type ON organizations(org_type)
    """)

    # Tournaments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tournaments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            event_date TEXT NOT NULL,
            event_time TEXT,
            end_date TEXT,
            state TEXT NOT NULL,
            location TEXT NOT NULL,
            species TEXT,
            entry_fee TEXT,
            rules_summary TEXT,
            contact_name TEXT,
            contact_phone TEXT,
            contact_email TEXT,
            contact_website TEXT,
            organizer TEXT,
            description TEXT,
            max_participants INTEGER,
            prize_info TEXT,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tournament_state ON tournaments(state)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tournament_date ON tournaments(event_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tournament_species ON tournaments(species)")

    # Series tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS series (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            year INTEGER,
            description TEXT,
            total_events INTEGER,
            best_of INTEGER,
            participation_points REAL DEFAULT 0,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS series_tournaments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            series_id INTEGER NOT NULL,
            tournament_id INTEGER,
            event_name TEXT NOT NULL,
            event_number INTEGER,
            event_date TEXT,
            FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE CASCADE,
            FOREIGN KEY (tournament_id) REFERENCES tournaments(id) ON DELETE SET NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS series_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            series_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            category_group TEXT,
            scoring_type TEXT DEFAULT 'points',
            sort_order INTEGER DEFAULT 0,
            FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS series_participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            series_id INTEGER NOT NULL,
            boat_name TEXT,
            captain TEXT,
            angler_name TEXT,
            participant_type TEXT DEFAULT 'boat',
            boat_type TEXT,
            FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS series_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            series_id INTEGER NOT NULL,
            series_tournament_id INTEGER NOT NULL,
            participant_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            points REAL NOT NULL,
            notes TEXT,
            FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE CASCADE,
            FOREIGN KEY (series_tournament_id) REFERENCES series_tournaments(id) ON DELETE CASCADE,
            FOREIGN KEY (participant_id) REFERENCES series_participants(id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES series_categories(id) ON DELETE CASCADE,
            UNIQUE(series_tournament_id, participant_id, category_id)
        )
    """)

    conn.commit()
    conn.close()

@contextmanager
def get_db():
    """Database connection context manager."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# ============================================================================
# Claude AI Research Functions
# ============================================================================

def get_anthropic_client():
    """Get Anthropic client - requires ANTHROPIC_API_KEY environment variable."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500, 
            detail="ANTHROPIC_API_KEY environment variable not set. Get your API key at console.anthropic.com"
        )
    return anthropic.Anthropic(api_key=api_key)

def research_organizations(query: str, state: Optional[str] = None, org_type: Optional[str] = None) -> dict:
    """
    Use Claude with web search to research fishing organizations.
    Returns structured data ready for database insertion.
    """
    client = get_anthropic_client()
    
    # Build the research prompt
    location_filter = f" in {state}" if state else ""
    type_filter = f" focusing on {org_type}" if org_type else ""
    
    system_prompt = """You are a research assistant helping build a comprehensive database of fishing organizations, clubs, and associations. 

When researching, focus on finding:
- Official organization names
- Organization type (fishing club, conservation group, guide association, tournament trail, etc.)
- Primary focus area (saltwater, freshwater, fly fishing, bass fishing, offshore, inshore, etc.)
- Geographic coverage (state, region, or specific area)
- Website URL
- Contact information if available
- Membership details (size, cost, requirements)
- Brief description of activities and mission

Always verify information through web search. Return ONLY organizations you find evidence for - never make up organizations."""

    user_prompt = f"""Research fishing organizations{location_filter}{type_filter} matching this request: {query}

Use web search to find current, accurate information. For each organization found, gather:
1. Official name
2. Type of organization
3. Focus area (what kind of fishing/conservation)
4. State/region served
5. Website
6. Any contact info
7. Membership info
8. Description

Return your findings as a JSON object with this exact structure:
{{
    "organizations": [
        {{
            "name": "Organization Name",
            "org_type": "Type (e.g., Fishing Club, Conservation, Guide Association)",
            "focus_area": "Focus (e.g., Saltwater, Bass Fishing, Fly Fishing)",
            "state_region": "State or Region",
            "website": "https://...",
            "contact": "Contact info if found",
            "membership": "Membership details if found",
            "description": "Brief description",
            "notes": "Any additional relevant notes"
        }}
    ],
    "summary": "Brief summary of what you found",
    "sources_searched": number_of_sources
}}

Be thorough but only include organizations you can verify exist."""

    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=4096,
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search"
            }],
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        
        # Extract the text response
        result_text = ""
        for block in response.content:
            if hasattr(block, 'text'):
                result_text += block.text
        
        # Parse JSON from response
        # Find JSON in the response (it might be wrapped in markdown code blocks)
        json_start = result_text.find('{')
        json_end = result_text.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = result_text[json_start:json_end]
            return json.loads(json_str)
        else:
            return {
                "organizations": [],
                "summary": result_text,
                "sources_searched": 0
            }
            
    except json.JSONDecodeError as e:
        return {
            "organizations": [],
            "summary": f"Research completed but could not parse results: {result_text[:500]}",
            "sources_searched": 0
        }
    except anthropic.APIError as e:
        raise HTTPException(status_code=500, detail=f"Anthropic API error: {str(e)}")

def research_tournaments(query: str, state: Optional[str] = None, species: Optional[str] = None) -> dict:
    """Use Claude with web search to research fishing tournaments."""
    client = get_anthropic_client()

    location_filter = f" in {state}" if state else ""
    species_filter = f" for {species}" if species else ""

    system_prompt = """You are a research assistant helping find fishing tournament schedules in the US Southeast coastal states (NC, SC, GA, FL, AL, MS, LA, TX).

When researching, focus on finding:
- Tournament name
- Dates and times
- Location and state
- Target species
- Entry fees
- Rules summary
- Contact information
- Organizer name
- Prize information

Always verify information through web search. Return ONLY tournaments you find evidence for."""

    user_prompt = f"""Research fishing tournaments{location_filter}{species_filter} matching: {query}

Return as JSON:
{{
    "tournaments": [
        {{
            "name": "Tournament Name",
            "event_date": "YYYY-MM-DD",
            "event_time": "7:00 AM",
            "end_date": "YYYY-MM-DD or null",
            "state": "XX",
            "location": "City or venue",
            "species": "Target species",
            "entry_fee": "$XXX",
            "rules_summary": "Key rules",
            "contact_name": "Name",
            "contact_phone": "Phone",
            "contact_email": "email",
            "contact_website": "url",
            "organizer": "Organizing club/group",
            "description": "Brief description",
            "max_participants": number_or_null,
            "prize_info": "Prize details"
        }}
    ],
    "summary": "Brief summary",
    "sources_searched": number
}}"""

    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=4096,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        result_text = ""
        for block in response.content:
            if hasattr(block, 'text'):
                result_text += block.text

        json_start = result_text.find('{')
        json_end = result_text.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            return json.loads(result_text[json_start:json_end])
        return {"tournaments": [], "summary": result_text, "sources_searched": 0}

    except json.JSONDecodeError:
        return {"tournaments": [], "summary": f"Could not parse results: {result_text[:500]}", "sources_searched": 0}
    except anthropic.APIError as e:
        raise HTTPException(status_code=500, detail=f"Anthropic API error: {str(e)}")

# ============================================================================
# API Routes
# ============================================================================

@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    init_database()

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main application."""
    return FileResponse("static/index.html")

# ----- Organization CRUD -----

@app.get("/api/organizations", response_model=List[Organization])
async def list_organizations(
    state: Optional[str] = Query(None, description="Filter by state"),
    org_type: Optional[str] = Query(None, description="Filter by organization type"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    limit: int = Query(100, le=500),
    offset: int = Query(0)
):
    """List organizations with optional filters."""
    with get_db() as conn:
        query = "SELECT * FROM organizations WHERE 1=1"
        params = []
        
        if state:
            query += " AND state_region LIKE ?"
            params.append(f"%{state}%")
        
        if org_type:
            query += " AND org_type LIKE ?"
            params.append(f"%{org_type}%")
        
        if search:
            query += " AND (name LIKE ? OR description LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        
        query += " ORDER BY name LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        
        return [Organization(**dict(row)) for row in rows]

@app.get("/api/organizations/{org_id}", response_model=Organization)
async def get_organization(org_id: int):
    """Get a single organization by ID."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM organizations WHERE id = ?", (org_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        return Organization(**dict(row))

@app.post("/api/organizations", response_model=Organization)
async def create_organization(org: Organization):
    """Create a new organization."""
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO organizations (name, org_type, focus_area, state_region, website, contact, membership, description, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (org.name, org.org_type, org.focus_area, org.state_region, org.website, org.contact, org.membership, org.description, org.notes))
        
        conn.commit()
        org.id = cursor.lastrowid
        return org

@app.put("/api/organizations/{org_id}", response_model=Organization)
async def update_organization(org_id: int, org: Organization):
    """Update an existing organization."""
    with get_db() as conn:
        cursor = conn.execute("""
            UPDATE organizations 
            SET name=?, org_type=?, focus_area=?, state_region=?, website=?, contact=?, membership=?, description=?, notes=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        """, (org.name, org.org_type, org.focus_area, org.state_region, org.website, org.contact, org.membership, org.description, org.notes, org_id))
        
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        org.id = org_id
        return org

@app.delete("/api/organizations/{org_id}")
async def delete_organization(org_id: int):
    """Delete an organization."""
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM organizations WHERE id = ?", (org_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        return {"message": "Organization deleted"}

# ----- AI Research -----

@app.post("/api/research", response_model=ResearchResult)
async def research(request: ResearchRequest):
    """Use Claude AI to research fishing organizations."""
    result = research_organizations(request.query, request.state, request.org_type)
    
    return ResearchResult(
        organizations=[Organization(**org) for org in result.get("organizations", [])],
        summary=result.get("summary", ""),
        sources_searched=result.get("sources_searched", 0)
    )

@app.post("/api/research/add")
async def add_research_results(organizations: List[Organization]):
    """Add multiple organizations from research results."""
    added = []
    with get_db() as conn:
        for org in organizations:
            cursor = conn.execute("""
                INSERT INTO organizations (name, org_type, focus_area, state_region, website, contact, membership, description, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (org.name, org.org_type, org.focus_area, org.state_region, org.website, org.contact, org.membership, org.description, org.notes))
            org.id = cursor.lastrowid
            added.append(org)
        
        conn.commit()
    
    return {"added": len(added), "organizations": added}

# ----- Statistics -----

@app.get("/api/stats")
async def get_stats():
    """Get database statistics."""
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM organizations").fetchone()[0]
        
        by_state = conn.execute("""
            SELECT state_region, COUNT(*) as count 
            FROM organizations 
            GROUP BY state_region 
            ORDER BY count DESC
        """).fetchall()
        
        by_type = conn.execute("""
            SELECT org_type, COUNT(*) as count 
            FROM organizations 
            GROUP BY org_type 
            ORDER BY count DESC
        """).fetchall()
        
        return {
            "total_organizations": total,
            "by_state": [{"state": row[0], "count": row[1]} for row in by_state],
            "by_type": [{"type": row[0], "count": row[1]} for row in by_type]
        }

# ----- Export -----

@app.get("/api/export")
async def export_data():
    """Export all organizations as JSON."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM organizations ORDER BY state_region, name")
        rows = cursor.fetchall()
        
        return {
            "exported_at": datetime.now().isoformat(),
            "total": len(rows),
            "organizations": [dict(row) for row in rows]
        }

# ============================================================================
# Tournament Routes
# ============================================================================

@app.get("/api/tournaments", response_model=List[Tournament])
async def list_tournaments(
    state: Optional[str] = Query(None),
    species: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0)
):
    """List tournaments with optional filters."""
    with get_db() as conn:
        query = "SELECT * FROM tournaments WHERE 1=1"
        params = []
        if state:
            query += " AND state = ?"
            params.append(state)
        if species:
            query += " AND species LIKE ?"
            params.append(f"%{species}%")
        if search:
            query += " AND (name LIKE ? OR description LIKE ? OR organizer LIKE ? OR location LIKE ?)"
            params.extend([f"%{search}%"] * 4)
        if date_from:
            query += " AND event_date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND event_date <= ?"
            params.append(date_to)
        query += " ORDER BY event_date ASC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        rows = conn.execute(query, params).fetchall()
        return [Tournament(**dict(row)) for row in rows]

@app.post("/api/tournaments", response_model=Tournament)
async def create_tournament(t: Tournament):
    """Create a new tournament."""
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO tournaments (name, event_date, event_time, end_date, state, location,
                species, entry_fee, rules_summary, contact_name, contact_phone, contact_email,
                contact_website, organizer, description, max_participants, prize_info, source)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (t.name, t.event_date, t.event_time, t.end_date, t.state, t.location,
              t.species, t.entry_fee, t.rules_summary, t.contact_name, t.contact_phone,
              t.contact_email, t.contact_website, t.organizer, t.description,
              t.max_participants, t.prize_info, t.source))
        conn.commit()
        t.id = cursor.lastrowid
        return t

@app.get("/api/tournaments/stats")
async def tournament_stats():
    """Get tournament statistics."""
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM tournaments").fetchone()[0]
        upcoming = conn.execute(
            "SELECT COUNT(*) FROM tournaments WHERE event_date >= date('now')"
        ).fetchone()[0]
        by_state = conn.execute(
            "SELECT state, COUNT(*) as count FROM tournaments GROUP BY state ORDER BY count DESC"
        ).fetchall()
        by_species = conn.execute(
            "SELECT species, COUNT(*) as count FROM tournaments WHERE species IS NOT NULL GROUP BY species ORDER BY count DESC"
        ).fetchall()
        return {
            "total_tournaments": total,
            "upcoming": upcoming,
            "by_state": [{"state": r[0], "count": r[1]} for r in by_state],
            "by_species": [{"species": r[0], "count": r[1]} for r in by_species],
        }

@app.post("/api/tournaments/research", response_model=TournamentResearchResult)
async def research_tournaments_endpoint(request: TournamentResearchRequest):
    """Use Claude AI to research fishing tournaments."""
    result = research_tournaments(request.query, request.state, request.species)
    return TournamentResearchResult(
        tournaments=[Tournament(**t) for t in result.get("tournaments", [])],
        summary=result.get("summary", ""),
        sources_searched=result.get("sources_searched", 0),
    )

@app.post("/api/tournaments/research/add")
async def add_tournament_research(tournaments: List[Tournament]):
    """Bulk add tournaments from research results."""
    added = []
    with get_db() as conn:
        for t in tournaments:
            cursor = conn.execute("""
                INSERT INTO tournaments (name, event_date, event_time, end_date, state, location,
                    species, entry_fee, rules_summary, contact_name, contact_phone, contact_email,
                    contact_website, organizer, description, max_participants, prize_info, source)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (t.name, t.event_date, t.event_time, t.end_date, t.state, t.location,
                  t.species, t.entry_fee, t.rules_summary, t.contact_name, t.contact_phone,
                  t.contact_email, t.contact_website, t.organizer, t.description,
                  t.max_participants, t.prize_info, t.source))
            t.id = cursor.lastrowid
            added.append(t)
        conn.commit()
    return {"added": len(added), "tournaments": added}

@app.post("/api/tournaments/seed")
async def seed_tournaments():
    """Seed sample tournament data (only if table is empty)."""
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM tournaments").fetchone()[0]
        if count > 0:
            return {"message": f"Table already has {count} tournaments", "seeded": 0}

        sample = [
            ("Cape Fear Redfish Classic", "2026-03-14", "6:00 AM", "2026-03-14", "NC", "Wrightsville Beach, NC", "Redfish", "$150 per boat", "Catch and release, 2-fish limit, slot 18-27 inches. Artificial lures only.", "Mike Turner", "(910) 555-0142", "mike@capefearredfish.com", None, "Cape Fear Fishing Club", "Annual inshore redfish tournament with cash prizes and trophies.", 60, "$5,000 first place, $2,500 second", "sample"),
            ("Charleston Harbor Flounder Slam", "2026-04-18", "7:00 AM", "2026-04-18", "SC", "Charleston, SC", "Flounder", "$100 per angler", "3-fish bag limit, 16 inch minimum. Live or artificial bait.", "Sarah Mitchell", "(843) 555-0198", "info@charlestonflounders.com", None, "Lowcountry Anglers Association", "Popular flounder tournament in Charleston Harbor and surrounding creeks.", 80, "$3,000 total purse", "sample"),
            ("Georgia Kingfish Challenge", "2026-05-09", "5:30 AM", "2026-05-10", "GA", "Savannah, GA", "King Mackerel", "$200 per boat", "Live bait and trolling permitted. No wire leaders over 6 ft.", "James Cooper", "(912) 555-0167", "james@gakingfish.org", None, "Savannah Offshore Fishing Club", "Two-day king mackerel tournament out of Thunderbolt Marina.", 40, "$10,000 first place", "sample"),
            ("Florida Keys Tarpon Fly Cup", "2026-05-22", "6:30 AM", "2026-05-24", "FL", "Islamorada, FL", "Tarpon", "$500 per team", "Fly tackle only, 12-weight max. Catch-photo-release format.", "Captain Rob Ellis", "(305) 555-0211", "rob@keystarpon.com", None, "Islamorada Fly Fishing Club", "Three-day prestigious tarpon on fly tournament in the Florida Keys.", 20, "$15,000 first place, custom trophies", "sample"),
            ("Alabama Deep Sea Rodeo", "2026-06-12", "5:00 AM", "2026-06-14", "AL", "Dauphin Island, AL", "Offshore Multi-species", "$250 per boat", "Multiple species divisions: red snapper, king mackerel, cobia, tuna.", "Robert Jackson", "(251) 555-0133", "info@aldeepsea.com", None, "Mobile Bay Fishing Association", "The Gulf Coast's largest offshore fishing tournament with dozens of categories.", 200, "$50,000 total purse", "sample"),
            ("Mississippi Sound Speckled Trout Shootout", "2026-03-28", "6:00 AM", "2026-03-28", "MS", "Biloxi, MS", "Speckled Trout", "$125 per boat", "5-fish limit per angler, 15 inch minimum. Artificial lures only.", "Tony Nguyen", "(228) 555-0155", "tony@msspecks.com", None, "Gulf Coast Trout Masters", "Premier speckled trout tournament along the Mississippi barrier islands.", 50, "$4,000 first place", "sample"),
            ("Louisiana Redfish Roundup", "2026-04-04", "5:30 AM", "2026-04-05", "LA", "Venice, LA", "Redfish", "$300 per team", "2-person teams, 5 redfish limit per team. Slot 16-27 inches.", "Captain Dale Thibodaux", "(504) 555-0177", "dale@laredfish.com", None, "Delta Redfish League", "Two-day team redfish event in the legendary Louisiana marsh.", 75, "$8,000 first place, $4,000 second", "sample"),
            ("Texas Offshore Slam", "2026-06-20", "4:30 AM", "2026-06-21", "TX", "Port Aransas, TX", "Offshore Multi-species", "$350 per boat", "Divisions for yellowfin tuna, wahoo, dorado, and billfish (release only).", "Chris Morales", "(361) 555-0199", "chris@texasoffshore.com", None, "Port Aransas Offshore Club", "Two-day blue water tournament targeting pelagic species in the Gulf.", 60, "$20,000 first place", "sample"),
            ("Outer Banks Surf Fishing Classic", "2026-10-17", "6:00 AM", "2026-10-18", "NC", "Nags Head, NC", "Surf Multi-species", "$75 per angler", "Points-based scoring. Target species: red drum, bluefish, sea mullet, flounder.", "Karen Bradley", "(252) 555-0144", "karen@obxsurf.org", None, "Outer Banks Surf Fishing Association", "Annual surf fishing classic on the beaches of the Outer Banks.", 150, "$2,000 first place, tackle prizes", "sample"),
            ("Palmetto Bass Trail Championship", "2026-04-25", "6:30 AM", "2026-04-26", "SC", "Santee Cooper Lakes, SC", "Largemouth Bass", "$200 per boat", "5-fish limit, 14 inch minimum. No Alabama rigs. Catch-weigh-release.", "Derek Williams", "(803) 555-0166", "derek@palmettobass.com", None, "Palmetto Bass Trail", "Season championship on South Carolina's premier bass fishery.", 100, "$7,500 first place boat", "sample"),
            ("Space Coast Snook Invitational", "2026-09-12", "6:00 AM", "2026-09-13", "FL", "Cape Canaveral, FL", "Snook", "$175 per angler", "Catch-photo-release. Minimum 28 inches. Artificial lures only.", "Maria Santos", "(321) 555-0188", "maria@spacecoastsnook.com", None, "Brevard County Anglers", "Two-day snook tournament along the Indian River Lagoon.", 40, "$5,000 first place", "sample"),
            ("Calcasieu Lake Slam", "2026-05-16", "5:00 AM", "2026-05-16", "LA", "Lake Charles, LA", "Inshore Slam", "$200 per boat", "Slam format: redfish + speckled trout + flounder. Heaviest combined weight wins.", "Paul Guidry", "(337) 555-0121", "paul@calcasieuslam.com", None, "Southwest Louisiana Fishing League", "Inshore slam tournament on world-famous Calcasieu Lake.", 50, "$6,000 first place", "sample"),
            ("Tybee Island Shark Tournament", "2026-07-11", "6:00 AM", "2026-07-12", "GA", "Tybee Island, GA", "Sharks", "$250 per boat", "Catch-tag-release. Points by species and estimated size. Blacktip, bull, hammerhead.", "Captain Will Harper", "(912) 555-0204", "will@tybeesharks.com", None, "Georgia Shark Fishing Alliance", "Catch-tag-release shark tournament for conservation data collection.", 30, "$3,500 first place, research recognition", "sample"),
            ("Gulf Shores King Mackerel Shootout", "2026-08-08", "5:00 AM", "2026-08-09", "AL", "Gulf Shores, AL", "King Mackerel", "$200 per boat", "Heaviest single king mackerel wins. Live bait and trolling permitted.", "Steve Patterson", "(251) 555-0178", "steve@gulfkings.com", None, "Gulf Shores Fishing Club", "Annual king mackerel tournament with calcutta side pots.", 45, "$8,000 first place with calcutta", "sample"),
            ("Biloxi Marsh Redfishing Series", "2026-09-20", "5:30 AM", "2026-09-20", "MS", "Biloxi, MS", "Redfish", "$150 per team", "2-person teams, 3 redfish per team. Slot 18-30 inches. Artificial only.", "Andre Lewis", "(228) 555-0192", "andre@biloxireds.com", None, "Mississippi Redfish Series", "Competitive redfish series event in the expansive Biloxi Marsh.", 40, "$3,000 first place", "sample"),
            ("South Padre Island Offshore Classic", "2026-07-24", "4:00 AM", "2026-07-26", "TX", "South Padre Island, TX", "Offshore Multi-species", "$500 per boat", "Three-day event. Divisions for marlin (release), tuna, dorado, wahoo, kingfish.", "Ricardo Garza", "(956) 555-0213", "ricardo@spioffshore.com", None, "South Padre Sportfishing Association", "Premier three-day offshore tournament near the US-Mexico border.", 50, "$25,000 first place, $50,000 total purse", "sample"),
            ("Crystal Coast Wahoo Open", "2026-11-07", "5:30 AM", "2026-11-08", "NC", "Morehead City, NC", "Wahoo", "$300 per boat", "Heaviest single wahoo wins. High-speed trolling. Gulf Stream waters.", "Dan Fletcher", "(252) 555-0137", "dan@crystalcoastwahoo.com", None, "Crystal Coast Sportfishing Club", "Late-season wahoo tournament targeting the fall Gulf Stream bite.", 35, "$7,000 first place", "sample"),
            ("Myrtle Beach Pier King Classic", "2026-10-03", "6:00 AM", "2026-10-04", "SC", "Myrtle Beach, SC", "King Mackerel", "$50 per angler", "Pier fishing only. Heaviest king mackerel wins. All standard tackle permitted.", "Brenda Cole", "(843) 555-0154", "brenda@mbpier.org", None, "Grand Strand Pier Fishing Club", "Affordable pier-based king mackerel tournament open to all skill levels.", 100, "$1,500 first place", "sample"),
            ("Panhandle Cobia Cup", "2026-04-11", "6:00 AM", "2026-04-12", "FL", "Destin, FL", "Cobia", "$225 per boat", "Heaviest single cobia wins. Sight casting and bottom fishing divisions.", "Captain Jim Bates", "(850) 555-0169", "jim@destincobia.com", None, "Emerald Coast Fishing Association", "Spring cobia tournament during the annual cobia migration along the Panhandle.", 55, "$6,000 first place", "sample"),
            ("Galveston Bay Flounder Fiesta", "2026-11-14", "6:30 AM", "2026-11-14", "TX", "Galveston, TX", "Flounder", "$100 per angler", "5-fish limit, 15 inch minimum. All legal methods. Heaviest stringer wins.", "Lisa Chen", "(409) 555-0147", "lisa@galvestonflounder.com", None, "Galveston Bay Fishing Association", "Fall flounder tournament targeting the annual flounder run in Galveston Bay.", 75, "$3,000 first place", "sample"),
        ]

        for t in sample:
            conn.execute("""
                INSERT INTO tournaments (name, event_date, event_time, end_date, state, location,
                    species, entry_fee, rules_summary, contact_name, contact_phone, contact_email,
                    contact_website, organizer, description, max_participants, prize_info, source)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, t)
        conn.commit()
        return {"message": "Seeded 20 sample tournaments", "seeded": 20}

@app.get("/api/tournaments/{tournament_id}", response_model=Tournament)
async def get_tournament(tournament_id: int):
    """Get a single tournament."""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM tournaments WHERE id = ?", (tournament_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Tournament not found")
        return Tournament(**dict(row))

@app.put("/api/tournaments/{tournament_id}", response_model=Tournament)
async def update_tournament(tournament_id: int, t: Tournament):
    """Update a tournament."""
    with get_db() as conn:
        cursor = conn.execute("""
            UPDATE tournaments SET name=?, event_date=?, event_time=?, end_date=?, state=?,
                location=?, species=?, entry_fee=?, rules_summary=?, contact_name=?,
                contact_phone=?, contact_email=?, contact_website=?, organizer=?,
                description=?, max_participants=?, prize_info=?, source=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        """, (t.name, t.event_date, t.event_time, t.end_date, t.state, t.location,
              t.species, t.entry_fee, t.rules_summary, t.contact_name, t.contact_phone,
              t.contact_email, t.contact_website, t.organizer, t.description,
              t.max_participants, t.prize_info, t.source, tournament_id))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Tournament not found")
        t.id = tournament_id
        return t

@app.delete("/api/tournaments/{tournament_id}")
async def delete_tournament(tournament_id: int):
    """Delete a tournament."""
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM tournaments WHERE id = ?", (tournament_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Tournament not found")
        return {"message": "Tournament deleted"}

# ============================================================================
# Series Routes
# ============================================================================

@app.get("/api/series")
async def list_series(
    year: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
):
    """List all series with participant counts."""
    with get_db() as conn:
        query = "SELECT * FROM series WHERE 1=1"
        params = []
        if year:
            query += " AND year = ?"
            params.append(year)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY year DESC, name"
        rows = conn.execute(query, params).fetchall()
        result = []
        for row in rows:
            s = dict(row)
            s["participant_count"] = conn.execute(
                "SELECT COUNT(*) FROM series_participants WHERE series_id = ?", (s["id"],)
            ).fetchone()[0]
            s["tournament_count"] = conn.execute(
                "SELECT COUNT(*) FROM series_tournaments WHERE series_id = ?", (s["id"],)
            ).fetchone()[0]
            result.append(s)
        return result

@app.post("/api/series")
async def create_series(s: Series):
    """Create a new series."""
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO series (name, year, description, total_events, best_of, participation_points, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (s.name, s.year, s.description, s.total_events, s.best_of, s.participation_points, s.status))
        conn.commit()
        s.id = cursor.lastrowid
        return s

@app.get("/api/series/{series_id}")
async def get_series(series_id: int):
    """Get series with full detail."""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM series WHERE id = ?", (series_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Series not found")
        s = dict(row)
        s["tournaments"] = [dict(r) for r in conn.execute(
            "SELECT * FROM series_tournaments WHERE series_id = ? ORDER BY event_number", (series_id,)
        ).fetchall()]
        s["categories"] = [dict(r) for r in conn.execute(
            "SELECT * FROM series_categories WHERE series_id = ? ORDER BY sort_order, id", (series_id,)
        ).fetchall()]
        s["participants"] = [dict(r) for r in conn.execute(
            "SELECT * FROM series_participants WHERE series_id = ?", (series_id,)
        ).fetchall()]
        return s

@app.put("/api/series/{series_id}")
async def update_series(series_id: int, s: Series):
    """Update a series."""
    with get_db() as conn:
        cursor = conn.execute("""
            UPDATE series SET name=?, year=?, description=?, total_events=?, best_of=?,
                participation_points=?, status=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        """, (s.name, s.year, s.description, s.total_events, s.best_of,
              s.participation_points, s.status, series_id))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Series not found")
        s.id = series_id
        return s

@app.delete("/api/series/{series_id}")
async def delete_series(series_id: int):
    """Delete a series and all related data."""
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM series WHERE id = ?", (series_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Series not found")
        return {"message": "Series deleted"}

# ----- Series Tournaments -----

@app.get("/api/series/{series_id}/tournaments")
async def list_series_tournaments(series_id: int):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM series_tournaments WHERE series_id = ? ORDER BY event_number", (series_id,)
        ).fetchall()
        return [dict(r) for r in rows]

@app.post("/api/series/{series_id}/tournaments")
async def add_series_tournament(series_id: int, t: SeriesTournament):
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO series_tournaments (series_id, tournament_id, event_name, event_number, event_date)
            VALUES (?, ?, ?, ?, ?)
        """, (series_id, t.tournament_id, t.event_name, t.event_number, t.event_date))
        conn.commit()
        t.id = cursor.lastrowid
        t.series_id = series_id
        return t

@app.delete("/api/series/{series_id}/tournaments/{tournament_id}")
async def delete_series_tournament(series_id: int, tournament_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM series_tournaments WHERE id = ? AND series_id = ?", (tournament_id, series_id))
        conn.commit()
        return {"message": "Removed"}

# ----- Series Categories -----

@app.get("/api/series/{series_id}/categories")
async def list_series_categories(series_id: int):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM series_categories WHERE series_id = ? ORDER BY sort_order, id", (series_id,)
        ).fetchall()
        return [dict(r) for r in rows]

@app.post("/api/series/{series_id}/categories")
async def add_series_category(series_id: int, c: SeriesCategory):
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO series_categories (series_id, name, category_group, scoring_type, sort_order)
            VALUES (?, ?, ?, ?, ?)
        """, (series_id, c.name, c.category_group, c.scoring_type, c.sort_order))
        conn.commit()
        c.id = cursor.lastrowid
        c.series_id = series_id
        return c

@app.delete("/api/series/{series_id}/categories/{category_id}")
async def delete_series_category(series_id: int, category_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM series_categories WHERE id = ? AND series_id = ?", (category_id, series_id))
        conn.commit()
        return {"message": "Removed"}

# ----- Series Participants -----

@app.get("/api/series/{series_id}/participants")
async def list_series_participants(series_id: int):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM series_participants WHERE series_id = ?", (series_id,)
        ).fetchall()
        return [dict(r) for r in rows]

@app.post("/api/series/{series_id}/participants")
async def add_series_participant(series_id: int, p: SeriesParticipant):
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO series_participants (series_id, boat_name, captain, angler_name, participant_type, boat_type)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (series_id, p.boat_name, p.captain, p.angler_name, p.participant_type, p.boat_type))
        conn.commit()
        p.id = cursor.lastrowid
        p.series_id = series_id
        return p

@app.delete("/api/series/{series_id}/participants/{participant_id}")
async def delete_series_participant(series_id: int, participant_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM series_participants WHERE id = ? AND series_id = ?", (participant_id, series_id))
        conn.commit()
        return {"message": "Removed"}

# ----- Series Points -----

@app.get("/api/series/{series_id}/points")
async def list_series_points(
    series_id: int,
    series_tournament_id: Optional[int] = Query(None),
    participant_id: Optional[int] = Query(None),
    category_id: Optional[int] = Query(None),
):
    with get_db() as conn:
        query = "SELECT * FROM series_points WHERE series_id = ?"
        params = [series_id]
        if series_tournament_id:
            query += " AND series_tournament_id = ?"
            params.append(series_tournament_id)
        if participant_id:
            query += " AND participant_id = ?"
            params.append(participant_id)
        if category_id:
            query += " AND category_id = ?"
            params.append(category_id)
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

@app.post("/api/series/{series_id}/points")
async def save_series_points(series_id: int, points: List[SeriesPoint]):
    """Save points — upserts based on (series_tournament_id, participant_id, category_id)."""
    with get_db() as conn:
        saved = []
        for p in points:
            cursor = conn.execute("""
                INSERT INTO series_points (series_id, series_tournament_id, participant_id, category_id, points, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(series_tournament_id, participant_id, category_id)
                DO UPDATE SET points=excluded.points, notes=excluded.notes
            """, (series_id, p.series_tournament_id, p.participant_id, p.category_id, p.points, p.notes))
            saved.append({**p.dict(), "id": cursor.lastrowid, "series_id": series_id})
        conn.commit()
        return {"saved": len(saved), "points": saved}

# ----- Standings -----

@app.get("/api/series/{series_id}/standings")
async def get_standings(
    series_id: int,
    group: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
):
    """Compute leaderboard with best-of-N logic."""
    with get_db() as conn:
        series_row = conn.execute("SELECT * FROM series WHERE id = ?", (series_id,)).fetchone()
        if not series_row:
            raise HTTPException(status_code=404, detail="Series not found")
        series = dict(series_row)
        best_of = series.get("best_of") or 999
        participation_pts = series.get("participation_points") or 0

        # Get tournaments in order
        tournaments_rows = conn.execute(
            "SELECT * FROM series_tournaments WHERE series_id = ? ORDER BY event_number", (series_id,)
        ).fetchall()
        tourney_list = [dict(r) for r in tournaments_rows]
        tourney_ids = [t["id"] for t in tourney_list]

        # Get participants (filtered by group)
        p_query = "SELECT * FROM series_participants WHERE series_id = ?"
        p_params = [series_id]
        if group and group != "all":
            if group in ("private", "charter"):
                p_query += " AND participant_type = 'boat' AND boat_type = ?"
                p_params.append(group)
            else:
                p_query += " AND participant_type = ?"
                p_params.append(group)
        participants = [dict(r) for r in conn.execute(p_query, p_params).fetchall()]

        # Get all points for this series
        pts_query = "SELECT * FROM series_points WHERE series_id = ?"
        pts_params = [series_id]
        if category_id:
            pts_query += " AND category_id = ?"
            pts_params.append(category_id)
        all_points = [dict(r) for r in conn.execute(pts_query, pts_params).fetchall()]

        # Build standings
        standings = []
        for part in participants:
            pid = part["id"]
            # Sum points per tournament for this participant
            tourney_totals = {}
            for tid in tourney_ids:
                pts_for_tourney = [p["points"] for p in all_points
                                   if p["participant_id"] == pid and p["series_tournament_id"] == tid]
                tourney_totals[tid] = sum(pts_for_tourney)

            # Count events participated in
            events_fished = sum(1 for tid in tourney_ids if tourney_totals.get(tid, 0) > 0)

            # Sort descending, take top N
            sorted_totals = sorted(tourney_totals.values(), reverse=True)
            best_of_score = sum(sorted_totals[:best_of])

            # Add participation points for each event fished
            total_participation = events_fished * participation_pts
            best_of_score += total_participation

            aggregate = sum(sorted_totals) + total_participation

            # Which tournament IDs are "counted"?
            sorted_tids = sorted(tourney_ids, key=lambda tid: tourney_totals.get(tid, 0), reverse=True)
            counted_ids = set(sorted_tids[:best_of])

            per_tournament = {}
            for t in tourney_list:
                tid = t["id"]
                per_tournament[str(tid)] = {
                    "points": tourney_totals.get(tid, 0),
                    "counted": tid in counted_ids and tourney_totals.get(tid, 0) > 0,
                }

            display_name = part.get("boat_name") or part.get("angler_name") or "Unknown"

            standings.append({
                "participant": part,
                "display_name": display_name,
                "per_tournament": per_tournament,
                "best_of_score": best_of_score,
                "aggregate": aggregate,
                "events_fished": events_fished,
                "counted_ids": list(counted_ids),
            })

        # Sort by best_of_score desc, then aggregate desc as tiebreaker
        standings.sort(key=lambda x: (-x["best_of_score"], -x["aggregate"]))

        # Assign ranks
        for i, s in enumerate(standings):
            s["rank"] = i + 1

        return {
            "series": series,
            "tournaments": tourney_list,
            "standings": standings,
            "best_of": best_of,
        }

# ----- Series Seed -----

@app.post("/api/series/seed")
async def seed_series():
    """Seed NC Billfish Series example data."""
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM series").fetchone()[0]
        if count > 0:
            return {"message": f"Series table already has {count} entries", "seeded": 0}

        # Create the series
        cursor = conn.execute("""
            INSERT INTO series (name, year, description, total_events, best_of, participation_points, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("NC Billfish Series", 2026,
              "North Carolina's premier billfish tournament series. Boats compete across multiple events for cumulative points with best 3 of 8 counting toward final standings.",
              8, 3, 25, "active"))
        series_id = cursor.lastrowid

        # Add 4 tournaments
        tourney_data = [
            (1, "Hatteras Marlin Club Blue Marlin Release", "2026-06-07"),
            (2, "Pirates Cove Billfish Tournament", "2026-06-21"),
            (3, "NC DU Band the Billfish", "2026-07-12"),
            (4, "Swansboro Bluewater Invitational", "2026-08-02"),
        ]
        tourney_ids = []
        for num, name, date in tourney_data:
            c = conn.execute("""
                INSERT INTO series_tournaments (series_id, event_name, event_number, event_date)
                VALUES (?, ?, ?, ?)
            """, (series_id, name, num, date))
            tourney_ids.append(c.lastrowid)

        # Add 13 categories
        cat_data = [
            ("Blue Marlin Release", "Release", "points", 1),
            ("White Marlin Release", "Release", "points", 2),
            ("Sailfish Release", "Release", "points", 3),
            ("Largest Blue Marlin", "Big Fish", "weight", 4),
            ("Largest Tuna", "Big Fish", "weight", 5),
            ("Largest Wahoo", "Big Fish", "weight", 6),
            ("Largest Dolphin", "Big Fish", "weight", 7),
            ("Lady Angler", "Special", "points", 8),
            ("Junior Boy", "Special", "points", 9),
            ("Junior Girl", "Special", "points", 10),
            ("Top Private Boat", "Boat", "points", 11),
            ("Top Charter Boat", "Boat", "points", 12),
            ("Overall Points", "Boat", "points", 13),
        ]
        cat_ids = []
        for name, grp, scoring, order in cat_data:
            c = conn.execute("""
                INSERT INTO series_categories (series_id, name, category_group, scoring_type, sort_order)
                VALUES (?, ?, ?, ?, ?)
            """, (series_id, name, grp, scoring, order))
            cat_ids.append(c.lastrowid)

        # Add 6 boats
        boat_data = [
            ("Sea Hunter", "Capt. Bill Davis", "boat", "private"),
            ("Blue Fin Express", "Capt. Tom Richards", "boat", "charter"),
            ("Reel Addiction", "Capt. Mike Jensen", "boat", "private"),
            ("Fish Whisper", "Capt. Sarah Cole", "boat", "charter"),
            ("Marlin Magic", "Capt. Dan Brooks", "boat", "private"),
            ("Island Time", "Capt. Jake Owens", "boat", "charter"),
        ]
        participant_ids = []
        for bname, captain, ptype, btype in boat_data:
            c = conn.execute("""
                INSERT INTO series_participants (series_id, boat_name, captain, participant_type, boat_type)
                VALUES (?, ?, ?, ?, ?)
            """, (series_id, bname, captain, ptype, btype))
            participant_ids.append(c.lastrowid)

        # Sample points — distribute across tournaments for meaningful leaderboard
        # cat_ids: 0=Blue Marlin Rel, 1=White Marlin Rel, 2=Sailfish Rel, 3=Largest Blue, 4=Largest Tuna, 5=Largest Wahoo, 6=Largest Dolphin, 7=Lady, 8=Jr Boy, 9=Jr Girl, 10=Top Private, 11=Top Charter, 12=Overall
        # tourney_ids: 0-3, participant_ids: 0-5
        points_data = [
            # Tournament 1 — Hatteras
            (tourney_ids[0], participant_ids[0], cat_ids[0], 300, "2 blue marlin releases"),
            (tourney_ids[0], participant_ids[0], cat_ids[1], 100, "1 white marlin"),
            (tourney_ids[0], participant_ids[0], cat_ids[4], 25, "42 lb tuna"),
            (tourney_ids[0], participant_ids[1], cat_ids[0], 150, "1 blue marlin release"),
            (tourney_ids[0], participant_ids[1], cat_ids[2], 75, "1 sailfish"),
            (tourney_ids[0], participant_ids[1], cat_ids[5], 30, "38 lb wahoo"),
            (tourney_ids[0], participant_ids[2], cat_ids[0], 450, "3 blue marlin releases"),
            (tourney_ids[0], participant_ids[2], cat_ids[3], 50, "420 lb blue marlin"),
            (tourney_ids[0], participant_ids[3], cat_ids[1], 200, "2 white marlin"),
            (tourney_ids[0], participant_ids[3], cat_ids[6], 20, "28 lb dolphin"),
            (tourney_ids[0], participant_ids[4], cat_ids[0], 150, "1 blue marlin release"),
            (tourney_ids[0], participant_ids[4], cat_ids[4], 35, "55 lb tuna"),
            (tourney_ids[0], participant_ids[5], cat_ids[2], 150, "2 sailfish"),
            (tourney_ids[0], participant_ids[5], cat_ids[5], 40, "45 lb wahoo"),

            # Tournament 2 — Pirates Cove
            (tourney_ids[1], participant_ids[0], cat_ids[0], 150, "1 blue marlin release"),
            (tourney_ids[1], participant_ids[0], cat_ids[5], 45, "52 lb wahoo"),
            (tourney_ids[1], participant_ids[1], cat_ids[0], 300, "2 blue marlin releases"),
            (tourney_ids[1], participant_ids[1], cat_ids[1], 100, "1 white marlin"),
            (tourney_ids[1], participant_ids[2], cat_ids[2], 75, "1 sailfish"),
            (tourney_ids[1], participant_ids[2], cat_ids[4], 30, "48 lb tuna"),
            (tourney_ids[1], participant_ids[3], cat_ids[0], 300, "2 blue marlin releases"),
            (tourney_ids[1], participant_ids[3], cat_ids[3], 60, "480 lb blue marlin"),
            (tourney_ids[1], participant_ids[4], cat_ids[0], 300, "2 blue marlin releases"),
            (tourney_ids[1], participant_ids[4], cat_ids[1], 200, "2 white marlin"),
            (tourney_ids[1], participant_ids[5], cat_ids[0], 150, "1 blue marlin release"),
            (tourney_ids[1], participant_ids[5], cat_ids[4], 20, "35 lb tuna"),

            # Tournament 3 — NC DU Band
            (tourney_ids[2], participant_ids[0], cat_ids[0], 450, "3 blue marlin releases"),
            (tourney_ids[2], participant_ids[0], cat_ids[3], 70, "510 lb blue marlin"),
            (tourney_ids[2], participant_ids[1], cat_ids[1], 100, "1 white marlin"),
            (tourney_ids[2], participant_ids[1], cat_ids[4], 25, "40 lb tuna"),
            (tourney_ids[2], participant_ids[2], cat_ids[0], 300, "2 blue marlin releases"),
            (tourney_ids[2], participant_ids[2], cat_ids[1], 100, "1 white marlin"),
            (tourney_ids[2], participant_ids[3], cat_ids[0], 150, "1 blue marlin release"),
            (tourney_ids[2], participant_ids[3], cat_ids[2], 75, "1 sailfish"),
            (tourney_ids[2], participant_ids[4], cat_ids[0], 150, "1 blue marlin release"),
            (tourney_ids[2], participant_ids[4], cat_ids[6], 25, "32 lb dolphin"),
            (tourney_ids[2], participant_ids[5], cat_ids[0], 300, "2 blue marlin releases"),
            (tourney_ids[2], participant_ids[5], cat_ids[1], 200, "2 white marlin"),

            # Tournament 4 — Swansboro
            (tourney_ids[3], participant_ids[0], cat_ids[1], 200, "2 white marlin"),
            (tourney_ids[3], participant_ids[0], cat_ids[2], 75, "1 sailfish"),
            (tourney_ids[3], participant_ids[1], cat_ids[0], 150, "1 blue marlin release"),
            (tourney_ids[3], participant_ids[1], cat_ids[3], 45, "380 lb blue marlin"),
            (tourney_ids[3], participant_ids[2], cat_ids[0], 150, "1 blue marlin release"),
            (tourney_ids[3], participant_ids[2], cat_ids[5], 35, "41 lb wahoo"),
            (tourney_ids[3], participant_ids[3], cat_ids[0], 150, "1 blue marlin release"),
            (tourney_ids[3], participant_ids[3], cat_ids[4], 40, "60 lb tuna"),
            (tourney_ids[3], participant_ids[4], cat_ids[2], 150, "2 sailfish"),
            (tourney_ids[3], participant_ids[4], cat_ids[5], 30, "36 lb wahoo"),
            (tourney_ids[3], participant_ids[5], cat_ids[0], 150, "1 blue marlin release"),
            (tourney_ids[3], participant_ids[5], cat_ids[6], 30, "35 lb dolphin"),
        ]

        for tid, pid, cid, pts, note in points_data:
            conn.execute("""
                INSERT INTO series_points (series_id, series_tournament_id, participant_id, category_id, points, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (series_id, tid, pid, cid, pts, note))

        conn.commit()
        return {"message": "Seeded NC Billfish Series with 4 tournaments, 13 categories, 6 boats, and sample points", "seeded": 1}

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
