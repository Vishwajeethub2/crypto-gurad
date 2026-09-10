import { useState, useEffect } from 'react';
import axios from 'axios';

export default function Portal({ onBack }) {
  const [reports, setReports] = useState([]);

  useEffect(() => {
    axios.get('http://localhost:8000/api/v1/sahyog/reports')
      .then(res => setReports(res.data.reports || []))
      .catch(err => console.error(err));
  }, []);

  return (
    <div style={{ width: '100vw', height: '100vh', backgroundColor: '#090d16', color: '#fff', padding: '30px', fontFamily: 'sans-serif', boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #1e293b', paddingBottom: '20px', marginBottom: '30px' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '24px', color: '#38bdf8' }}>🏛️ Sahyog Financial Intelligence Portal</h1>
          <p style={{ margin: '5px 0 0 0', color: '#94a3b8', fontSize: '14px' }}>National AML / CFT Suspicious Activity Report (SAR) Intake Gateway</p>
        </div>
        <button 
          onClick={onBack}
          style={{ padding: '10px 20px', backgroundColor: '#334155', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}
        >
          ⬅️ Back to Crypto Guard Tracer
        </button>
      </div>

      <h3 style={{ fontSize: '18px', marginBottom: '15px' }}>Incoming Electronic Filings ({reports.length})</h3>

      {reports.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px', backgroundColor: '#1e293b', borderRadius: '12px', color: '#94a3b8' }}>
          <p style={{ fontSize: '16px' }}>No active filings received yet.</p>
          <p style={{ fontSize: '13px' }}>Go back to the tracer, select a suspect wallet, and click "Generate & File SAR Report".</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {reports.map((r, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#1e293b', padding: '16px 20px', borderRadius: '8px', borderLeft: '4px solid #10b981' }}>
              <div>
                <span style={{ fontSize: '12px', fontWeight: 'bold', color: '#38bdf8' }}>{r.id}</span>
                <h4 style={{ margin: '4px 0', fontSize: '16px' }}>Target Wallet: {r.wallet_address}</h4>
                <p style={{ margin: '4px 0', fontSize: '13px', color: '#94a3b8' }}>Associated Entity: <strong>{r.vasp_name}</strong> | Filed at: {r.timestamp}</p>
                
                {/* 📂 VIEW FILED PDF REPORT BUTTON */}
                {r.download_url && (
                  <button 
                    onClick={() => window.open(`http://localhost:8000${r.download_url}`, '_blank')}
                    style={{ marginTop: '8px', padding: '6px 12px', backgroundColor: '#2563eb', color: '#fff', border: 'none', borderRadius: '4px', fontSize: '12px', cursor: 'pointer', fontWeight: 'bold' }}
                  >
                    📂 View Filed PDF Report
                  </button>
                )}
              </div>
              <div style={{ textAlign: 'right' }}>
                <span style={{ display: 'inline-block', padding: '4px 10px', borderRadius: '4px', backgroundColor: '#fef2f2', color: '#dc2626', fontWeight: 'bold', fontSize: '12px', marginBottom: '6px' }}>
                  Risk Score: {r.risk_score}/100
                </span><br/>
                <span style={{ fontSize: '12px', color: '#10b981', fontWeight: 'bold' }}>● {r.status}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}