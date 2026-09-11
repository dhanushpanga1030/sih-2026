import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect } from 'vitest'
import Header from '../components/Header'

describe('Header', () => {
  it('renders project name', () => {
    render(
      <BrowserRouter>
        <Header />
      </BrowserRouter>
    )
    expect(screen.getByText('SafeHabitat AI')).toBeInTheDocument()
  })

  it('renders nav links', () => {
    render(
      <BrowserRouter>
        <Header />
      </BrowserRouter>
    )
    expect(screen.getByText('State Overview')).toBeInTheDocument()
    expect(screen.getByText('Scenario Simulation')).toBeInTheDocument()
  })
})
