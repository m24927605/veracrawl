# Contract: Network And Browser Safety Policy

## Gates

- egress allowlist
- private network denylist
- robots policy
- rate budget
- response size budget
- redirect budget and redirect target policy
- runtime timeout
- browser side-effect class
- browser DOM/screenshot/network log size budget

## Required Non-Success Statuses

- `egress_denied`
- `private_network_denied`
- `robots_blocked`
- `rate_budget_exceeded`
- `size_budget_exceeded`
- `redirect_denied`
- `network_timeout`
- `unsafe_browser_side_effect`

## Rules

- Egress and private-network gates run before network execution.
- Robots, rate, size, redirect, and timeout gates produce typed reports.
- Browser side-effect gate runs before DOM/screenshot/network artifact acceptance.
- Every denied gate must produce operator-visible diagnostics and replay refs.
