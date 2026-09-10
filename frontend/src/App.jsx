import { useState, useEffect, useCallback } from 'react';
import { ReactFlow, Background, Controls, applyNodeChanges } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import axios from 'axios';
import Portal from './Portal';

const API_BASE_URL = 'http://localhost:8000';

export default function App() {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [searchAddress, setSearchAddress] = useState('232022460');
  const [selectedWallet, setSelectedWallet] = useState(null);
  const [walletDetails, setWalletDetails] = useState(null);
  const [viewMode, setViewMode] = useState('tracer'); // 'tracer' or 'portal'

  const onNodesChange = useCallback(
    (changes) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  );

  const fetchTrace = (address) => {
    axios.get(`${API_BASE_URL}/api/v1/trace/${address}`)
      .then(response => {
        const traceData = response.data.trace_results;
        const newNodes = [];
        const newEdges = [];
        const seenNodes = new Set();
        let gridCounter = 0; 
        const cryptoCoins = ['BTC', 'ETH', 'USDT', 'SOL', 'USDC'];

        const allSenders = new Set(traceData.map(t => t.search_target));

        traceData.forEach((tx, index) => {
          const getGridPosition = () => {
            const row = Math.floor(gridCounter / 5);
            const col = gridCounter % 5;
            gridCounter++;
            return { x: 100 + (col * 240), y: 250 + (row * 150) };
          };

          if (!seenNodes.has(tx.search_target)) {
            const isMainSearch = tx.search_target === address;
            newNodes.push({
              id: tx.search_target,
              position: isMainSearch ? { x: 550, y: 50 } : getGridPosition(),
              data: { 
                label: `🚨 Suspect: ${tx.search_target}`,
                flowStatus: isMainSearch ? '🚨 Source Ingress / Initial Deposit' : '🔄 Transit / Layering Mule'
              },
              style: { backgroundColor: '#ff4d4f', color: '#fff', padding: '10px', borderRadius: '8px', fontWeight: 'bold' }
            });
            seenNodes.add(tx.search_target);
          }

          if (!seenNodes.has(tx.connected_wallet)) {
            const isCashOut = !allSenders.has(tx.connected_wallet);

            newNodes.push({
              id: tx.connected_wallet,
              position: getGridPosition(),
              data: { 
                label: isCashOut ? `🏦 Cash-Out: ${tx.connected_wallet}` : tx.connected_wallet,
                flowStatus: isCashOut ? '🏦 Fiat Withdrawal / Off-Ramp Endpoint' : '🔄 Transit / Layering Mule'
              },
              style: isCashOut 
                ? { backgroundColor: '#10b981', color: '#fff', padding: '10px', borderRadius: '8px', fontWeight: 'bold', border: '2px solid #059669' } 
                : { backgroundColor: '#1890ff', color: '#fff', padding: '10px', borderRadius: '8px' } 
            });
            seenNodes.add(tx.connected_wallet);
          }

          const displayCoin = cryptoCoins[index % cryptoCoins.length];
          newEdges.push({
            id: `edge-${tx.search_target}-${tx.connected_wallet}-${index}`,
            source: tx.search_target,
            target: tx.connected_wallet,
            label: `${tx.amount} ${displayCoin}`,
            animated: true,
            style: { stroke: '#ff7875', strokeWidth: 2 }
          });
        });

        setNodes(newNodes);
        setEdges(newEdges);
      })
      .catch(err => console.error("Trace error:", err));
  };

  useEffect(() => {
    fetchTrace(searchAddress);
  }, []);

  const onNodeClick = (_, node) => {
    setSelectedWallet(node.id);
    
    Promise.all([
      axios.get(`${API_BASE_URL}/api/v1/wallet/${node.id}`),
      axios.get(`${API_BASE_URL}/api/v1/vasp/identify/${node.id}`)
    ])
    .then(([walletRes, vaspRes]) => {
      setWalletDetails({
        ...walletRes.data,
        vasp: vaspRes.data
      });
    })
    .catch(err => {
      console.error("Metadata fetch error:", err);
      setWalletDetails({ balance: 'N/A', risk_score: 'N/A', vasp: { vasp_name: 'Unknown', category: 'N/A' } });
    });
  };

  // Switch to Sahyog Portal view if toggled
  if (viewMode === 'portal') {
    return <Portal onBack={() => setViewMode('tracer')} />;
  }

  return (
    <div style={{ width: '100vw', height: '100vh', backgroundColor: '#0f172a', position: 'relative' }}>
      <div style={{ position: 'absolute', top: 16, left: 16, zIndex: 10, display: 'flex', gap: '8px', alignItems: 'center' }}>
        <input 
          type="text" 
          value={searchAddress} 
          onChange={(e) => setSearchAddress(e.target.value)}
          placeholder="Enter wallet address..."
          style={{ padding: '8px 12px', borderRadius: '6px', border: '1px solid #334155', backgroundColor: '#1e293b', color: '#fff', width: '260px' }}
        />
        <button 
          onClick={() => fetchTrace(searchAddress)}
          style={{ padding: '8px 16px', backgroundColor: '#2563eb', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}
        >
          Trace Network
        </button>
        <button 
          onClick={() => setViewMode('portal')}
          style={{ padding: '8px 16px', backgroundColor: '#059669', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}
        >
          🏛️ Open Sahyog Portal
        </button>
      </div>

      {selectedWallet && (
        <div style={{ 
          position: 'fixed', 
          top: '20px', 
          right: '20px', 
          zIndex: 1000, 
          width: '300px', 
          maxWidth: 'calc(100vw - 40px)',
          maxHeight: 'calc(100vh - 40px)',
          overflowY: 'auto',
          backgroundColor: '#1e293b', 
          padding: '20px', 
          borderRadius: '12px', 
          color: '#ffffff', 
          boxShadow: '0 10px 25px rgba(0, 0, 0, 0.5)',
          border: '1px solid #334155' 
        }}>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '18px', fontWeight: 'bold' }}>Forensic Inspector</h3>
          <p style={{ wordBreak: 'break-all', fontSize: '14px' }}><strong>Address:</strong> {selectedWallet}</p>
          
          <div style={{ backgroundColor: '#334155', padding: '10px', borderRadius: '8px', margin: '12px 0', borderLeft: '4px solid #38bdf8' }}>
             <span style={{ fontSize: '12px', fontWeight: 'bold', color: '#94a3b8', textTransform: 'uppercase' }}>Trace Flow Status</span><br/>
             <span style={{ fontSize: '14px', color: '#fff', fontWeight: 'bold' }}>
               {nodes.find(n => n.id === selectedWallet)?.data?.flowStatus || 'Unknown Flow'}
             </span>
          </div>

          {walletDetails ? (
            <div style={{ fontSize: '14px', lineHeight: '1.6' }}>
              <p><strong>Balance:</strong> {walletDetails.balance ?? 'N/A'} BTC</p>
              <p><strong>Risk Score:</strong> <span style={{ color: walletDetails.vasp?.risk_score > 70 ? '#f87171' : '#4ade80', fontWeight: 'bold' }}>{walletDetails.vasp?.risk_score ?? walletDetails.risk_score ?? 'N/A'} / 100</span></p>
              <p><strong>Entity / VASP:</strong> {walletDetails.vasp?.vasp_name || 'Unclassified'}</p>
              <p><strong>Category:</strong> {walletDetails.vasp?.category || 'Peer-to-Peer Transfer'}</p>
            </div>
          ) : (
            <p style={{ fontSize: '12px', color: '#94a3b8' }}>Loading forensic data...</p>
          )}

          {/* 📄 GENERATE & FILE SAR BUTTON WITH DYNAMIC VASP PARAMS */}
          <button 
            onClick={() => {
              const currentVasp = walletDetails?.vasp?.vasp_name || 'Unattributed Entity';
              const currentCategory = walletDetails?.vasp?.category || 'Peer-to-Peer Transfer';
              const currentRisk = walletDetails?.vasp?.risk_score || 85;

              axios.get(`${API_BASE_URL}/api/v1/generate-sar/${selectedWallet}?vasp_name=${encodeURIComponent(currentVasp)}&category=${encodeURIComponent(currentCategory)}&risk_score=${currentRisk}`)
                .then(res => {
                  const pdfUrl = res.data.download_url;
                  
                  // Open the generated PDF in a new tab
                  window.open(`${API_BASE_URL}${pdfUrl}`, '_blank');

                  // Automatically File to Sahyog Portal Backend WITH the PDF URL included
                  return axios.post(`${API_BASE_URL}/api/v1/sahyog/submit-report`, {
                    wallet_address: selectedWallet,
                    risk_score: currentRisk,
                    vasp_name: currentVasp,
                    download_url: pdfUrl
                  });
                })
                .then(() => {
                  alert("🚨 SAR successfully transmitted & filed to Sahyog Intelligence Portal!");
                })
                .catch(err => console.error("Report generation or submission error:", err));
            }}
            style={{ 
              marginTop: '12px', 
              width: '100%',
              padding: '8px 16px', 
              fontSize: '14px',
              backgroundColor: '#10b981', 
              color: '#fff', 
              border: 'none', 
              borderRadius: '6px', 
              cursor: 'pointer',
              fontWeight: 'bold'
            }}
          >
            📄 Generate & File SAR Report
          </button>
          
          <button 
            onClick={() => setSelectedWallet(null)} 
            style={{ 
              marginTop: '8px', 
              width: '100%',
              padding: '8px 16px', 
              fontSize: '14px',
              backgroundColor: '#334155', 
              color: '#fff', 
              border: 'none', 
              borderRadius: '6px', 
              cursor: 'pointer',
              fontWeight: 'bold'
            }}
          >
            Close
          </button>
        </div>
      )}

      <ReactFlow 
        nodes={nodes} 
        edges={edges} 
        onNodesChange={onNodesChange}
        onNodeClick={onNodeClick}
        fitView 
        colorMode="dark"
        minZoom={0.1}
        maxZoom={2.0}
      >
        <Background color="#334155" gap={20} />
        <Controls />
      </ReactFlow>
    </div>
  );
}