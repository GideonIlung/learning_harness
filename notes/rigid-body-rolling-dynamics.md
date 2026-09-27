# Rigid-Body Rolling Dynamics

## Why this matters

Rigid bodies can translate and rotate at the same time. FE dynamics problems often require both force equations and moment equations, plus a rolling constraint.

## Core idea

For planar rigid-body motion:

\[
\sum F_x = m a_{Gx}
\]

\[
\sum F_y = m a_{Gy}
\]

\[
\sum M_G = I_G \alpha
\]

where:

- \(G\) = center of mass
- \(m\) = mass
- \(a_G\) = acceleration of the center of mass
- \(I_G\) = mass moment of inertia about the center of mass
- \(\alpha\) = angular acceleration

Translation is caused by net force. Rotation is caused by net moment/torque.

## Important analogy

| Linear motion | Rotational motion |
|---|---|
| \(\sum F = ma\) | \(\sum M = I\alpha\) |
| force causes linear acceleration | moment causes angular acceleration |
| mass \(m\) resists translation | inertia \(I\) resists rotation |
| \(T=\frac12 mv^2\) | \(T=\frac12 I\omega^2\) |

## Rolling without slipping

For a body of radius \(r\):

\[
v_G = \omega r
\]

\[
a_G = \alpha r
\]

These are constraint equations, not force laws.

## Worked example: solid cylinder rolling down an incline

A solid cylinder has:

\[
I_G=\frac12 mr^2
\]

Forces along the slope:

- \(mg\sin\theta\) down the incline
- static friction \(f_s\) up the incline

Translation along slope:

\[
mg\sin\theta - f_s = ma
\]

Rotation about center:

\[
f_s r = I_G\alpha
\]

Rolling constraint:

\[
a=\alpha r
\]

Substitute:

\[
f_s r = \left(\frac12 mr^2\right)\left(\frac{a}{r}\right)
\]

\[
f_s=\frac12 ma
\]

Then:

\[
mg\sin\theta - \frac12 ma = ma
\]

\[
\boxed{a=\frac23 g\sin\theta}
\]

## Common mistakes

1. Using only \(\sum F=ma\) for rolling objects.
2. Using \(\sum F=I\alpha\), which mixes linear force with rotational inertia.
3. Thinking static friction is zero just because there is no slipping.
4. Forgetting that static friction can provide torque without doing work at the contact point for ideal rolling.

## Checkpoints from session

- Correctly identified that rolling cylinder dynamics generally requires both \(\sum F=ma\) and \(\sum M=I\alpha\). Confidence: 70%.
- Correctly identified static friction direction as up the incline for a cylinder rolling down an incline. Confidence: 80%.
