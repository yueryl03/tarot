# Tarot Drawing Engine: Mathematical Model and Design Principles

> **Tarot Engine — Probability, Randomness & Physical-Deck Simulation**  
> **Document type:** Technical Concept / Mathematical Design Note  
> **Scope:** A standard 78-card tarot deck, upright/reversed orientations, shuffling, drawing without replacement, spreads, and interactive card selection  
> **Purpose:** This document explains **why the system is designed this way**. It is not an installation guide, API reference, or AI interpretation prompt.

---

## 1. Objectives and Core Principles

The project aims to approximate the experience of using a **physical tarot deck** with a mathematically testable digital model: shuffle a deck, determine card orientations, choose face-down cards, and place revealed cards into a spread without drawing the same physical card twice within one reading.

The core principles are:

1. **There are 78 cards, not 156.** Upright and reversed are two possible *states* of one card, not two distinct physical cards.
2. **Shuffle once per reading.** The shuffled order and each card's orientation remain fixed for that reading.
3. **Draw without replacement.** After a card has been drawn, it cannot appear again, even with the opposite orientation.
4. **Randomness belongs to the Tarot Engine.** An LLM may interpret results but must never choose, alter, or redraw cards.
5. **The frontend cannot inspect hidden cards.** Users may select face-down positions, but only the backend knows which cards occupy those positions.

This is an **idealised digital shuffling model**. It does not claim that every person shuffling a physical deck by hand produces the same statistical distribution.

---

## 2. Mathematical Definitions

Let:

- $N = 78$ be the number of cards in the deck.
- $D = \{c_1, c_2, \ldots, c_{78}\}$ be the set of 78 **distinct physical cards**.
- $\pi$ be a permutation representing the shuffled deck order.
- $O_i \in \{U, R\}$ be the orientation of card $c_i$, where $U$ means *upright* and $R$ means *reversed*.
- $n$ be the number of cards required by the selected spread (e.g., 1, 3, 5, or 10).
- $K$ be the number of reversed cards among the $n$ cards drawn.

### 2.1 Deck Composition

| Category | Number of cards | Probability on the first draw |
|---|---:|---:|
| Major Arcana | 22 | $22/78 \approx 28.21\%$ |
| Minor Arcana | 56 | $56/78 \approx 71.79\%$ |
| **Total** | **78** | **100%** |

The Minor Arcana contains four suits—Wands, Cups, Swords, and Pentacles—with 14 cards per suit.

### 2.2 Two Independent Random Decisions

The default model has two components:

1. **Uniform shuffle:** All $78!$ possible deck permutations are equally likely.
2. **Independent orientations:** Each card has $P(U)=0.5$ and $P(R)=0.5$. Card orientations are independent of one another and independent of the shuffle.

> **An explicit design choice, not a universal law of tarot:** Some readers never use reversals; others turn or mix cards in different ways. The 50%/50% assumption is a transparent, symmetric digital model, not a claim about the outcomes of actual hand shuffling.

---

## 3. Probability of Drawing One Card

For the first draw from a uniformly shuffled 78-card deck:

$$
P(\text{a particular card}) = \frac{1}{78} \approx 1.2821\%.
$$

If we also require a particular orientation—for example, **The Fool upright**—then:

$$
\begin{aligned}
P(\text{The Fool upright})
&= P(\text{The Fool})\,P(U\mid\text{The Fool})\\
&= \frac{1}{78}\times\frac{1}{2}\\
&= \frac{1}{156} \approx 0.6410\%.
\end{aligned}
$$

Likewise, $P(\text{The Fool reversed})=1/156$.

**Important distinction:** There are $78\times2=156$ equally likely *card-and-orientation outcomes for one draw*, but there are still only **78 physical cards**. Drawing The Fool upright means The Fool reversed cannot subsequently appear in the same reading.

---

## 4. Multiple Draws and Sampling Without Replacement

After each draw, there is one fewer available card.

| Draw position | Available cards | Conditional probability of a particular undrawn card |
|---|---:|---:|
| First | 78 | $1/78$ |
| Second | 77 | $1/77$ |
| Third | 76 | $1/76$ |
| $(k+1)$th | $78-k$ | $1/(78-k)$ |

These probabilities assume the specified card **has not already been drawn**. Once that card has appeared, its probability of appearing again is zero.

If we additionally require a specified orientation, and that card's orientation remains unobserved, then:

$$
P(\text{next card is a specified remaining card with a specified orientation}
\mid \text{card is still available}) = \frac{1}{2(78-k)}.
$$

### 4.1 Ordered Spreads

Tarot spreads usually assign meaning to positions—for example, **Past → Present → Future**. Therefore, A–B–C and C–B–A are different reading outcomes.

For $n$ **particular distinct cards in a particular order and with particular orientations**, the probability is:

$$
\begin{aligned}
P(\text{a specified ordered result})
&= \frac{1}{78\times77\times\cdots\times(78-n+1)}\left(\frac12\right)^n\\
&= \frac{(78-n)!}{78!\,2^n}.
\end{aligned}
$$

The number of possible ordered results is:

$$
\#(\text{ordered results with }n\text{ cards}) = \frac{78!}{(78-n)!}\,2^n.
$$

For a **three-card spread**:

$$
\# = 78\times77\times76\times2^3 = 3,651,648.
$$

Therefore, the probability of one exact three-card combination **including order and orientations** is:

$$
\boxed{P = \frac{1}{3,651,648} \approx 0.00002738\%.}
$$

If **order does not matter**, and we only ask whether a particular set of three cards appears with particular orientations, the sample space contains $\binom{78}{3}2^3=608,608$ equally likely unordered outcomes. The probability of one specified unordered outcome is $1/608,608$.

The difference is whether **spread position matters**.

---

## 5. Number of Reversed Cards: Binomial Distribution

Because card orientations are sampled independently at 50% each, the number $K$ of reversed cards in an $n$-card draw follows a **binomial distribution**:

$$
K\sim\operatorname{Binomial}(n,0.5).
$$

$$
\boxed{P(K=k) = \binom{n}{k}(0.5)^k(0.5)^{n-k} = \frac{\binom{n}{k}}{2^n}.}
$$

### 5.1 Example: Three-Card Spread

| Number of reversed cards ($k$) | Calculation | Probability |
|---|---|---:|
| 0 | $\binom{3}{0}/8$ | 12.5% |
| 1 | $\binom{3}{1}/8$ | 37.5% |
| 2 | $\binom{3}{2}/8$ | 37.5% |
| 3 | $\binom{3}{3}/8$ | 12.5% |

The probability of **at least one reversed card** among three cards is:

$$
P(K\ge1)=1-P(K=0)=1-(0.5)^3=87.5\%.
$$

### 5.2 Must a Full Deck Have Exactly 39 Reversed Cards?

**No.** With independent orientation assignments:

$$
K_{78}\sim\operatorname{Binomial}(78,0.5),
\qquad E[K_{78}]=39,
\qquad \operatorname{SD}(K_{78})=\sqrt{19.5}\approx4.42.
$$

The value 39 is an **expected count**, not a fixed requirement. A shuffled deck may contain 33, 39, 44, or another number of reversed cards.

Forcing exactly 39 upright and 39 reversed cards produces a **different probability model**: the orientations are no longer independent, and the number of remaining reversed cards depends on those already revealed. This is not the default model used here.

---

## 6. Major Arcana Counts: Hypergeometric Distribution

The question *"How many Major Arcana cards will appear in an $n$-card spread?"* is different from the orientation question. There are only 22 Major Arcana cards, and drawing is **without replacement**, so the relevant distribution is **hypergeometric**.

Let $M$ be the number of Major Arcana cards among $n$ drawn cards. Then:

$$
P(M=m)=\frac{\binom{22}{m}\binom{56}{n-m}}{\binom{78}{n}}.
$$

For example, the probability that a three-card spread contains **at least one Major Arcana card** is:

$$
\begin{aligned}
P(M\ge1)
&=1-P(M=0)\\
&=1-\frac{\binom{56}{3}}{\binom{78}{3}}\\
&\approx63.56\%.
\end{aligned}
$$

If $k$ cards have already been drawn and $a$ of them were Major Arcana, then:

$$
P(\text{next card is Major Arcana}\mid k,a)=\frac{22-a}{78-k}.
$$

**Key comparison:** The number of reversed cards is binomial because orientations are independent in the default model. The number of Major Arcana cards is hypergeometric because physical cards are drawn without replacement.

---

## 7. Does User Selection of Face-Down Cards Affect Fairness?

**No—provided the backend uniformly shuffles the deck first and the user has no information about the hidden card assignments.**

Example workflow:

1. The backend shuffles all 78 cards and fixes their orientations.
2. Cards are assigned to persistent face-down positions, `slot 0` through `slot 77`.
3. The frontend displays only the card backs and their positions—not unrevealed identities or orientations.
4. The user selects `slot 12`, `slot 40`, and `slot 7`, in that order.
5. The backend reveals the cards **already assigned** to those slots, placing them in the spread in selection order.

With a uniformly random hidden permutation, every fixed slot is equally likely to contain any of the 78 cards. If selection does not rely on hidden-card information, selecting positions is **distributionally equivalent** to drawing random cards without replacement.

This separation is crucial: the user's interaction determines **which position is revealed**, not **which card an AI decides ought to occupy that position**.

---

## 8. Shuffling Algorithm: Fisher–Yates with Secure Randomness

### 8.1 Why Fisher–Yates?

Fisher–Yates can generate a permutation in $O(N)$ time and $O(1)$ additional space when performed in place. If each step selects an integer **uniformly** from the correct range, all $78!$ possible permutations are equally likely.

Avoid replacing it with "sort cards by random keys" without carefully considering key collisions and implementation details, which can introduce unnecessary bias.

### 8.2 Python Reference Implementation

```python
import secrets
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class DeckSlot:
    slot_index: int
    card_id: int
    orientation: str


def create_shuffled_deck(
    card_ids: Sequence[int],
    reversals_enabled: bool = True,
) -> list[DeckSlot]:
    """Generate a complete shuffled deck of 78 unique cards."""
    if len(card_ids) != 78 or len(set(card_ids)) != 78:
        raise ValueError("A tarot deck must contain 78 unique card IDs")

    # Secure, unbiased Fisher–Yates shuffle.
    shuffled = list(card_ids)
    for i in range(len(shuffled) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        shuffled[i], shuffled[j] = shuffled[j], shuffled[i]

    return [
        DeckSlot(
            slot_index=i,
            card_id=card_id,
            orientation=(
                "reversed"
                if reversals_enabled and secrets.randbelow(2) == 1
                else "upright"
            ),
        )
        for i, card_id in enumerate(shuffled)
    ]
```

`secrets.randbelow(2)` yields two equally likely outcomes. With `reversals_enabled=False`, every card is assigned the upright orientation.

**Important:** This function creates the **entire deck once**; it is **not** rerun whenever a card is revealed. The generated deck must be persisted so refreshing the page or retrying a request cannot change any hidden card assignments.

---

## 9. Reading State, Persistence, and Invariants

One reading session can be modelled as:

```text
Reading Session
  ├── Question
  ├── Selected Spread (1 / 3 / 5 / 10 / custom cards)
  ├── Shuffled Deck
  │     ├── slot 0  → card + orientation (hidden)
  │     ├── slot 1  → card + orientation (hidden)
  │     └── ...
  │     └── slot 77 → card + orientation (hidden)
  └── Revealed Draws
        ├── draw 1 → chosen slot → spread position 1
        ├── draw 2 → chosen slot → spread position 2
        └── ...
```

The system must always enforce these **invariants**:

- Each reading session has exactly 78 distinct `card_id` values in its deck.
- `slot_index` is unique within a reading session.
- Every card's `orientation` remains fixed within that session.
- A revealed slot cannot be selected again.
- All revealed cards come from that session's previously generated deck.
- The number of draws cannot exceed the selected spread's capacity.
- A batch draw succeeds entirely or fails entirely (atomicity).
- Concurrent draw requests cannot allocate the same slot or spread position twice.
- Public API responses cannot leak unrevealed card identities or orientations.

**Suggested persistence model:** `reading_sessions`, `reading_deck_slots`, `reading_draws`, `tarot_spreads`, and `tarot_spread_positions`, plus a separate catalogue of 78 base tarot cards. Use database transactions, unique constraints, and row-level locks where needed for concurrency safety.

---

## 10. How Spreads Relate to Probability

A spread determines **how many cards to draw** and **what each position means**. Under the default fair-draw model, choosing a different spread should not make particular cards more likely to appear in any given draw position.

| Spread | Number of cards | Example meanings |
|---|---:|---|
| Single Card | 1 | Current guidance |
| Three-Card Spread | 3 | Past / Present / Future |
| Five-Card Spread | 5 | Situation / Challenge / Hidden influence / Advice / Potential outcome |
| Celtic Cross | 10 | Ten distinct traditional spread positions |

Different questions and spreads **must not alter an already shuffled deck**. The AI may adjust the **interpretation** according to a card's position, but it must not retroactively adjust the **drawing probabilities**.

---

## 11. Separate AI Interpretation from the Probability Model

```text
User question + Selected spread
             │
             ▼
      Tarot Engine
 (shuffle → persist → reveal)
             │
             ▼
   Immutable revealed cards
 (card, orientation, position)
             │
             ▼
    AI Interpretation Engine
   (Meanings / RAG / LLM / LoRA)
             │
             ▼
      Reading explanation
```

The **Tarot Engine** is responsible for discrete random sampling and consistent state. The **AI Interpretation Engine** is responsible for natural-language explanations and synthesising card meanings. RAG or LoRA does not make the drawing process "more random" and must not affect its probability distribution.

Symbolic tarot interpretations are **not** statistically validated predictions of future events, real-world outcomes, or another person's thoughts. Thus, the probability of drawing The Lovers cannot be interpreted as the probability that a particular person loves the user. These are fundamentally different probability questions, and the drawing engine does not provide a predictive model for the latter.

---

## 12. How to Test Correctness and Fairness

### 12.1 Required Deterministic Tests

- Every new deck has **exactly 78 unique cards**.
- Slot indices range from 0 to 77 without duplication.
- Every card has exactly one valid orientation.
- Reversal-disabled mode produces no reversed cards.
- A drawn card cannot be drawn again within the same reading.
- Reloading a session does not change the hidden deck order.
- Concurrent draws cannot consume the same card twice.
- Failed transactions do not consume cards.
- Public endpoints never reveal unrevealed card names or orientations.

### 12.2 Optional Statistical Simulation

Generate many independently shuffled decks and examine:

- The relative frequency of each card appearing in the first slot; theoretical probability $1/78$ each.
- The overall fraction of reversed orientations; theoretical expectation 50%.
- The proportions of three-card readings with $0,1,2,3$ reversed cards; theoretical values $12.5\%, 37.5\%, 37.5\%, 12.5\%$.
- The fraction of three-card readings containing at least one Major Arcana card; theoretical probability about 63.56%.

Statistical tests can help detect bias, but **finite samples cannot be expected to match theoretical probabilities exactly**. Use justified confidence intervals or predefined tolerances. Avoid making ordinary CI tests flaky by asserting exact empirical frequencies after relatively few trials.

---

## 13. Frequently Asked Design Questions

**Q1: Should the 78 cards be expanded into 156 entries for upright and reversed?**  
No. Each card has one physical identity; orientation is a state attached to it.

**Q2: Is drawing a new random card each time mathematically different from shuffling the entire deck first?**  
If each draw uniformly samples the **remaining** cards and assigns orientations independently, the resulting distribution of drawn cards can be the same. However, pre-shuffling and persisting a full deck is a better fit for face-down cards, fixed positions, and safe retries.

**Q3: Will there always be exactly 39 reversed cards?**  
No. The independent 50% orientation model does not enforce a fixed number of reversals.

**Q4: On the second draw, is the probability still $1/156$?**  
For a **particular card known to remain in the deck** with a specified but still unobserved orientation, the probability is $1/(77\times2)=1/154$. For a card that has already been drawn, it is zero. Unconditionally, before seeing the first draw, symmetry means a particular card and orientation still have probability $1/156$ of occupying the second position.

**Q5: Does choosing three cards instead of ten affect fairness?**  
Not the shuffling rule or marginal fairness of each draw position. However, with more cards drawn, the chance that a particular card appears **at least once** naturally increases, and the number of possible combinations changes.

**Q6: Do these formulas tell us how likely a future event is to happen?**  
No. They describe the **randomness of the card-drawing process**, not the predictive accuracy of tarot readings about external events.

---

## 14. Design Decision Summary

| Design aspect | Chosen approach | Rationale |
|---|---|---|
| Deck size | 78 cards | Models a standard physical tarot deck |
| Orientations | Independent, 50% each | Symmetric, transparent, and testable |
| Shuffle | Secure Fisher–Yates | Makes all card permutations equally likely |
| Drawing | Without replacement | Matches the finite physical deck constraint |
| Shuffle frequency | Once per reading session | Preserves hidden assignments |
| Interactive face-down selection | Persistent slot-to-card mapping | Supports user choice without sacrificing fairness |
| Spreads | Data-driven, variable lengths | Not limited to three-card readings |
| AI interpretation | Separate from the drawing engine | Prevents the language model from influencing random outcomes |
| Database | Persists order, orientation, and draw state | Supports refreshes, retries, and auditability |

**In one sentence:** First generate and persist one genuinely 78-card shuffled deck; then let the user reveal cards from it. The AI interprets the revealed result but never determines which cards appear.
