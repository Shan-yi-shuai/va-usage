# Segmentation Policy

The main segmentation risk is over-structuring narrative text. Use these rules.

## Case

A `CaseStudySpec` should correspond to one coherent analysis scenario.

Determine the number of cases from narrative text first. Figures and captions can strengthen or localize the interpretation, but they should not be the sole basis for deciding how many cases exist.

Start a new case when:

- the paper explicitly presents a different scenario or dataset use
- a new analyst role or analysis objective appears
- the narrative resets to a distinct end-to-end story

Do not assume one `case_study` figure equals one case.
Do not assume the absence of a dedicated figure means the case does not exist.

## Episode

An `Episode` should correspond to a local analytic goal or phase inside the case.

Good episode boundaries usually align with:

- a new subgoal
- a new candidate or explanation being investigated
- a move from exploration to validation or reporting
- a clear shift in the main view set or evidence source

Do not create episodes for every paragraph.
An episode should usually contain one or more steps, not just a paragraph summary.
Episodes are higher-level phase boundaries inside a case; they usually imply stage progression from one local goal to the next.

## Step

A `UsageStep` is the smallest semantic unit that still has analytic meaning.
A step is not the smallest UI action. It is the smallest process unit that still has an independent local purpose or result.
A step should ideally capture one local analytic advance rather than a whole mini-story.

A step should usually contain at least one of:

- a clear intent
- a meaningful operation
- an observation
- an insight
- a decision
- a question or hypothesis event

Do not create steps for click-level details unless the paper explicitly makes them analytically meaningful.

Relationship to sub-views:

- sub-views are structure units from the system specification
- steps are process units in the case-study narrative
- a step should explicitly record directly involved sub-views in `usedViews`
- a step does not need to map one-to-one to a single sub-view
- a step may involve observing multiple sub-views when they jointly support one local purpose
- if one sub-view appears alone but belongs to a parent view whose sibling sub-views usually work together, check whether the paper likely omitted the sibling relationship by default; when the local purpose clearly depends on both, include the jointly involved sibling sub-views in `usedViews`

Split a step when:

- there is a clear sequential move to a different local purpose
- the analyst first uses one sub-view for one purpose and then another sub-view for a different purpose
- the analyst acts in source `A` and later reads updated target `B` to form a new insight; the target-side reading belongs to the next step
- one narrative chunk contains multiple local advances such as observe -> interact -> read updated result
- keeping them together would hide meaningful step-to-step progression

Keep one step when:

- multiple sub-views are used together for the same local purpose
- the analyst is simultaneously comparing or cross-checking sub-views to reach one local result
- multiple sub-views are jointly involved in one local purpose, even if one of them reflects an update caused by an earlier interaction
- one sibling sub-view is explicitly mentioned while another sibling sub-view in the same parent view is only implicitly involved because the paper assumes their relationship is obvious

When in doubt:

- prefer semantically meaningful steps, but do not keep multiple local advances inside one summarized step
- keep the original text in `rawNarrative`
- mark uncertainty through evidence and `inferenceType`, not by forcing extra structure
