import { useState, useEffect, useCallback } from 'react';
import { ReactFlow, Background, Controls, applyNodeChanges } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import axios from 'axios';

export default function App() {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [searchAddress, setSearchAddress] = useState('0xHackeR001');
  const [selectedWallet, setSelectedWallet] = useState(null);
  const [walletDetails, setWalletDetails] = useState(null);

  // Allow nodes to be dragged around the screen
  const onNodesChange = useCallback(
    (changes) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  );

  // Fetch graph connections for a target address from your FastAPI backend
  const fetchTrace = (address) => {
    axios.get(`http://localhost:8000/api/v1/trace/${address}`)
      .then(response => {
        const traceData = response.data.trace_results;
        const newNodes = [];
        const newEdges = [];
        const seenNodes = new Set();

        traceData.forEach((tx, index) => {
          if (!seenNodes.has(tx.search_target)) {
            newNodes.push({
              id: tx.search_target,
              position: { x: 350, y: 80 },
              data: { label: `🚨 Suspect: ${tx.search_target}` },
              style: { backgroundColor: '#ff4d4f', color: '#fff', padding: '10px', borderRadius: '8px', fontWeight: 'bold' }
            });
            seenNodes.add(tx.search_target);
          }

          if (!seenNodes.has(tx.connected_wallet)) {
            newNodes.push({
              id: tx.connected_wallet,
              position: { x: 100 + (index * 220), y: 280 },
              data: { label: tx.connected_wallet },
              style: { backgroundColor: '#1890ff', color: '#fff', padding: '10px', borderRadius: '8px' }
            });
            seenNodes.add(tx.connected_wallet);
          }

          newEdges.push({
            id: `edge-${tx.search_target}-${tx.connected_wallet}-${index}`,
            source: tx.search_target,
            target: tx.connected_wallet,
            label: `${tx.amount} BTC`,
            animated: true,
            style: { stroke: '#ff7875', strokeWidth: 2 }
          });
        });

        setNodes(newNodes);
        setEdges(newEdges);
      })
      .catch(err => console.error("Trace error:", err));
  };

  // Run initial trace on load
  useEffect(() => {
    fetchTrace('0xHackeR001');
  }, []);

  // When a user clicks a node, open the sidebar and fetch wallet metadata & VASP details
  const onNodeClick = (_, node) => {
    setSelectedWallet(node.id);
    
    Promise.all([
      axios.get(`http://localhost:8000/api/v1/wallet/${node.id}`),
      axios.get(`http://localhost:8000/api/v1/vasp/identify/${node.id}`)
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

  return (
    <div style={{ width: '100vw', height: '100vh', backgroundColor: '#0f172a', position: 'relative' }}>
      {/* Top Search Header */}
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
      </div>

      {/* Side Forensic Inspector Panel */}
      {selectedWallet && (
        <div style={{ position: 'absolute', top: 16, right: 16, zIndex: 10, width: '280px', backgroundColor: '#1e293b', padding: '16px', borderRadius: '8px', color: '#fff', border: '1px solid #334155' }}>
          <h3 style={{ margin: '0 0 10px 0', fontSize: '16px' }}>Forensic Inspector</h3>
          <p style={{ wordBreak: 'break-all', fontSize: '13px' }}><strong>Address:</strong> {selectedWallet}</p>
          {walletDetails ? (
            <div style={{ fontSize: '13px', lineHeight: '1.6' }}>
              <p><strong>Balance:</strong> {walletDetails.balance ?? 'N/A'} BTC</p>
              <p><strong>Risk Score:</strong> <span style={{ color: walletDetails.risk_score > 70 ? '#f87171' : '#4ade80' }}>{walletDetails.risk_score ?? 'N/A'}/100</span></p>
              <p><strong>Entity / VASP:</strong> {walletDetails.vasp?.vasp_name || 'Unlabeled'}</p>
              <p><strong>Category:</strong> {walletDetails.vasp?.category || 'Peer-to-Peer'}</p>
            </div>
          ) : (
            <p style={{ fontSize: '12px', color: '#94a3b8' }}>Loading forensic data...</p>
          )}
          <button 
            onClick={() => setSelectedWallet(null)} 
            style={{ marginTop: '8px', padding: '4px 8px', fontSize: '12px', backgroundColor: '#334155', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
          >
            Close
          </button>
        </div>
      )}

      {/* React Flow Canvas */}
      <ReactFlow 
        nodes={nodes} 
        edges={edges} 
        onNodesChange={onNodesChange}
        onNodeClick={onNodeClick}
        fitView 
        colorMode="dark"
      >
        <Background color="#334155" gap={20} />
        <Controls />
      </ReactFlow>
    </div>
  );
}