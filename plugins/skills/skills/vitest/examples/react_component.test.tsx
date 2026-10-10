import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { StatusBadge } from '../src/StatusBadge'

// Requires @testing-library/jest-dom/vitest in the project's Vitest setup file.
describe('StatusBadge', () => {
  it('shows the current status', () => {
    render(<StatusBadge status="Ready" />)

    expect(screen.getByText('Ready')).toBeInTheDocument()
  })
})
