import { describe, expect, it } from 'vitest'
import { formatCurrency } from '../src/formatCurrency'

describe('formatCurrency', () => {
  it('formats cents as a USD amount', () => {
    expect(formatCurrency(1299)).toBe('$12.99')
  })
})

