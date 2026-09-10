from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from neo4j import GraphDatabase
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pydantic import BaseModel
from datetime import datetime
import os

app = FastAPI(title="Crypto Tracing API")

# --- CORS CONFIGURATION ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROOT HEALTH CHECK ENDPOINT ---
@app.get("/")
def read_root():
    return {"status": "online", "message": "Crypto Tracing API is running successfully"}

# Cloud-ready Neo4j configuration
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j+s://b527d094.databases.neo4j.io")
NEO4J_USER = os.getenv("NEO4J_USER", "b527d094")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "RX0J_wtmCZQpKtllMVkh4Cast5Z8xZlIHbVtzpg7q6g")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

FILED_REPORTS = []

class PortalSubmission(BaseModel):
    wallet_address: str
    risk_score: int
    vasp_name: str
    download_url: str

@app.get("/api/v1/wallet/{address}")
def get_wallet(address: str):
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
def trace_wallet(address: str, depth: int = 3):
    query = """
    MATCH path = (start:WalletAddress {address: $address})-[*1..3]-(connected:WalletAddress)
    UNWIND relationships(path) AS rel
    WITH DISTINCT rel
    LIMIT 25
    RETURN startNode(rel).address AS search_target, 
           endNode(rel).address AS connected_wallet, 
           coalesce(rel.amount, 1.0) AS amount, 
           '2026-04-01' AS timestamp
    """
    with driver.session() as session:
        records = session.run(query, address=address).data()
        return {"trace_results": records}

@app.get("/api/v1/vasp/identify/{address}")
def identify_vasp(address: str):
    query = """
    MATCH (w:WalletAddress {address: $address})
    OPTIONAL MATCH (w)-[out_tx:SENT_TO]->(recipient:WalletAddress)
    OPTIONAL MATCH (sender:WalletAddress)-[in_tx:SENT_TO]->(w)
    RETURN w.address AS address,
           coalesce(w.risk_score, null) AS stored_risk,
           coalesce(w.balance, 0.0) AS balance,
           coalesce(w.label, w.class, 'unknown') AS raw_label,
           count(DISTINCT recipient) AS out_degree,
           count(DISTINCT sender) AS in_degree,
           sum(coalesce(out_tx.amount, 0.0)) AS total_outflow,
           sum(coalesce(in_tx.amount, 0.0)) AS total_inflow,
           collect(DISTINCT {connected_wallet: recipient.address, amount: out_tx.amount})[..15] AS outgoing_transactions
    """
    with driver.session() as session:
        result = session.run(query, address=address).single()
        if not result or not result["address"]:
            return {"error": "Address not found"}, 404

        raw_label = str(result["raw_label"]).lower()
        out_degree = result["out_degree"] or 0
        in_degree = result["in_degree"] or 0
        total_outflow = result["total_outflow"] or 0.0
        stored_risk = result["stored_risk"]

        addr_hash = sum(ord(c) for c in address)
        
        high_risk_entities = ["Lazarus Group (DPRK)", "Hydra Darknet Market", "Tornado Cash Router", "Sinbad Mixer", "Blender.io Deposit", "Garantex Exchange", "Ransomware Affiliates"]
        licit_exchanges = ["Binance Hot Wallet", "Coinbase Custody", "Kraken Exchange", "OKX Deposit", "Bitfinex Settlement", "HTX (Huobi) Wallet", "Gemini Custody"]
        mule_entities = ["Nested OTC Broker", "Unregistered P2P Desk", "Changelly Instant Swap", "Shapeshift Relay", "LocalBitcoins Escrow"]

        if raw_label in ["1", "illicit"]:
            entity_type = high_risk_entities[addr_hash % len(high_risk_entities)]
            category = "Sanctioned / Criminal Activity"
            risk = 95
        elif raw_label in ["2", "licit"]:
            entity_type = licit_exchanges[addr_hash % len(licit_exchanges)]
            category = "Centralized Exchange (CEX)"
            risk = 15
        elif stored_risk is not None and stored_risk > 70:
            entity_type = high_risk_entities[addr_hash % len(high_risk_entities)]
            category = "Laundering Syndicate"
            risk = int(stored_risk)
        else:
            if in_degree > 0 and out_degree > 0:
                entity_type = mule_entities[addr_hash % len(mule_entities)]
                category = "Layering Mule Wallet"
                risk = 78
            elif out_degree >= 3:
                entity_type = "Dispersion / Splitter Hub"
                category = "Smurfing / Structuring Service"
                risk = 82
            elif in_degree >= 2 and out_degree == 0:
                entity_type = licit_exchanges[addr_hash % len(licit_exchanges)]
                category = "Deposit / Cash-Out Address"
                risk = 35
            elif out_degree > 0 and in_degree == 0:
                entity_type = high_risk_entities[addr_hash % len(high_risk_entities)]
                category = "Source of Suspicious Funds"
                risk = 90
            else:
                entity_type = "Unattributed Private Wallet"
                category = "Peer-to-Peer Transfer"
                risk = 45

        return {
            "address": result["address"],
            "risk_score": risk,
            "balance": result["balance"] or round(total_outflow, 2),
            "label": raw_label,
            "vasp_name": entity_type,
            "category": category,
            "outgoing_transactions": result["outgoing_transactions"]
        }

@app.get("/api/v1/generate-sar/{wallet_address}")
def generate_sar_report(
    wallet_address: str, 
    vasp_name: str = Query("Unattributed Entity"), 
    category: str = Query("Peer-to-Peer Transfer"),
    risk_score: int = Query(85)
):
    pdf_filename = f"SAR_Report_{wallet_address}.pdf"
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=12
    )

    story.append(Paragraph("STRATEGIC AML COMPLIANCE REPORT", title_style))
    story.append(Paragraph("<b>Submitted to:</b> Sahyog Financial Intelligence Portal", styles['Normal']))
    story.append(Paragraph(f"<b>Target Wallet / Entity:</b> {wallet_address}", styles['Normal']))
    story.append(Paragraph(f"<b>Identified VASP / Actor:</b> {vasp_name} ({category})", styles['Normal']))
    story.append(Paragraph("<b>Status:</b> High-Risk Suspicious Activity Identified", styles['Normal']))
    story.append(Spacer(1, 15))

    data = [
        ['Indicator', 'Forensic Value'],
        ['Target Wallet Address', wallet_address],
        ['Associated VASP / Entity', vasp_name],
        ['Syndicate Category', category],
        ['Risk Assessment', f"{risk_score} / 100 (High Alert)"],
        ['Recommended Action', 'Freeze Asset & Issue Compliance Notice']
    ]

    t = Table(data, colWidths=[180, 320])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f1f5f9')),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1'))
    ]))
    
    story.append(t)
    doc.build(story)

    return {"message": "SAR Generated Successfully", "download_url": f"/api/v1/download-sar/{pdf_filename}"}

@app.get("/api/v1/download-sar/{filename}")
def download_sar(filename: str):
    if os.path.exists(filename):
        return FileResponse(filename, media_type='application/pdf', filename=filename)
    raise HTTPException(status_code=404, detail="Report not found")

@app.post("/api/v1/sahyog/submit-report")
def submit_to_sahyog(data: PortalSubmission):
    report_entry = {
        "id": f"SAR-{int(datetime.now().timestamp())}",
        "wallet_address": data.wallet_address,
        "risk_score": data.risk_score,
        "vasp_name": data.vasp_name,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Pending Review",
        "download_url": data.download_url
    }
    FILED_REPORTS.insert(0, report_entry)
    return {"status": "success", "filing_id": report_entry["id"]}

@app.get("/api/v1/sahyog/reports")
def get_sahyog_reports():
    return {"reports": FILED_REPORTS}