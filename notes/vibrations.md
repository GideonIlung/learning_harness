# Vibrations: Single-Degree-of-Freedom Systems

## Why this matters

FE vibration problems often ask for natural frequency, damping ratio, resonance behavior, or forced-response amplification. The core model is a mass, spring, damper, and sometimes an external force.

Source: `sources/fe-handbook-10-6.pdf`, Dynamics section, Free and Forced Vibration.

## Core model

For a linear mass-spring-damper system:

\[
m\ddot{x}+c\dot{x}+kx=F(t)
\]

where:

- \(m\) = mass
- \(c\) = viscous damping coefficient
- \(k\) = spring stiffness
- \(x\) = displacement from equilibrium
- \(\dot{x}\) = velocity
- \(\ddot{x}\) = acceleration
- \(F(t)\) = external applied force

Term meanings:

| Term | Meaning |
|---|---|
| \(m\ddot{x}\) | inertia effect |
| \(c\dot{x}\) | damping force proportional to velocity |
| \(kx\) | spring restoring force |
| \(F(t)\) | external forcing |

## Natural circular frequency

Undamped free vibration:

\[
m\ddot{x}+kx=0
\]

Divide by \(m\):

\[
\ddot{x}+\frac{k}{m}x=0
\]

Compare with standard form:

\[
\ddot{x}+\omega_n^2x=0
\]

Therefore:

\[
\omega_n^2=\frac{k}{m}
\]

\[
\boxed{\omega_n=\sqrt{\frac{k}{m}}}
\]

Key intuition:

```text
larger k  -> stiffer spring -> faster oscillation -> larger ωn
larger m  -> more inertia   -> slower oscillation -> smaller ωn

ωn = sqrt(stiffness / inertia)
```

Important unit check:

\[
\frac{k}{m}\sim \frac{1}{s^2}
\]

so

\[
\sqrt{\frac{k}{m}}\sim \frac{1}{s}
\]

matching rad/s.

## Circular frequency, frequency, and period

\[
\omega_n = \sqrt{\frac{k}{m}} \quad [\mathrm{rad/s}]
\]

\[
f_n=\frac{\omega_n}{2\pi} \quad [\mathrm{Hz}]
\]

\[
T_n=\frac{1}{f_n}=\frac{2\pi}{\omega_n} \quad [\mathrm{s}]
\]

Visual:

```text
ωn = rad/s       angular/circular frequency
fn = cycles/s    ordinary frequency, Hz
Tn = s/cycle     period

ωn = 2π fn
```

## Damping ratio

Critical damping coefficient:

\[
\boxed{c_c=2m\omega_n=2\sqrt{km}}
\]

Damping ratio:

\[
\boxed{\zeta=\frac{c}{c_c}}
\]

Behavior:

| \(\zeta\) | Behavior |
|---:|---|
| 0 | undamped oscillation |
| \(0<\zeta<1\) | underdamped: oscillates while decaying |
| 1 | critically damped: fastest return without oscillation |
| \(>1\) | overdamped: no oscillation, slower return |

Visual:

```text
undamped:       ~~~~~~~~ constant amplitude
underdamped:    ~~~~\___ decaying oscillation
critical:       \____    fastest no overshoot
overdamped:     \_____   slower no overshoot
```

## Forced vibration and resonance

For sinusoidal forcing:

\[
F(t)=F_0\sin(\omega t)
\]

There are two important frequencies:

```text
ωn = natural frequency of system
ω  = external forcing frequency
```

Resonance occurs when:

\[
\omega \approx \omega_n
\]

especially when damping is small.

Swing intuition:

```text
forcing rhythm matches natural rhythm
            ↓
each push adds energy at the right time
            ↓
large vibration amplitude
```

## Forced response amplification

Static displacement from force amplitude:

\[
x_{static}=\frac{F_0}{k}
\]

Frequency ratio:

\[
r=\frac{\omega}{\omega_n}
\]

Dynamic amplification factor:

\[
\frac{X}{F_0/k}
=
\frac{1}
{\sqrt{(1-r^2)^2+(2\zeta r)^2}}
\]

where:

- \(X\) = steady-state vibration amplitude
- \(F_0/k\) = static deflection under force amplitude \(F_0\)
- \(r\) = frequency ratio
- \(\zeta\) = damping ratio

Key idea:

```text
r ≈ 1 and ζ small -> large amplification
```

## Torsional vibration analogy

Linear vibration:

\[
\omega_n=\sqrt{\frac{k}{m}}
\]

Torsional vibration:

\[
\omega_n=\sqrt{\frac{k_t}{I}}
\]

where:

- \(k_t\) = torsional stiffness
- \(I\) = mass moment of inertia

Same structure:

```text
natural frequency = sqrt(stiffness / inertia)
```

## Worked examples from session

### Example 1: Natural circular frequency

Given:

\[
m=10\ \mathrm{kg}, \qquad k=2500\ \mathrm{N/m}
\]

\[
\omega_n=\sqrt{\frac{k}{m}}=\sqrt{\frac{2500}{10}}=\sqrt{250}=15.8\ \mathrm{rad/s}
\]

### Example 2: Natural frequency in Hz

\[
f_n=\frac{\omega_n}{2\pi}=\frac{15.8}{2\pi}=2.52\ \mathrm{Hz}
\]

### Example 3: Damping ratio

Given:

\[
m=10\ \mathrm{kg},\quad k=2500\ \mathrm{N/m},\quad c=100\ \mathrm{N\cdot s/m}
\]

Using \(\omega_n=15.8\ \mathrm{rad/s}\):

\[
c_c=2m\omega_n=2(10)(15.8)=316\ \mathrm{N\cdot s/m}
\]

\[
\zeta=\frac{c}{c_c}=\frac{100}{316}=0.316
\]

Since \(0<\zeta<1\), the system is underdamped.

## Learner evidence from session

- Correctly answered natural frequency calculation after repairing initial confusion between \(k/m\) and \(\sqrt{k/m}\).
- Correctly converted rad/s to Hz using \(f=\omega/(2\pi)\).
- Correctly computed damping ratio with moderate confidence.
- Correctly recognized near-resonance behavior, but with low confidence.

## Review later

- Practice forced-vibration frequency ratio \(r=\omega/\omega_n\).
- Apply amplification factor formula.
- Strengthen resonance intuition and damping effects near \(r=1\).

## Session update: forced vibration start

- Reviewed natural circular frequency: \(\omega_n=\sqrt{k/m}\).
- Correctly recognized near-resonance when forcing frequency \(\omega\) is close to natural frequency \(\omega_n\).
- Introduced frequency ratio:

\[
r=\frac{\omega}{\omega_n}
\]

- Learner correctly computed \(r=10/40=0.25\) and identified it as not near resonance.
- Next time: continue with dynamic amplification factor

\[
M=\frac{1}{\sqrt{(1-r^2)^2+(2\zeta r)^2}}
\]

and practice calculating vibration amplitude \(X=M(F_0/k)\).
