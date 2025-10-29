import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard/Dashboard';
import Photos from './pages/Photos/Photos';
import Detections from './pages/Detections/Detections';
import LiveView from './pages/LiveView/LiveView';

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="photos" element={<Photos />} />
        <Route path="detections" element={<Detections />} />
        <Route path="live" element={<LiveView />} />
      </Route>
    </Routes>
  );
}
