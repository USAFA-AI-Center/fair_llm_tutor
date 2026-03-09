# Linear Algebra: Matrices — Tutor Reference

## Core Concepts

**Matrix**: A rectangular array of numbers organized in rows and columns. An m x n matrix has m rows and n columns. The entry in row i, column j is denoted a_ij.

**Vector**: A matrix with a single column (column vector, n x 1) or single row (row vector, 1 x n). Vectors are the building blocks of linear algebra.

**Dot product**: For two vectors of equal length, the sum of element-wise products: a . b = a1*b1 + a2*b2 + ... + an*bn. Returns a scalar. Requires vectors of the same dimension.

**Matrix multiplication**: For matrices A (m x n) and B (n x p), the product C = AB is an m x p matrix where c_ij = dot product of row i of A with column j of B. The inner dimensions must match.

**Transpose**: A^T flips rows and columns. If A is m x n, then A^T is n x m. Entry (i,j) of A becomes entry (j,i) of A^T.

**Identity matrix**: Square matrix with 1s on the diagonal and 0s elsewhere. AI = IA = A for any compatible matrix A.

**Determinant**: A scalar value computed from a square matrix. det(A) = 0 means the matrix is singular (non-invertible). For 2x2: det([[a,b],[c,d]]) = ad - bc.

**Inverse**: A^(-1) exists only for square matrices with non-zero determinant. AA^(-1) = A^(-1)A = I.

## Key Rules and Formulas

- **Dimension compatibility**: A(m x n) * B(n x p) = C(m x p). The number of columns in A must equal the number of rows in B.
- **Matrix multiplication is NOT commutative**: AB != BA in general. Order matters.
- **Matrix multiplication IS associative**: (AB)C = A(BC).
- **Distributive**: A(B + C) = AB + AC.
- **Transpose of product**: (AB)^T = B^T * A^T (note the reversal of order).
- **Inverse of product**: (AB)^(-1) = B^(-1) * A^(-1) (note the reversal).
- **Scalar multiplication**: k*A multiplies every entry by k.
- **Matrix addition**: Only defined for matrices of the same dimensions. Add element-wise.

## Common Student Misconceptions and Errors

1. **Dimension mismatch in multiplication**: Students attempt to multiply matrices where the inner dimensions do not match. Example: trying to multiply a 3x2 matrix by a 4x3 matrix. They may not check dimensions before computing.

2. **Element-wise multiplication instead of matrix multiplication**: Students multiply corresponding entries (Hadamard product) instead of using row-by-column dot products. This is the most common computational error. Example: for 2x2 matrices, computing [[a1*b1, a2*b2],[a3*b3, a4*b4]] instead of the correct matrix product.

3. **Wrong result dimensions**: Students get the output dimensions wrong. If A is 2x3 and B is 3x4, students may think the result is 3x3 instead of 2x4.

4. **Assuming commutativity**: Students assume AB = BA. This is almost never true for matrices, and attempting to swap order leads to wrong answers or dimension errors.

5. **Dot product dimension errors**: Computing a dot product of vectors with different lengths, or summing incorrectly when performing row-column products.

6. **Confusing rows and columns**: Students mix up which index is which. They may read a 2x3 matrix as "2 columns and 3 rows" instead of "2 rows and 3 columns."

7. **Addition of incompatible matrices**: Attempting to add matrices of different dimensions, which is undefined.

8. **Determinant errors for larger matrices**: Students can compute 2x2 determinants but make sign errors in cofactor expansion for 3x3 matrices, especially forgetting the alternating sign pattern (+, -, +, ...).

9. **Inverse confusion**: Students think every matrix has an inverse, not recognizing that singular matrices (det = 0) are non-invertible. Or they attempt to invert non-square matrices.

10. **Transpose errors in formulas**: Forgetting to reverse order when transposing or inverting products: (AB)^T = B^T A^T, not A^T B^T.

## Diagnostic Questions

- "What are the dimensions of matrix A and matrix B? Can you multiply them in this order?" (surfaces dimension awareness)
- "How do you compute the entry in row 1, column 2 of the product?" (surfaces element-wise vs matrix multiply confusion)
- "What will the dimensions of the result be?" (surfaces output dimension errors)
- "If I swap the order and compute BA instead of AB, do I get the same result?" (surfaces commutativity assumption)
- "Can you show me the dot product of row 1 of A with column 1 of B?" (isolates the fundamental operation)
- "How many rows and how many columns does this matrix have?" (surfaces row/column confusion)
- "What does it mean for a matrix to be singular?" (surfaces inverse understanding)

## Worked Example: Common Error and Correct Approach

**Problem**: Multiply A = [[1, 2], [3, 4]] by B = [[5, 6], [7, 8]].

**Common incorrect approach (element-wise)**:
Student writes: [[1*5, 2*6], [3*7, 4*8]] = [[5, 12], [21, 32]].
Error: Performed element-wise (Hadamard) multiplication instead of matrix multiplication.

**Correct approach**:
1. Verify dimensions: A is 2x2, B is 2x2. Inner dimensions match (2=2). Result will be 2x2.
2. c_11 = row 1 of A . col 1 of B = 1*5 + 2*7 = 5 + 14 = 19
3. c_12 = row 1 of A . col 2 of B = 1*6 + 2*8 = 6 + 16 = 22
4. c_21 = row 2 of A . col 1 of B = 3*5 + 4*7 = 15 + 28 = 43
5. c_22 = row 2 of A . col 2 of B = 3*6 + 4*8 = 18 + 32 = 50
6. Result: AB = [[19, 22], [43, 50]]

**Tutoring note**: When students perform element-wise multiplication, ask them to describe in words how matrix multiplication works before computing. Have them circle one row from A and one column from B and compute that single dot product first. Building the result one entry at a time prevents the element-wise shortcut.
