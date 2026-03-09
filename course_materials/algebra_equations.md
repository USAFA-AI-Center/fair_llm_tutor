# Algebra: Equations — Tutor Reference

## Core Concepts

**Linear equation**: An equation of the form ax + b = 0, where a and b are constants. The graph is a straight line. Solution: x = -b/a. In two variables: ax + by = c represents a line in the coordinate plane.

**System of linear equations**: Two or more linear equations with the same variables. Solutions can be found by substitution, elimination, or matrix methods. A system can have one solution (intersecting lines), no solution (parallel lines), or infinitely many solutions (same line).

**Quadratic equation**: An equation of the form ax^2 + bx + c = 0, where a is not zero. The graph is a parabola. Can have two real solutions, one repeated real solution, or two complex solutions.

**Factoring**: Rewriting a polynomial as a product of simpler polynomials. Example: x^2 + 5x + 6 = (x + 2)(x + 3). Factoring sets each factor to zero to find solutions.

**Quadratic formula**: x = (-b +/- sqrt(b^2 - 4ac)) / (2a). Works for all quadratic equations. Derived from completing the square.

**Discriminant**: D = b^2 - 4ac. Determines the nature of roots: D > 0 gives two distinct real roots; D = 0 gives one repeated real root; D < 0 gives two complex conjugate roots.

**Completing the square**: Rewriting ax^2 + bx + c in the form a(x - h)^2 + k. Useful for deriving the quadratic formula and finding the vertex of a parabola.

## Key Procedures

- **Solving linear equations**: Isolate the variable by performing the same operation on both sides. Maintain balance.
- **Factoring trinomials**: Find two numbers that multiply to give ac and add to give b (for ax^2 + bx + c).
- **FOIL**: Multiply two binomials: (a+b)(c+d) = ac + ad + bc + bd.
- **Zero product property**: If AB = 0, then A = 0 or B = 0. Foundation of solving by factoring.
- **Checking solutions**: Always substitute answers back into the original equation to verify.

## Common Student Misconceptions and Errors

1. **Forgetting the +/- in the quadratic formula**: Students compute only one root, using just the + (or just the -) in front of the square root. A quadratic can have two roots, and both must be found.

2. **Sign errors when distributing negatives**: The most pervasive algebra error. Students write -(x - 3) = -x - 3 instead of -x + 3. Distributing a negative sign across parentheses requires flipping every sign inside.

3. **Incorrect distribution (FOIL errors)**: Students omit the inner or outer terms when multiplying binomials. Example: (x + 2)(x + 3) = x^2 + 6 (missing the middle term 5x). They multiply only the first and last terms.

4. **Moving terms across the equals sign without changing sign**: Students move a term from one side to the other but forget to negate it. Example: x + 5 = 12 becomes x = 12 + 5 = 17 instead of x = 12 - 5 = 7.

5. **Dividing by a variable that might be zero**: Students divide both sides by x without considering that x might equal zero, losing a valid solution. Example: x^2 = 5x, dividing both sides by x gives x = 5, but x = 0 is also a solution.

6. **Squaring both sides and introducing extraneous solutions**: When solving equations with square roots, squaring can introduce solutions that do not satisfy the original equation. Students fail to check their answers.

7. **Applying the quadratic formula with wrong signs**: Students misidentify a, b, or c, especially when terms are not in standard order or when b or c is negative. Example: for 2x^2 - 3x + 1 = 0, using b = 3 instead of b = -3.

8. **Factoring errors**: Students factor incorrectly by choosing numbers that do not multiply to the correct product. Example: x^2 + 7x + 10 = (x + 2)(x + 6), which gives a product of 12 instead of 10.

9. **Confusing "no real solution" with "no solution"**: When the discriminant is negative, students say the equation has no solution. It has no real solution, but it does have complex solutions. The distinction matters.

10. **Illegal operations**: Students add/subtract terms to only one side of the equation, breaking the equality. Or they "cancel" terms that are added (not multiplied), such as canceling the x in (x + 3)/x.

## Diagnostic Questions

- "Can you identify a, b, and c in your equation? What are their signs?" (surfaces sign identification errors)
- "When you distributed that negative, what happened to each term inside the parentheses?" (surfaces distribution errors)
- "How many solutions should a quadratic equation have?" (surfaces +/- omission)
- "Can you check your answer by plugging it back into the original equation?" (catches all errors via verification)
- "What operation did you perform, and did you do it to both sides?" (surfaces one-sided operations)
- "Before you divided both sides by x, is it possible that x equals zero?" (surfaces dividing-by-variable error)
- "What does the discriminant tell you about this equation?" (surfaces understanding of solution types)

## Worked Example: Common Error and Correct Approach

**Problem**: Solve x^2 - 5x + 6 = 0 using the quadratic formula.

**Common incorrect approach**:
Student identifies a=1, b=5 (wrong sign), c=6.
x = (-5 +/- sqrt(25 - 24)) / 2 = (-5 +/- 1) / 2.
x = -2 or x = -3.
Error: Used b=5 instead of b=-5, producing negative roots instead of positive ones.

**Correct approach**:
1. Identify coefficients: a = 1, b = -5, c = 6.
2. Discriminant: (-5)^2 - 4(1)(6) = 25 - 24 = 1 > 0, so two distinct real roots.
3. x = (-(-5) +/- sqrt(1)) / (2*1) = (5 +/- 1) / 2.
4. x = (5+1)/2 = 3, or x = (5-1)/2 = 2.
5. Check: 3^2 - 5(3) + 6 = 9 - 15 + 6 = 0. Correct. 2^2 - 5(2) + 6 = 4 - 10 + 6 = 0. Correct.

**Tutoring note**: Before students apply the formula, have them explicitly write out "a = ..., b = ..., c = ..." including the sign. The most common quadratic formula error is a sign error in identifying b. Also verify by factoring when possible: x^2 - 5x + 6 = (x - 2)(x - 3), confirming x = 2 and x = 3.
