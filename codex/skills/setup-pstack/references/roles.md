# pstack roles

Use the active session model by default. Only record other models that the target installation reports as available.

| Role | Default |
| --- | --- |
| feature, refactoring | inherit-parent |
| bug-fix | inherit-parent |
| perf-issue | inherit-parent |
| hillclimb | inherit-parent |
| judgment and prose | inherit-parent |
| hardest tasks | inherit-parent |
| how explorer | inherit-parent |
| how explainer | inherit-parent |
| why investigators | inherit-parent |
| why synthesizer | inherit-parent |
| reflect tooling | inherit-parent |
| reflect judgment, divergent, synthesizer | inherit-parent |
| arena runners | inherit-parent, inherit-parent |
| arena cross-judge pool | empty until another available model family is configured |
| swarm workers | inherit-parent |
| architect runners | inherit-parent, inherit-parent |
| interrogate reviewers | inherit-parent, inherit-parent |

Panel lists launch one delegate per entry. Order the arena cross-judge pool by preference; the first available model from a different family may judge. `inherit-parent` and `auto` do not provide a different family and must not be used as cross-judges. If no eligible family is configured, skip that cross-judge step and disclose the limitation.
