from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from neo4j import GraphDatabase

# Initialize the API engine
app = FastAPI(title="Crypto Tracing API")

# Enable CORS for local React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATABASE CONFIGURATION ---
# Replace with the exact password you used in seed_data.py
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "admin123"

# We create one single driver instance to use across all API calls
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

@app.get("/api/v1/wallet/{address}")
def get_wallet(address: str):
    """Returns specific metadata, balance, and risk score for a single wallet."""
    query = """
    MATCH (w:WalletAddress {address: $address}) 
    RETURN w.address AS address, w.balance AS balance, w.risk_score AS risk_score, w.label AS label
    """
    with driver.session() as session:
        result = session.run(query, address=address).single()
        if result:
            return result.data()
        return {"error": "Wallet not found"}

@app.get("/api/v1/trace/{address}")
def trace_wallet(address: str, depth: int = 2):
    """Main tracing endpoint. Returns array of connected nodes and edges."""
    query = """
    MATCH (start:WalletAddress {address: $address})-[r:SENT_TO*1..2]-(connected:WalletAddress)
    UNWIND r AS tx
    RETURN DISTINCT start.address AS search_target, connected.address AS connected_wallet, tx.amount AS amount, tx.timestamp AS timestamp
    """
    with driver.session() as session:
        records = session.run(query, address=address).data()
        return {"trace_results": records}

@app.get("/api/v1/vasp/identify/{address}")
def identify_vasp(address: str):
    """Checks if wallet belongs to a known exchange, mixer, or blacklisted address."""
    query = """
    MATCH (w:WalletAddress {address: $address})-[:BELONGS_TO]->(v:VASP) 
    RETURN v.name AS vasp_name, v.category AS category
    """
    with driver.session() as session:
        result = session.run(query, address=address).single()
        if result:
            return result.data()
        return {"status": "Unknown Entity"}