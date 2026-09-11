import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import SHAPWaterfall from '../components/SHAPWaterfall'

describe('SHAPWaterfall', () => {
  it('renders chart title', () => {
    render(
      <SHAPWaterfall
        contributions={{ flood_score: 0.3, pop_density: -0.1 }}
      />
    )
    expect(screen.getByText('Feature Contributions (SHAP)')).toBeInTheDocument()
  })

  it('renders legend', () => {
    render(
      <SHAPWaterfall contributions={{ flood_score: 0.3 }} />
    )
    expect(screen.getByText(/Increases risk/)).toBeInTheDocument()
    expect(screen.getByText(/Decreases risk/)).toBeInTheDocument()
  })

  it('renders without contributions', () => {
    render(<SHAPWaterfall contributions={{}} />)
    expect(screen.getByText('Feature Contributions (SHAP)')).toBeInTheDocument()
  })
})
