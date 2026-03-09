# Programming: Recursion — Tutor Reference

## Core Concepts

**Recursion**: A technique where a function calls itself to solve a problem by breaking it into smaller, self-similar subproblems. Every recursive solution must have a base case and a recursive case.

**Base case**: The termination condition that stops the recursion. It represents the simplest version of the problem with a known answer. Without a base case, recursion runs indefinitely until a stack overflow occurs.

**Recursive case**: The part of the function that calls itself with a modified (typically smaller) argument, making progress toward the base case.

**Call stack**: The data structure that tracks active function calls. Each recursive call adds a new frame to the stack containing local variables and the return address. The stack unwinds as each call returns.

**Stack overflow**: Occurs when recursion depth exceeds the system's stack limit, typically due to missing or unreachable base cases.

## Key Patterns and Procedures

- **Factorial**: `fact(n) = n * fact(n-1)`, base case `fact(0) = 1` or `fact(1) = 1`.
- **Fibonacci**: `fib(n) = fib(n-1) + fib(n-2)`, base cases `fib(0) = 0, fib(1) = 1`. Naive implementation is O(2^n); demonstrate memoization as optimization.
- **Binary search**: Divide search space in half each call. Base case: element found or search space empty.
- **Tree traversal**: Process node, recurse on children. Base case: null/empty node.
- **Divide and conquer**: Split problem (merge sort, quicksort), recurse on halves, combine results.

**Template structure**:
```
def recursive_function(input):
    if base_condition(input):    # Base case
        return base_value
    else:                        # Recursive case
        smaller = reduce(input)
        return combine(recursive_function(smaller))
```

## Common Student Misconceptions and Errors

1. **Missing base case**: The most critical error. Students write the recursive case but forget the base case entirely, causing infinite recursion and stack overflow. Example: writing `def fact(n): return n * fact(n-1)` without the `if n == 0` check.

2. **Base case present but unreachable**: The base case exists but the recursive call never reaches it. Example: base case checks `n == 0` but the recursive call passes `n + 1` (incrementing instead of decrementing), so n never reaches 0.

3. **Not returning the recursive call**: Students write `recursive_function(smaller)` instead of `return recursive_function(smaller)`. The function executes correctly internally but returns None to the caller because the return value is discarded.

4. **Off-by-one errors in base case**: Setting the base case boundary incorrectly. Example: `fact(1) = 1` works but `fact(0)` causes infinite recursion because the base case only catches n==1, not n==0. Or using `n < 0` instead of `n <= 0`.

5. **Not reducing the problem**: The recursive call uses the same argument as the current call, causing infinite recursion. Example: `def f(lst): return f(lst)` instead of `f(lst[1:])`.

6. **Confusing iteration and recursion**: Students write a loop inside the recursive function that does all the work, making the recursion redundant. Or they try to maintain external state (global variables) instead of using return values.

7. **Multiple base cases omission**: For problems like Fibonacci that need two base cases (n==0 and n==1), students provide only one, leading to incorrect results or infinite recursion for certain inputs.

8. **Incorrect combination step**: Students compute the recursive result correctly but combine it wrong. Example: `return fact(n-1) + n` instead of `return fact(n-1) * n` for factorial.

9. **Thinking recursion modifies the original data**: Students believe that recursive calls on sublists or substrings modify the original input, rather than understanding that each call operates on a copy or slice.

10. **Inability to trace execution mentally**: Students cannot walk through the call stack. They treat recursion as a "magic box" rather than understanding the step-by-step unfolding and folding of calls.

## Diagnostic Questions

- "What happens when your function is called with the smallest possible input?" (surfaces missing base case)
- "Can you trace through what happens when n=3? Write out each call." (surfaces inability to trace execution)
- "Does your argument get closer to the base case with each call?" (surfaces unreachable base case or non-reducing arguments)
- "What does your function return at each step? Follow the returns back up." (surfaces missing return statement)
- "If I call your function with n=0, what path does it take?" (surfaces off-by-one in base case)
- "Can you explain in words what the recursive call is supposed to give you back?" (surfaces conceptual understanding of the subproblem)
- "How many times will your function call itself before stopping?" (surfaces understanding of termination)

## Worked Example: Common Error and Correct Approach

**Problem**: Write a recursive function to compute the sum of a list of numbers.

**Common incorrect approach**:
```python
def sum_list(lst):
    return lst[0] + sum_list(lst[1:])
```
Error: No base case. When `lst` becomes empty, `lst[0]` raises an IndexError.

**Correct approach**:
```python
def sum_list(lst):
    if len(lst) == 0:        # Base case: empty list
        return 0
    return lst[0] + sum_list(lst[1:])  # Recursive case
```

**Trace for sum_list([3, 1, 2])**:
1. sum_list([3, 1, 2]) -> 3 + sum_list([1, 2])
2. sum_list([1, 2]) -> 1 + sum_list([2])
3. sum_list([2]) -> 2 + sum_list([])
4. sum_list([]) -> 0 (base case)
5. Unwind: 2 + 0 = 2, then 1 + 2 = 3, then 3 + 3 = 6

**Tutoring note**: When a student's recursion crashes or loops, first ask them to identify their base case. If they cannot, have them think about the simplest possible input (empty list, n=0, single element) and what the answer should be for that input. Then work upward from there.
