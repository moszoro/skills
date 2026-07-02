---
name: cove
description: Apply Chain-of-Verification to reduce hallucinations. Use when accuracy matters - complex questions, factual claims, research. Invoked as /cove [question].
---

<objective>
Apply Meta AI's Chain-of-Verification (CoVe) technique to answer questions with higher accuracy by separating generation from verification, preventing confirmation bias.

**CRITICAL:** Before running CoVe, ensure 100% clarity on what the user is asking through clarifying questions.
</objective>

<process>
## Step 0: Clarify the Question (MANDATORY)

Before attempting any answer, use AskUserQuestion to ensure complete understanding. Ask until you have FULL clarity.

**What to clarify:**
- Ambiguous terms or scope
- Specific context (domain, timeframe, constraints)
- What "success" looks like for their answer
- Any assumptions you're making

```
Use AskUserQuestion tool with 1-4 targeted questions:
- Question must be specific, not generic
- Options should cover the likely interpretations
- Continue asking until no ambiguity remains
```

**Exit criteria for Step 0:**
- You can restate the question in your own words with full specificity
- User confirms your understanding is correct
- No remaining "it depends" scenarios

Only proceed to Step 1 after achieving 100% clarity.

---

## Step 1: Baseline Response

Answer the question directly. Don't hold back - give your full initial answer.

```
INITIAL ANSWER:
[Your complete answer to the question]
```

## Step 2: Plan Verification Questions

Generate 3-5 verification questions that would expose errors in your answer. These should:
- Challenge specific factual claims
- Check for missing nuances or exceptions
- Verify assumptions you made

```
VERIFICATION QUESTIONS:
1. [Question that tests a specific claim]
2. [Question that checks for exceptions]
3. [Question that verifies an assumption]
...
```

## Step 3: Independent Verification

Answer each verification question **independently** - as if you never saw your initial answer. This prevents confirmation bias.

```
VERIFICATION ANSWERS:
Q1: [Answer based purely on what you know, not defending initial answer]
Q2: [Independent answer]
Q3: [Independent answer]
...
```

## Step 4: Final Verified Response

Compare verification answers against your initial response. Identify discrepancies. Produce corrected final answer.

```
CORRECTIONS NEEDED:
- [What needs to change based on verification]

FINAL VERIFIED ANSWER:
[Revised answer incorporating verification findings]
```
</process>

<example>
**Question:** "What are the health benefits of coffee?"

**Step 1 - Initial Answer:**
Coffee has many health benefits including improved mental alertness, antioxidants, reduced risk of type 2 diabetes, and protection against Parkinson's disease.

**Step 2 - Verification Questions:**
1. What does peer-reviewed research say about coffee and heart health?
2. Are there populations that should avoid coffee?
3. What's the difference between filtered and unfiltered coffee health effects?

**Step 3 - Independent Answers:**
1. Research shows moderate coffee (3-4 cups/day) associated with reduced cardiovascular risk, but high intake may raise blood pressure temporarily.
2. Pregnant women advised to limit caffeine. People with anxiety disorders, certain heart arrhythmias, or acid reflux may need to avoid.
3. Unfiltered coffee (French press, espresso) contains cafestol which raises LDL cholesterol. Paper filters remove this.

**Step 4 - Final Verified Answer:**
Coffee offers health benefits including improved alertness, antioxidants, and reduced risk of type 2 diabetes and Parkinson's. However, benefits depend on preparation method (filtered preferred) and individual factors. Some populations should limit or avoid coffee: pregnant women, those with anxiety disorders, certain cardiac conditions, or acid reflux.
</example>

<when_to_use>
- Complex factual questions
- Claims requiring accuracy
- Research synthesis
- Medical/legal/financial information
- Anything where being wrong matters
</when_to_use>

<success_criteria>
- Step 0: Question fully clarified via AskUserQuestion before proceeding
- All 5 steps completed visibly (0-4)
- Verification questions genuinely challenge the initial answer
- Verification answers are independent (not defending initial answer)
- Final answer incorporates corrections
</success_criteria>
