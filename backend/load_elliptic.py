import os
import pandas as pd
from neo4j import GraphDatabase

# Neo4j local connection details
URI = "bolt://localhost:7687"
AUTH = ("neo4j","admin123")  # Change "password" if you set a custom password during Neo4j setup

def load_data():
    print("🚀 Starting Elliptic Dataset bulk load into Neo4j...")
    
    # Paths to your CSV files
    edgelist_path = "data/elliptic_txs_edgelist.csv"
    classes_path = "data/elliptic_txs_classes.csv"
    
    if not os.path.exists(edgelist_path) or not os.path.exists(classes_path):
        print("❌ Error: CSV files not found in backend/data/ folder!")
        return

    # 1. Load Classes (Risk mapping: 1 = Illicit (High Risk), 2 = Licit (Low Risk))
    print("📂 Reading transaction classes...")
    classes_df = pd.read_csv(classes_path)
    
    # Create a dictionary mapping txId -> risk score
    # If class is '1' (illicit), risk = 95. If '2' (licit), risk = 10. Else 50.
    def get_risk(val):
        if val == '1': return 95
        elif val == '2': return 10
        return 50

    classes_df['risk_score'] = classes_df['class'].apply(get_risk)
    
    driver = GraphDatabase.driver(URI, auth=AUTH)

    with driver.session() as session:
        print("📥 Inserting transaction nodes and risk scores into Neo4j...")
        # Batch insert nodes to prevent memory overflow
        batch_size = 5000
        for i in range(0, len(classes_df), batch_size):
            batch = classes_df.iloc[i:i+batch_size]
            query = """
            UNWIND $batch AS row
            MERGE (w:WalletAddress {address: toString(row.txId)})
            SET w.risk_score = row.risk_score,
                w.balance = round(rand() * 50, 2),
                w.label = case row.class when '1' then 'Illicit' when '2' then 'Licit' else 'Unknown' end
            """
            session.run(query, batch=batch.to_dict(orient="records"))
            print(f"Processed nodes {i} to {i+len(batch)}...")

        # 2. Load Edges (Transactions between wallets)
        print("📂 Reading transaction edgelist...")
        edgelist_df = pd.read_csv(edgelist_path)
        
        print("📥 Inserting transaction edges into Neo4j...")
        for i in range(0, len(edgelist_df), batch_size):
            batch = edgelist_df.iloc[i:i+batch_size]
            query = """
            UNWIND $batch AS row
            MATCH (w1:WalletAddress {address: toString(row.txId1)})
            MATCH (w2:WalletAddress {address: toString(row.txId2)})
            CREATE (w1)-[r:SENT_TO {amount: round(rand() * 5, 2), timestamp: '2026-04-01'}]->(w2)
            """
            session.run(query, batch=batch.to_dict(orient="records"))
            print(f"Processed edges {i} to {i+len(batch)}...")

    driver.close()
    print("✅ Successfully loaded Elliptic Dataset into Neo4j!")

if __name__ == "__main__":
    load_data()