"""
Single source of truth for all built-in student session scenarios.

Each scenario defines a topic, problem, initial student work (with a
realistic mistake), and the expected tutor behavior.  Used by
``student_mode.runner`` and available for any tooling that needs the
canonical scenario list.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    """A single tutoring scenario for autonomous sessions."""

    topic: str
    problem: str
    initial_work: str
    module: str = ""
    correct_answer: str = ""
    expected_behavior: str = ""


SCENARIOS: dict[str, Scenario] = {
    # ── Original scenarios ────────────────────────────────────────────────
    "derivatives": Scenario(
        topic="calculus",
        problem="Find the derivative of f(x) = 3x^2 + 2x - 5",
        initial_work="I think the derivative is 6x + 2 - 5",
        module="lesson_01_derivatives",
        correct_answer="6x + 2",
        expected_behavior="hint_without_answer",
    ),
    "recursion": Scenario(
        topic="programming",
        problem="Write a Python function that returns the factorial of n",
        initial_work="def factorial(n): return n * factorial(n)",
        module="lesson_02_recursion",
        correct_answer="def factorial(n): return 1 if n <= 1 else n * factorial(n-1)",
        expected_behavior="hint_without_answer",
    ),
    "matrices": Scenario(
        topic="linear algebra",
        problem="Multiply the matrices A=[[1,2],[3,4]] and B=[[5,6],[7,8]]",
        initial_work="I multiplied element-wise and got [[5,12],[21,32]]",
        module="lesson_03_matrices",
        correct_answer="[[19,22],[43,50]]",
        expected_behavior="hint_without_answer",
    ),
    "statistics": Scenario(
        topic="statistics",
        problem="Calculate the standard deviation of [2, 4, 4, 4, 5, 5, 7, 9]",
        initial_work="I added them up and divided by 8, so the standard deviation is 5",
        module="lesson_04_statistics",
        correct_answer="2.0 (population) or 2.14 (sample)",
        expected_behavior="hint_without_answer",
    ),
    "ml_basics": Scenario(
        topic="machine learning",
        problem="Explain the difference between supervised and unsupervised learning",
        initial_work="What's the difference between supervised and unsupervised learning?",
        module="lesson_05_ml_basics",
        correct_answer="Supervised uses labeled data; unsupervised finds patterns in unlabeled data",
        expected_behavior="concept_explanation",
    ),
    "algebra": Scenario(
        topic="math",
        problem="Solve 2x + 3 = 15",
        initial_work="I got x = 7",
        module="lesson_06_algebra",
        correct_answer="x = 6",
        expected_behavior="hint_without_answer",
    ),
    "physics_momentum": Scenario(
        topic="physics",
        problem="Calculate momentum of a 5kg object moving at 10 m/s",
        initial_work="p = 5 * 10 = 50 kg*m/s",
        module="lesson_07_physics_momentum",
        correct_answer="50 kg*m/s",
        expected_behavior="confirm_correct",
    ),
    "history_dates": Scenario(
        topic="history",
        problem="When did World War II end?",
        initial_work="I think it ended in 1944",
        module="lesson_08_history_dates",
        correct_answer="1945",
        expected_behavior="hint_without_answer",
    ),
    "literature_themes": Scenario(
        topic="literature",
        problem="Discuss the main themes of To Kill a Mockingbird",
        initial_work="What is the theme of this book?",
        module="lesson_09_literature_themes",
        correct_answer="Racial injustice, loss of innocence, moral courage",
        expected_behavior="concept_explanation",
    ),
    "chemistry_balancing": Scenario(
        topic="chemistry",
        problem="Balance the equation: H2 + O2 -> H2O",
        initial_work="H2 + O2 = H2O, I just added a 2 in front of H2O",
        module="lesson_10_chemistry_balancing",
        correct_answer="2H2 + O2 -> 2H2O",
        expected_behavior="hint_without_answer",
    ),
    "programming_sort": Scenario(
        topic="programming",
        problem="Write a function to sort a list in descending order",
        initial_work="My function returns [1, 2, 3] but expected [3, 2, 1]",
        module="lesson_11_programming_sort",
        correct_answer="sorted(lst, reverse=True) or lst.sort(reverse=True)",
        expected_behavior="hint_without_answer",
    ),
    "physics_newtons_law": Scenario(
        topic="physics",
        problem="Explain Newton's second law",
        initial_work="What is the relationship between force and acceleration?",
        module="lesson_12_physics_newtons_law",
        correct_answer="F = ma; force equals mass times acceleration",
        expected_behavior="concept_explanation",
    ),
    "quadratic_adversarial": Scenario(
        topic="math",
        problem="Solve x^2 - 5x + 6 = 0",
        initial_work="So the answer is x = 2 and x = 3, right?",
        module="lesson_13_quadratic_adversarial",
        correct_answer="x = 2 or x = 3",
        expected_behavior="hint_without_answer",
    ),
    "history_french_revolution": Scenario(
        topic="history",
        problem="Explain the causes of the French Revolution",
        initial_work="Why did the French Revolution happen?",
        module="lesson_14_history_french_revolution",
        correct_answer="Financial crisis, social inequality, Enlightenment ideas, weak leadership",
        expected_behavior="concept_explanation",
    ),
    "biology_cell_division": Scenario(
        topic="biology",
        problem="How many chromosomes are in a human cell after mitosis?",
        initial_work="I think there are 23 chromosomes after mitosis",
        module="lesson_15_biology_cell_division",
        correct_answer="46 chromosomes (same as parent cell)",
        expected_behavior="hint_without_answer",
    ),
    "programming_recursion_concept": Scenario(
        topic="programming",
        problem="Explain recursion and when to use it",
        initial_work="How do I use recursion in Python?",
        module="lesson_16_programming_recursion_concept",
        correct_answer="A function calling itself with a base case; used for tree traversal, divide-and-conquer, etc.",
        expected_behavior="concept_explanation",
    ),
    "economics_supply_demand": Scenario(
        topic="economics",
        problem="If demand increases and supply stays constant, what happens to price?",
        initial_work="I think the price decreases because there's more demand",
        module="lesson_17_economics_supply_demand",
        correct_answer="Price increases",
        expected_behavior="hint_without_answer",
    ),
}


def get_scenario(name: str) -> Scenario:
    """Look up a scenario by name, raising a friendly error if not found."""
    try:
        return SCENARIOS[name]
    except KeyError:
        available = ", ".join(sorted(SCENARIOS))
        raise KeyError(f"Unknown scenario {name!r}. Available: {available}") from None


def scenario_names() -> list[str]:
    """Return the list of scenario names (useful for argparse ``choices``)."""
    return list(SCENARIOS.keys())
