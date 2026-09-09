from neo4j import GraphDatabase

# --- 1. DATABASE CONNECTION CONFIGURATION ---
# Replace these with your actual Neo4j credentials
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "admin123"


def seed_database(tx):
    # Wipe the existing database clean so we start fresh every run
    tx.run("MATCH (n) DETACH DELETE n")

    # --- 2. CREATE ENTITIES / VASPS ---
    tx.run(
        """
        CREATE (b:VASP {entity_id: 'VASP_BINANCE', name: 'Binance', category: 'Exchange'}),
               (c:VASP {entity_id: 'VASP_COINBASE', name: 'Coinbase', category: 'Exchange'}),
               (m:VASP {entity_id: 'VASP_TORNADO', name: 'Tornado Cash', category: 'Mixer'})
    """
    )

    # --- 3. CREATE WALLET ADDRESSES ---
    # Hacker -> Mules -> Mixer / Exchanges
    tx.run(
        """
        CREATE 
        // Suspect Hacker Wallet
        (w_hack:WalletAddress {address: '0xHackeR001', balance: 5.2, risk_score: 95, label: 'Suspicious'}),
        
        // Money Mule Wallets (Intermediate Hops)
        (w_mule1:WalletAddress {address: '0xMule1111', balance: 1.5, risk_score: 80, label: 'Intermediary'}),
        (w_mule2:WalletAddress {address: '0xMule2222', balance: 0.8, risk_score: 75, label: 'Intermediary'}),
        (w_mule3:WalletAddress {address: '0xMule3333', balance: 2.1, risk_score: 70, label: 'Intermediary'}),
        (w_mule4:WalletAddress {address: '0xMule4444', balance: 0.4, risk_score: 60, label: 'Intermediary'}),
        
        // Mixer Interaction Wallets
        (w_mix_in:WalletAddress {address: '0xMixInlet', balance: 10.0, risk_score: 90, label: 'Mixer Deposit'}),
        (w_mix_out:WalletAddress {address: '0xMixOutlet', balance: 0.2, risk_score: 85, label: 'Mixer Withdrawal'}),
        
        // Clean-looking Secondary Wallets
        (w_clean1:WalletAddress {address: '0xCleanUserA', balance: 3.4, risk_score: 20, label: 'User'}),
        (w_clean2:WalletAddress {address: '0xCleanUserB', balance: 1.1, risk_score: 15, label: 'User'}),
        
        // Exchange Deposit Wallets (Cash-out points)
        (w_bin_dep:WalletAddress {address: '0xBinanceDep', balance: 0.0, risk_score: 40, label: 'Deposit'}),
        (w_coin_dep:WalletAddress {address: '0xCoinbaseDep', balance: 0.0, risk_score: 30, label: 'Deposit'})
    """
    )

    # --- 4. LINK WALLETS TO VASPS (BELONGS_TO) ---
    tx.run(
        """
        MATCH (w_mix_in:WalletAddress {address: '0xMixInlet'}),
              (w_mix_out:WalletAddress {address: '0xMixOutlet'}),
              (m:VASP {entity_id: 'VASP_TORNADO'})
        CREATE (w_mix_in)-[:BELONGS_TO]->(m),
               (w_mix_out)-[:BELONGS_TO]->(m)
    """
    )

    tx.run(
        """
        MATCH (w_bin_dep:WalletAddress {address: '0xBinanceDep'}),
              (b:VASP {entity_id: 'VASP_BINANCE'})
        CREATE (w_bin_dep)-[:BELONGS_TO]->(b)
    """
    )

    tx.run(
        """
        MATCH (w_coin_dep:WalletAddress {address: '0xCoinbaseDep'}),
              (c:VASP {entity_id: 'VASP_COINBASE'})
        CREATE (w_coin_dep)-[:BELONGS_TO]->(c)
    """
    )

    # --- 5. CREATE TRANSACTION HOPS (SENT_TO) ---
    tx.run(
        """
        MATCH (w_hack:WalletAddress {address: '0xHackeR001'}),
              (w_mule1:WalletAddress {address: '0xMule1111'}),
              (w_mule2:WalletAddress {address: '0xMule2222'}),
              (w_mule3:WalletAddress {address: '0xMule3333'}),
              (w_mix_in:WalletAddress {address: '0xMixInlet'}),
              (w_mix_out:WalletAddress {address: '0xMixOutlet'}),
              (w_mule4:WalletAddress {address: '0xMule4444'}),
              (w_bin_dep:WalletAddress {address: '0xBinanceDep'}),
              (w_coin_dep:WalletAddress {address: '0xCoinbaseDep'})
        
        // Hop 1: Hacker splits funds to mules
        CREATE (w_hack)-[:SENT_TO {amount: 25.0, timestamp: '2026-03-01T10:00:00Z', tx_hash: '0xTX01'}]->(w_mule1),
               (w_hack)-[:SENT_TO {amount: 15.0, timestamp: '2026-03-01T10:15:00Z', tx_hash: '0xTX02'}]->(w_mule2)
               
        // Hop 2: Mule 1 routes to Mixer; Mule 2 forwards to Mule 3
        CREATE (w_mule1)-[:SENT_TO {amount: 24.5, timestamp: '2026-03-01T11:00:00Z', tx_hash: '0xTX03'}]->(w_mix_in),
               (w_mule2)-[:SENT_TO {amount: 14.8, timestamp: '2026-03-01T11:20:00Z', tx_hash: '0xTX04'}]->(w_mule3)
               
        // Hop 3: Funds exit mixer and move to cash-out exchanges
        CREATE (w_mix_out)-[:SENT_TO {amount: 20.0, timestamp: '2026-03-01T14:00:00Z', tx_hash: '0xTX05'}]->(w_bin_dep),
               (w_mule3)-[:SENT_TO {amount: 14.0, timestamp: '2026-03-01T14:30:00Z', tx_hash: '0xTX06'}]->(w_coin_dep)
    """
    )


def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        with driver.session() as session:
            session.execute_write(seed_database)
            print("Successfully populated Neo4j with mock crypto network data!")
    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        driver.close()


if __name__ == "__main__":
    main()