import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import VeterinaryAssistance from './pages/VeterinaryAssistance.jsx'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/veterinary" replace />} />
        <Route path="/veterinary" element={<VeterinaryAssistance />} />
        <Route path="*" element={<Navigate to="/veterinary" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
