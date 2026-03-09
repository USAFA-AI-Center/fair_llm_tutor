# Common Misconceptions: Cross-Domain Error Patterns — Tutor Reference

## Purpose

This document catalogs the most frequent student error patterns across all domains, organized by error type. These patterns repeat across subjects and recognizing the underlying error type helps the tutor diagnose issues faster, even in unfamiliar domains. When a student makes an error, first identify which category it falls into, then use domain-specific knowledge to address the specific instance.

## 1. Arithmetic and Computational Errors

These are mechanical mistakes in executing calculations. The student may understand the concept but makes errors in the computation.

**Sign errors**: Dropping or flipping a negative sign during calculation. Extremely common across all quantitative domains.
- Calculus: Forgetting the negative in d/dx[cos x] = -sin x.
- Algebra: Distributing -(x - 3) as -x - 3 instead of -x + 3.
- Physics: Treating velocity as positive when an object moves in the negative direction.
- Statistics: Computing (mu - x) instead of (x - mu) in z-scores.

**Off-by-one errors**: Being one unit off in counting, indexing, or boundary conditions.
- Programming: Array index starting at 0 vs 1; loop running one too many or one too few times.
- Statistics: Using n instead of n-1 in sample variance (Bessel's correction).
- Biology: Miscounting chromosome numbers after one round of division.
- Recursion: Base case set at the wrong boundary (n==1 instead of n==0).

**Order of operations errors**: Applying operations in the wrong sequence.
- Algebra: Computing 2 + 3 * 4 as 20 instead of 14.
- Statistics: Computing sum(x^2 - mean^2) instead of sum((x - mean)^2).
- Calculus: Applying the chain rule steps out of order.

**Unit conversion failures**: Not converting units before combining quantities.
- Physics: Mixing grams and kilograms, or centimeters and meters, in a momentum calculation.
- Chemistry: Mixing moles and grams without molar mass conversion.

**Rounding and precision errors**: Rounding intermediate results too early, causing accumulated error in the final answer.

## 2. Conceptual Confusion Errors

The student has an incorrect or incomplete mental model of the concept.

**Confusing similar concepts**: Mixing up two related but distinct ideas.
- Biology: Mitosis vs meiosis, sister chromatids vs homologous chromosomes.
- Statistics: Population vs sample parameters (sigma vs s, N vs n-1).
- Physics: Mass vs weight, momentum vs kinetic energy.
- Economics: Demand vs quantity demanded, movement along vs shift of curve.
- Literature: Theme vs plot, tone vs mood.
- Chemistry: Coefficients vs subscripts.

**False equivalence / oversimplification**: Assuming two things are the same when they are not.
- History: Correlation = causation; single-cause explanations for complex events.
- ML: Accuracy = model quality (ignoring class imbalance).
- Physics: Force = velocity (thinking objects need force to maintain motion).
- Literature: Narrator = author; symbol = one fixed meaning.

**Misapplied analogy**: Extending a rule beyond its valid domain.
- Calculus: Applying the power rule to exponentials (d/dx[2^x] = x*2^(x-1)).
- Linear algebra: Assuming matrix multiplication is commutative (like scalar multiplication).
- Statistics: Applying the 68-95-99.7 rule to non-normal distributions.
- Economics: Assuming all goods are normal goods.

**Incomplete mental model**: Understanding part of a concept but missing a critical component.
- Recursion: Understanding the recursive case but not the base case.
- Meiosis: Understanding chromosome separation but not the difference between meiosis I and II.
- Calculus: Understanding the power rule but not recognizing when the chain rule also applies.

## 3. Procedural Errors

The student knows what to do conceptually but executes the steps incorrectly or in the wrong order.

**Skipped steps**: Omitting a required step in a multi-step procedure.
- Calculus: Applying the chain rule's outer derivative but forgetting to multiply by the inner derivative.
- Chemistry: Balancing some elements but not checking all of them.
- Statistics: Forgetting to sort data before finding the median.
- Algebra: Finding one root of a quadratic but not the other (omitting +/-).

**Wrong step order**: Performing correct steps in the wrong sequence.
- ML: Normalizing data before splitting into train/test (data leakage).
- Chemistry: Trying to balance oxygen first instead of starting with less common elements.
- Biology: Describing meiosis II before meiosis I.

**Wrong formula selection**: Choosing the wrong formula for the situation.
- Statistics: Using population variance formula for sample data.
- Physics: Using KE = 1/2 mv^2 when momentum p = mv is needed.
- Algebra: Using the quadratic formula when the equation is linear.

**Failure to check work**: Not verifying the answer against the original problem.
- Algebra: Not substituting solutions back into the original equation to catch extraneous roots.
- Chemistry: Not verifying atom counts on both sides after balancing.
- Programming: Not tracing through code with sample inputs.

## 4. Reading Comprehension and Problem Interpretation Errors

The student misreads or misinterprets what the problem is asking.

**Answering a different question**: Solving for the wrong quantity.
- Calculus: Computing f(2) when asked for f'(2).
- Physics: Computing speed when asked for velocity (missing direction).
- Statistics: Computing mean when asked for median.

**Misidentifying given information**: Extracting wrong values from the problem statement.
- Algebra: Misidentifying a, b, c in the quadratic formula, especially signs.
- Physics: Confusing which mass goes with which velocity in collision problems.
- Economics: Misidentifying which good's market to analyze.

**Ignoring constraints or conditions**: Overlooking conditions stated in the problem.
- Algebra: Ignoring "x > 0" constraint and including negative solutions.
- Programming: Ignoring edge cases specified in the problem (empty input, zero, negative numbers).
- Economics: Ignoring "ceteris paribus" and changing multiple variables.

**Misinterpreting notation**: Not understanding mathematical or domain-specific notation.
- Statistics: Confusing sigma (population) with s (sample).
- Calculus: Confusing dy/dx (derivative) with delta-y/delta-x (average rate of change).
- Linear algebra: Confusing A^T (transpose) with A^(-1) (inverse).

## 5. Metacognitive Errors

Errors in the student's awareness of their own understanding.

**False confidence**: The student believes they understand but their mental model is wrong. They do not ask questions because they think they already know.
- Diagnostic: Ask them to explain the concept in their own words or teach it to someone else. Gaps surface quickly.

**Learned helplessness**: The student believes they cannot understand and gives up before engaging.
- Diagnostic: Start with something they can succeed at and build incrementally.

**Pattern matching without understanding**: The student recognizes surface patterns and applies memorized procedures without understanding why.
- Diagnostic: Change the problem slightly (different numbers, different variable names, reversed order) and see if they can still solve it. If not, they were pattern matching.

## Tutor Strategy Summary

When diagnosing an error:
1. **Classify the error type** using the categories above.
2. **Identify the specific instance** using domain knowledge from the relevant course material file.
3. **Choose a diagnostic question** that surfaces the root cause without revealing the answer.
4. **Guide correction** by asking the student to re-examine the specific step where the error occurred.
5. **Verify understanding** by posing a similar but slightly different problem.

The goal is never to tell the student the answer, but to help them discover where their reasoning went wrong and correct it themselves.
