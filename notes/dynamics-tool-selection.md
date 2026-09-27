# Dynamics Tool Selection

## Why this matters

Many dynamics problems can be solved in several ways. The fastest FE method is usually the one whose central quantity matches the information given and the quantity requested.

## The four main tools

| Tool | Main relationship | Best signal | Typical question |
|---|---|---|---|
| Kinematics | Motion variables ↔ motion variables | Time, displacement, velocity, acceleration | Find position, velocity, or acceleration |
| Newton's second law | Forces ↔ acceleration | Forces and acceleration are central | Find acceleration, force, or tension |
| Work-energy | Work ↔ kinetic energy | Distance/displacement is given | Find speed after moving a distance |
| Impulse-momentum | Impulse ↔ momentum change | A time interval or impact is central | Find velocity change |

Symbols:

- $\mathbf F$ = force
- $m$ = mass
- $\mathbf a$ = acceleration
- $U$ = work
- $T = \frac{1}{2}mv^2$ = translational kinetic energy
- $\mathbf p = m\mathbf v$ = linear momentum
- $\int F\,dt$ = impulse

## Visual memory aid

```text
force × distance  → work/energy   → speed
force × time      → impulse       → velocity change
force             → F = ma        → acceleration
motion variables  → kinematics    → position/velocity
```

## Important distinction: forces do not usually balance in dynamics

In statics/equilibrium:

$$
\sum \mathbf F = 0
$$

In dynamics:

$$
\sum \mathbf F = m\mathbf a
$$

If the resultant force is nonzero, the object accelerates. Forces do not need to balance for Newton's second law to apply.

## Does Newton's second law require constant acceleration?

No. Newton's second law is valid instant-by-instant:

$$
\sum \mathbf F(t,x,v) = m\mathbf a
$$

or

$$
 m\frac{d\mathbf v}{dt} = \sum \mathbf F
$$

However, the familiar constant-acceleration kinematics equations require constant acceleration:

$$
v = v_0 + at
$$

$$
x = x_0 + v_0t + \frac{1}{2}at^2
$$

$$
v^2 = v_0^2 + 2a(x-x_0)
$$

## Choosing between methods

### Use kinematics when

- The problem describes motion.
- Time, displacement, velocity, and acceleration are available.
- Forces have already been converted into a known acceleration.

Example: A car has constant acceleration $3\ \mathrm{m/s^2}$ for $4\ \mathrm{s}$. Find its final speed.

### Use Newton's second law when

- You need a force, acceleration, normal force, tension, or friction.
- A free-body diagram is central.
- Forces must be resolved into components.

For a block sliding down an incline:

$$
\sum F_{\parallel} = mg\sin\theta - \mu_k N = ma
$$

### Use work-energy when

- The problem gives a distance or height.
- Speed is requested.
- Time is absent or irrelevant.
- Forces may vary with position.

$$
T_1 + U_{1\to2} = T_2
$$

For a constant force:

$$
U = Fs\cos\phi
$$

For a block moving down a rough incline:

$$
mg(s\sin\theta) - \mu_k Ns
= \frac{1}{2}mv_2^2 - \frac{1}{2}mv_1^2
$$

### Use impulse-momentum when

- A force acts over a known time interval.
- The event is short, such as an impact or collision.
- A velocity or momentum change is requested.

$$
\int_{t_1}^{t_2}\mathbf F\,dt
= m\mathbf v_2 - m\mathbf v_1
$$

For a constant force:

$$
\mathbf F\Delta t = m(\mathbf v_2 - \mathbf v_1)
$$

## Worked comparison

A cart starts from rest and is pushed by a constant force.

- Pushed for $5\ \mathrm{s}$; find final velocity → **impulse-momentum**.
- Pushed through $5\ \mathrm{m}$; find final speed → **work-energy**.
- Given acceleration and time; find final velocity → **kinematics**.
- Given the forces; find acceleration → **Newton's second law**.

## Common mistakes

1. Choosing impulse-momentum merely because a force appears. Impulse requires force over time.
2. Choosing work-energy merely because speed is requested. It is especially useful when distance or height is given.
3. Assuming forces must balance in every problem. Unbalanced forces cause acceleration.
4. Using constant-acceleration equations before checking whether acceleration is constant.
5. Treating Newton's second law as limited to constant acceleration. It is not.
6. Forgetting that friction does negative work when it opposes motion.

## Fast decision procedure

1. Is this mainly a force/acceleration problem? → Newton's second law.
2. Is a time interval or impact central? → impulse-momentum.
3. Is a distance or height central, with speed requested? → work-energy.
4. Are motion variables given and acceleration known/constant? → kinematics.
5. Could several methods work? Choose the method with fewer unknown intermediate quantities.

## Retrieval checkpoint

1. A force acts for $2\ \mathrm{s}$, and final velocity is requested. → impulse-momentum.
2. A block moves $3\ \mathrm{m}$ down an incline, and final speed is requested. → work-energy.
3. A free-body diagram is given and acceleration is requested. → Newton's second law.
4. Initial velocity, constant acceleration, and time are given. → kinematics.

## Summary

$$
\text{time} \longrightarrow \text{impulse-momentum}
$$

$$
\text{distance/height} \longrightarrow \text{work-energy}
$$

$$
\text{forces} \longrightarrow \text{Newton's second law}
$$

$$
\text{motion variables} \longrightarrow \text{kinematics}
$$

The key is to identify the shortest bridge between the given information and the requested unknown.
