# Statistics: Descriptive Statistics — Tutor Reference

## Core Concepts

**Population vs Sample**: A population is the entire group of interest. A sample is a subset drawn from the population. This distinction affects which formulas to use. Population parameters are denoted by Greek letters (mu, sigma); sample statistics use Latin letters (x-bar, s).

**Mean (arithmetic average)**: The sum of all values divided by the count. Population mean: mu = (sum of x_i) / N. Sample mean: x-bar = (sum of x_i) / n. The mean is sensitive to outliers.

**Median**: The middle value when data is sorted. For even-count data, it is the average of the two middle values. The median is robust to outliers and skewed distributions.

**Mode**: The most frequently occurring value. A dataset can be unimodal, bimodal, or multimodal. Not always useful for continuous data.

**Variance**: The average of the squared deviations from the mean. Measures spread.
- Population variance: sigma^2 = sum((x_i - mu)^2) / N
- Sample variance: s^2 = sum((x_i - x-bar)^2) / (n - 1)

**Standard deviation**: The square root of variance. Same units as the original data.
- Population: sigma = sqrt(sigma^2)
- Sample: s = sqrt(s^2)

**Bessel's correction**: Using n-1 instead of n in the sample variance denominator. This corrects for the bias introduced by estimating the population mean with the sample mean. The sample mean is closer to the sample data than the true population mean, so dividing by n would systematically underestimate the true variance.

## Key Formulas

- Mean: x-bar = (1/n) * sum(x_i)
- Variance (population): sigma^2 = (1/N) * sum((x_i - mu)^2)
- Variance (sample): s^2 = (1/(n-1)) * sum((x_i - x-bar)^2)
- Standard deviation: sigma = sqrt(variance)
- Range: max - min
- Coefficient of variation: CV = (s / x-bar) * 100%
- Z-score: z = (x - mu) / sigma (how many standard deviations from the mean)

## Common Student Misconceptions and Errors

1. **Using N instead of n-1 for sample variance**: The most frequent error. Students divide by n (the sample size) when computing sample variance instead of n-1. This underestimates the true population variance. They do not understand why Bessel's correction exists.

2. **Confusing sigma and s notation**: Students use population formulas (sigma, N) when working with sample data, or vice versa. They may not recognize when a problem specifies a sample vs a population.

3. **Forgetting to square deviations**: Students compute the average of |x_i - mean| (mean absolute deviation) instead of the average of (x_i - mean)^2 (variance). Or they compute variance correctly but forget to take the square root for standard deviation.

4. **Squaring the standard deviation incorrectly**: When going from standard deviation to variance, students sometimes double instead of square (e.g., if s = 3, they write variance = 6 instead of 9).

5. **Computing mean of already-summarized data**: When given grouped data or frequency tables, students add the values and divide by the number of rows instead of using weighted means.

6. **Confusing mean and median**: Students use the mean when the median would be more appropriate (skewed data, outliers), or they compute one when asked for the other.

7. **Order of operations in variance**: Students compute sum(x_i^2 - mean^2) instead of sum((x_i - mean)^2). They distribute the square incorrectly.

8. **Not sorting data before finding median**: Students pick the middle value from unsorted data.

9. **Z-score direction errors**: Students compute (mu - x) / sigma instead of (x - mu) / sigma, flipping the sign.

10. **Assuming normal distribution**: Students apply the 68-95-99.7 rule without verifying that the data is approximately normally distributed.

## Diagnostic Questions

- "Is this dataset a sample or the entire population? How does that affect your formula?" (surfaces n vs n-1 confusion)
- "What are the units of variance? What are the units of standard deviation?" (surfaces understanding of squaring)
- "Why do we divide by n-1 instead of n for a sample?" (surfaces conceptual understanding of Bessel's correction)
- "Can you walk me through how you computed each deviation from the mean?" (surfaces squaring and arithmetic errors)
- "If I add an outlier value of 1000 to this dataset, which changes more: the mean or the median?" (surfaces mean vs median understanding)
- "What does a z-score of -2 tell you about this data point?" (surfaces z-score interpretation)
- "Did you sort the data before finding the median?" (surfaces procedural error)

## Worked Example: Common Error and Correct Approach

**Problem**: Find the sample standard deviation of the data: {4, 8, 6, 5, 3}.

**Common incorrect approach**:
1. Mean = (4+8+6+5+3)/5 = 26/5 = 5.2
2. Deviations squared: (4-5.2)^2=1.44, (8-5.2)^2=7.84, (6-5.2)^2=0.64, (5-5.2)^2=0.04, (3-5.2)^2=4.84
3. Sum = 14.8
4. Variance = 14.8 / 5 = 2.96 (ERROR: divided by n instead of n-1)
5. StdDev = sqrt(2.96) = 1.72

**Correct approach**:
1. Mean = (4+8+6+5+3)/5 = 26/5 = 5.2
2. Deviations squared: 1.44 + 7.84 + 0.64 + 0.04 + 4.84 = 14.8
3. Sample variance = 14.8 / (5-1) = 14.8 / 4 = 3.7
4. Sample standard deviation = sqrt(3.7) = 1.924

**Tutoring note**: When a student divides by n for a sample, ask "Is this the entire population or a sample?" Then ask why the distinction matters. Guide them to understand that the sample mean is already optimized for the sample data, so dividing by n-1 compensates for the resulting underestimate of spread.
