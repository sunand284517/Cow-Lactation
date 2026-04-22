import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import api from '../utils/api';
import { Upload, Activity, Clock, FileWarning } from 'lucide-react';

const Dashboard = () => {
  const { user } = useContext(AuthContext);
  const [file, setFile] = useState(null);
  const [cowId, setCowId] = useState('');
  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchHistory = async () => {
    try {
      const res = await api.get('/inference/history');
      setHistory(res.data);
    } catch (err) {
      console.error('Failed to fetch history', err);
    }
  };

  useEffect(() => {
    fetchHistory();
    // Poll for updates every 5 seconds
    const interval = setInterval(fetchHistory, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    setIsLoading(true);
    setError('');
    
    const formData = new FormData();
    formData.append('image', file);
    formData.append('cowId', cowId);

    try {
      await api.post('/inference/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setFile(null);
      setCowId('');
      fetchHistory();
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to upload image');
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const statusLower = status.toLowerCase();
    return <span className={`badge badge-${statusLower}`}>{status}</span>;
  };

  return (
    <div className="container animate-fade-in">
      <div className="text-center mb-2">
        <h1 className="mt-2">Sonogram Analysis Dashboard</h1>
        <p className="text-muted">Upload ultrasound echotextures to classify dairy cow lactation stages</p>
      </div>

      <div className="grid grid-2 mb-2">
        <div className="glass-panel">
          <h3><Upload size={20} style={{ verticalAlign: 'middle', marginRight: '0.5rem' }} /> New Analysis</h3>
          <p className="text-muted mb-1" style={{ fontSize: '0.9rem' }}>Select a cow sonogram image for DL processing</p>
          
          {error && <div style={{ color: 'var(--error)', background: 'rgba(239,68,68,0.1)', padding: '0.75rem', borderRadius: '8px', marginBottom: '1rem' }}>{error}</div>}

          <form onSubmit={handleUpload}>
            <div className="form-group">
              <label className="form-label">Cow ID / Identifier</label>
              <input 
                type="text" 
                className="form-input" 
                value={cowId} 
                onChange={e => setCowId(e.target.value)} 
                required 
                placeholder="e.g. Cow #4052"
              />
            </div>
            <div className="form-group mb-2">
              <label className="form-label">Select Image</label>
              <input 
                type="file" 
                className="form-input" 
                accept="image/*" 
                onChange={e => setFile(e.target.files[0])} 
                required 
              />
            </div>
            
            <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={isLoading || !file}>
              {isLoading ? <div className="spinner"></div> : <><Activity size={18} /> Analyze Sonogram</>}
            </button>
          </form>
        </div>

        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column' }}>
          <h3><Clock size={20} style={{ verticalAlign: 'middle', marginRight: '0.5rem' }} /> Recent Activity</h3>
          <p className="text-muted mb-1" style={{ fontSize: '0.9rem' }}>Real-time updates from ML worker</p>
          
          <div style={{ flex: 1, overflowY: 'auto', maxHeight: '350px', paddingRight: '0.5rem' }}>
            {history.length === 0 ? (
              <div className="text-center text-muted mt-2">
                <FileWarning size={32} style={{ marginBottom: '1rem', opacity: 0.5 }} />
                <p>No sonograms analyzed yet</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {history.map((item) => (
                  <div key={item._id} style={{ background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', padding: '1rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <strong style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        {item.cowId}
                      </strong>
                      {getStatusBadge(item.status)}
                    </div>
                    {item.classification && (
                      <div style={{ marginTop: '0.75rem', padding: '0.75rem', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '8px', borderLeft: '3px solid var(--success)' }}>
                        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Classified Stage:</div>
                        <div style={{ fontWeight: '600', color: 'var(--success)' }}>{item.classification}</div>
                        {item.confidence && (
                          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Confidence: {(item.confidence * 100).toFixed(1)}%</div>
                        )}
                        {item.predictedYield !== undefined && item.predictedYield !== null && (
                          <div style={{ marginTop: '0.5rem', paddingTop: '0.5rem', borderTop: '1px solid rgba(16, 185, 129, 0.2)' }}>
                             <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Predicted DMY:</div>
                             <div style={{ fontWeight: '600', color: 'var(--success)' }}>{item.predictedYield.toFixed(2)} Liters/Day</div>
                          </div>
                        )}
                      </div>
                    )}
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.75rem', textAlign: 'right' }}>
                      {new Date(item.createdAt).toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
