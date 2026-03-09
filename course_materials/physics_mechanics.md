# Physics: Mechanics — Tutor Reference

## Core Concepts

**Newton's First Law (Inertia)**: An object at rest stays at rest, and an object in motion stays in motion at constant velocity, unless acted upon by a net external force. Inertia is the tendency of an object to resist changes in its state of motion. Mass is the measure of inertia.

**Newton's Second Law**: F_net = ma. The net force on an object equals its mass times its acceleration. This is a vector equation: direction matters. Unit: 1 Newton = 1 kg * m/s^2.

**Newton's Third Law**: For every action, there is an equal and opposite reaction. If object A exerts a force on object B, then B exerts an equal-magnitude, opposite-direction force on A. These forces act on different objects.

**Momentum**: p = mv. A vector quantity. Units: kg*m/s. Momentum has both magnitude and direction.

**Impulse**: J = F * delta_t = delta_p. The change in momentum equals the net force times the time interval over which it acts.

**Conservation of Momentum**: In a closed system (no external forces), total momentum before an interaction equals total momentum after. m1*v1_initial + m2*v2_initial = m1*v1_final + m2*v2_final.

**Elastic collision**: Both momentum and kinetic energy are conserved. Objects bounce off each other.

**Inelastic collision**: Momentum is conserved but kinetic energy is not. Perfectly inelastic: objects stick together, m1*v1 + m2*v2 = (m1+m2)*v_final.

**Weight vs Mass**: Mass is the amount of matter (kg). Weight is the gravitational force on an object: W = mg (Newtons). Mass is constant everywhere; weight depends on the local gravitational field.

**Free body diagram**: A diagram showing all forces acting on a single object. Essential for applying Newton's second law. Forces include gravity, normal force, friction, tension, applied forces.

## Key Formulas

- F = ma (Newton's Second Law)
- p = mv (momentum)
- J = F * delta_t = delta_p (impulse-momentum theorem)
- W = mg (weight, g = 9.8 m/s^2 on Earth)
- Conservation: p_total_before = p_total_after
- Kinetic energy: KE = (1/2)mv^2
- Friction: f = mu * N (friction force = coefficient of friction * normal force)

## Common Student Misconceptions and Errors

1. **Confusing mass and weight**: The most fundamental mechanics misconception. Students use mass (kg) where weight (N) is needed, or vice versa. They say "I weigh 70 kilograms" when they mean their mass is 70 kg and their weight is approximately 686 N.

2. **Forgetting that momentum is a vector**: Students add momentum magnitudes without considering direction. In a collision where objects move in opposite directions, one momentum should be negative. Example: m1*v1 + m2*(-v2), not m1*v1 + m2*v2.

3. **Wrong units**: Students mix units (grams with m/s, or kg with cm/s) without converting. Momentum requires kg*m/s, force requires kg*m/s^2 (Newtons).

4. **Thinking force is needed for constant velocity**: Students believe an object in motion must have a force acting on it to keep moving. Newton's First Law says the opposite: constant velocity requires zero net force.

5. **Third law pair confusion**: Students apply action-reaction forces to the same object instead of recognizing they act on different objects. Example: the normal force on a book from a table is NOT the reaction to the book's weight. (The reaction to the book's weight is the book's gravitational pull on the Earth.)

6. **Adding forces as scalars**: Students add force magnitudes without considering their directions as vectors. Forces in opposite directions should partially cancel, not add.

7. **Confusing momentum and kinetic energy**: Students think conservation of momentum implies conservation of kinetic energy. Momentum is always conserved in a closed system; kinetic energy is only conserved in elastic collisions.

8. **Sign errors in collision problems**: Students forget to assign negative velocity to objects moving in the opposite direction, leading to incorrect total momentum.

9. **Using the wrong system**: Students include external forces in a "conservation of momentum" analysis, or they define the system boundary incorrectly (e.g., including the floor in the system).

10. **Proportional reasoning errors**: Students think doubling velocity doubles kinetic energy (it quadruples it, since KE = 1/2 mv^2). They confuse linear and quadratic relationships.

## Diagnostic Questions

- "What is the difference between the mass and weight of this object?" (surfaces mass/weight confusion)
- "In which direction is each object moving? How does that affect the sign of its momentum?" (surfaces vector/sign errors)
- "What units should your answer be in? Are all your given values in compatible units?" (surfaces unit errors)
- "Draw a free body diagram. What forces act on this object?" (surfaces force analysis)
- "If no net force acts on a moving object, what happens to its motion?" (surfaces Newton's First Law misconception)
- "In Newton's Third Law, which objects do the two forces act on?" (surfaces same-object confusion)
- "Is kinetic energy conserved in this collision? How do you know?" (surfaces momentum vs energy confusion)
- "If I double the velocity, what happens to the momentum? What happens to the kinetic energy?" (surfaces proportional reasoning)

## Worked Example: Common Error and Correct Approach

**Problem**: A 5 kg ball moving at 10 m/s to the right collides with a 3 kg ball moving at 4 m/s to the left. They stick together. Find the final velocity.

**Common incorrect approach**:
Student writes: 5(10) + 3(4) = 8 * v_final.
50 + 12 = 8v, so v = 62/8 = 7.75 m/s.
Error: Did not account for direction. The 3 kg ball moves to the LEFT, so its velocity should be negative.

**Correct approach**:
1. Define positive direction: rightward is positive.
2. Ball 1: m1 = 5 kg, v1 = +10 m/s (right). Ball 2: m2 = 3 kg, v2 = -4 m/s (left).
3. Conservation of momentum: m1*v1 + m2*v2 = (m1+m2)*v_final.
4. 5(10) + 3(-4) = (5+3)*v_final.
5. 50 - 12 = 8*v_final.
6. 38 = 8*v_final, so v_final = 4.75 m/s (positive = rightward).

**Tutoring note**: Before any calculation, ask the student to establish a sign convention and assign signs to each velocity. Drawing arrows showing direction makes this concrete. The most common collision error is treating all velocities as positive regardless of direction.
