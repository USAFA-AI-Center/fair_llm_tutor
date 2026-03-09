# Calculus: Derivatives — Tutor Reference

## Core Concepts

**Derivative**: The instantaneous rate of change of a function at a point. Geometrically, it is the slope of the tangent line to the curve at that point. Notation: f'(x), dy/dx, Df(x).

**Differentiability**: A function is differentiable at a point if the limit definition of the derivative exists there. Differentiability implies continuity, but continuity does not imply differentiability (e.g., |x| at x=0).

**Limit definition**: f'(x) = lim(h->0) [f(x+h) - f(x)] / h. Students should understand this conceptually even when using shortcut rules.

## Key Rules and Formulas

- **Constant rule**: d/dx [c] = 0
- **Power rule**: d/dx [x^n] = n * x^(n-1). Works for all real n, including negatives and fractions.
- **Constant multiple rule**: d/dx [c * f(x)] = c * f'(x)
- **Sum/difference rule**: d/dx [f(x) +/- g(x)] = f'(x) +/- g'(x)
- **Product rule**: d/dx [f(x) * g(x)] = f'(x)*g(x) + f(x)*g'(x)
- **Quotient rule**: d/dx [f(x)/g(x)] = [f'(x)*g(x) - f(x)*g'(x)] / [g(x)]^2
- **Chain rule**: d/dx [f(g(x))] = f'(g(x)) * g'(x). The "outside-inside" rule.
- **Common derivatives**: d/dx [sin x] = cos x, d/dx [cos x] = -sin x, d/dx [e^x] = e^x, d/dx [ln x] = 1/x

## Common Student Misconceptions and Errors

1. **Forgetting the chain rule**: The single most common derivative error. Students differentiate the outer function but forget to multiply by the derivative of the inner function. Example: d/dx [sin(3x)] = cos(3x) instead of the correct 3*cos(3x). This error is especially frequent with nested functions like e^(x^2) or (2x+1)^5.

2. **Power rule sign/arithmetic errors**: When applying d/dx [x^n] = n*x^(n-1), students miscalculate n-1, especially with negative or fractional exponents. Example: d/dx [x^(-2)] written as -2x^(-1) instead of -2x^(-3).

3. **Treating variables as constants**: Students sometimes treat a variable term as if it were a constant and differentiate it to zero, especially in multivariable contexts or when the variable has an unfamiliar name.

4. **Product rule omission**: Students multiply derivatives instead of using the product rule. Example: d/dx [x * sin(x)] = 1 * cos(x) = cos(x), instead of the correct sin(x) + x*cos(x).

5. **Sign errors with trig derivatives**: Confusing d/dx [sin x] = cos x with d/dx [cos x] = -sin x. The negative sign on the cosine derivative is frequently dropped.

6. **Incorrect quotient rule order**: Swapping the numerator terms in the quotient rule, computing f*g' - f'*g instead of f'*g - f*g'. This is a subtle but frequent algebraic error.

7. **Derivative of a constant times a function**: Students sometimes differentiate the constant. Example: d/dx [5x^3] = 0 * 3x^2 = 0 (treating 5 as a separate function in a product rule when the constant multiple rule suffices).

8. **Confusing the derivative with the function value**: When asked "what is f'(2)?", students sometimes compute f(2) instead of first finding f'(x) and then evaluating at x=2.

9. **Misapplying power rule to exponentials**: Writing d/dx [2^x] = x * 2^(x-1) by treating 2^x like x^2. The correct derivative is 2^x * ln(2).

## Diagnostic Questions

- "Can you identify the outer and inner functions in this composition?" (surfaces chain rule confusion)
- "What rule applies when two functions are multiplied together?" (surfaces product rule omission)
- "What happens to the exponent when you apply the power rule?" (surfaces arithmetic errors)
- "Is the base or the exponent the variable here?" (surfaces exponential vs power confusion)
- "Before computing, can you tell me which differentiation rule you plan to use and why?" (surfaces procedural understanding)
- "What is the derivative of the inside function by itself?" (isolates chain rule step)

## Worked Example: Common Error and Correct Approach

**Problem**: Find d/dx [(3x + 1)^4]

**Common incorrect approach**:
Student writes: 4(3x + 1)^3.
Error: Forgot the chain rule. The student differentiated the outer function (power rule) but did not multiply by the derivative of the inner function (3x + 1).

**Correct approach**:
1. Identify structure: This is a composition f(g(x)) where f(u) = u^4 and g(x) = 3x + 1.
2. Differentiate outer function: f'(u) = 4u^3, so f'(g(x)) = 4(3x + 1)^3.
3. Differentiate inner function: g'(x) = 3.
4. Apply chain rule: d/dx [(3x + 1)^4] = 4(3x + 1)^3 * 3 = 12(3x + 1)^3.

**Tutoring note**: When a student omits the chain rule, ask them to explicitly name the "inside" function and compute its derivative separately before combining. This decompositional approach builds the habit of checking for chain rule applicability.
