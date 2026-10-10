import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import StatusBadge from '../src/StatusBadge.vue'

describe('StatusBadge', () => {
  it('shows the current status', () => {
    const wrapper = mount(StatusBadge, {
      props: { status: 'Ready' },
    })

    expect(wrapper.text()).toContain('Ready')
  })
})

