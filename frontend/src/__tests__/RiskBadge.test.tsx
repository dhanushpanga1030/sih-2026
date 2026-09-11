import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import RiskBadge from '../components/RiskBadge'

describe('RiskBadge', () => {
  it('renders Immediate band', () => {
    render(<RiskBadge band="immediate" />)
    expect(screen.getByText('Immediate')).toBeInTheDocument()
  })

  it('renders Short-term band', () => {
    render(<RiskBadge band="short_term" />)
    expect(screen.getByText('Short-term')).toBeInTheDocument()
  })

  it('renders Medium-term band', () => {
    render(<RiskBadge band="medium_term" />)
    expect(screen.getByText('Medium-term')).toBeInTheDocument()
  })

  it('renders Monitor band', () => {
    render(<RiskBadge band="monitor" />)
    expect(screen.getByText('Monitor')).toBeInTheDocument()
  })

  it('renders raw label for unknown band', () => {
    render(<RiskBadge band="unknown" />)
    expect(screen.getByText('unknown')).toBeInTheDocument()
  })
})
