import React from 'react'
import VeterinaryLocator from '../components/VeterinaryLocator.jsx'

/**
 * VeterinaryAssistance — standalone page.
 *
 * To integrate with your disease-risk module, pass props:
 *   <VeterinaryAssistance riskLevel="high" animalName="Dairy Cow #3" />
 *
 * riskLevel: "low" | "moderate" | "high" | "critical"
 */
export default function VeterinaryAssistance({
  riskLevel,
  animalName,
}) {
  return (
    <div
      style={{
        minHeight: '100vh',
        background: '#f1f8e9',
      }}
    >
      <VeterinaryLocator
        riskLevel={riskLevel}
        animalName={animalName}
      />
    </div>
  )
}