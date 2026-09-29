# Curved Motion and Banked Curves

## Core intuition

Velocity can change even when speed is constant because velocity includes direction. In circular/curved motion, acceleration has two useful perpendicular components:

- Tangential: changes speed
- Normal/centripetal: changes direction

## Normal–tangential acceleration

\[
a_t=\frac{dv}{dt}
\]

\[
a_n=\frac{v^2}{\rho}
\]

where:

- \(v\) = speed
- \(\rho\) = radius of curvature
- \(a_n\) points toward the center of curvature

Total acceleration:

\[
a=\sqrt{a_t^2+a_n^2}
\]

Force equations:

\[
\sum F_t=ma_t
\]

\[
\sum F_n=m\frac{v^2}{\rho}
\]

## Derivation preferred by learner

For uniform circular motion:

\[
x(t)=r\cos(\omega t),\qquad y(t)=r\sin(\omega t)
\]

Velocity:

\[
\vec v(t)=\langle -r\omega\sin(\omega t),\ r\omega\cos(\omega t)\rangle
\]

Speed:

\[
|\vec v|=r\omega
\]

Acceleration:

\[
\vec a(t)=\langle -r\omega^2\cos(\omega t),\ -r\omega^2\sin(\omega t)\rangle
=-\omega^2\vec r(t)
\]

So acceleration points inward and has magnitude:

\[
a=r\omega^2=\frac{v^2}{r}
\]

## Vertical circular motion

At the bottom of a loop, inward is upward:

\[
N-mg=m\frac{v^2}{r}
\]

At the top of a loop, inward is downward:

\[
N+mg=m\frac{v^2}{r}
\]

Minimum speed to maintain contact at the top occurs when \(N=0\):

\[
v_{\min}=\sqrt{gr}
\]

## Flat curves and friction

For a flat curve without skidding, static friction provides inward force:

\[
f_s=m\frac{v^2}{r}
\]

with

\[
f_s\le \mu_s N=\mu_s mg
\]

Therefore:

\[
v_{\max}=\sqrt{\mu_s g r}
\]

Important distinction:

| Situation | Friction model |
|---|---|
| rolling without slipping | static friction |
| sliding/skidding | kinetic friction |

## Frictionless banked curve

Banked means the road is tilted sideways. On a frictionless banked curve, the horizontal component of the normal force provides centripetal force.

Vertical:

\[
N\cos\theta=mg
\]

Radial/inward:

\[
N\sin\theta=m\frac{v^2}{r}
\]

Divide equations:

\[
\tan\theta=\frac{v^2}{rg}
\]

Design speed:

\[
v=\sqrt{rg\tan\theta}
\]

## Common mistakes repaired

- Constant speed does not imply zero acceleration if direction changes.
- A moving tire does not automatically mean kinetic friction; slipping is required.
- On a frictionless banked curve, there is no friction force; inward force comes from the normal force component.

## Source

Aligned with NCEES FE Handbook, Dynamics section: particle curvilinear motion, normal/tangential components, friction, rigid-body/rolling constraints, and free/forced vibration overview.
