# General Dynamics Equations

## 1. Kinematics

Kinematics describes motion without considering its causes.

Position:

$$
\mathbf r=\mathbf r(t)
$$

Velocity:

$$
\mathbf v(t)=\frac{d\mathbf r}{dt}
$$

Acceleration:

$$
\mathbf a(t)=\frac{d\mathbf v}{dt}=\frac{d^2\mathbf r}{dt^2}
$$

Recover velocity from acceleration:

$$
\mathbf v(t)=\mathbf v(t_0)+\int_{t_0}^{t}\mathbf a(\tau)\,d\tau
$$

Recover position from velocity:

$$
\mathbf r(t)=\mathbf r(t_0)+\int_{t_0}^{t}\mathbf v(\tau)\,d\tau
$$

Here, $\tau$ is a dummy time variable.

## 2. Newton's second law

General momentum form:

$$
\sum \mathbf F_{\text{external}}=\frac{d\mathbf p}{dt}
$$

Momentum:

$$
\mathbf p=m\mathbf v
$$

For constant mass:

$$
\sum \mathbf F_{\text{external}}=m\mathbf a
$$

For variable mass:

$$
\sum \mathbf F_{\text{external}}=\frac{d}{dt}(m\mathbf v)
$$

Newton's law determines acceleration from the forces:

$$
\mathbf a(t)=\frac{1}{m}\sum\mathbf F(t,\mathbf r,\mathbf v)
$$

## 3. Work-energy

Differential work:

$$
dU=\mathbf F\cdot d\mathbf r
$$

Total work from position $1$ to position $2$:

$$
U_{1\to2}=\int_{\mathbf r_1}^{\mathbf r_2}\mathbf F\cdot d\mathbf r
$$

Work-energy theorem:

$$
U_{1\to2}=T_2-T_1
$$

Translational kinetic energy:

$$
T=\frac{1}{2}mv^2
$$

Therefore:

$$
\int_{\mathbf r_1}^{\mathbf r_2}\mathbf F_{\text{net}}\cdot d\mathbf r
=\frac{1}{2}mv_2^2-\frac{1}{2}mv_1^2
$$

Including potential energy:

$$
T_1+V_1+W_{\text{nonconservative}}=T_2+V_2
$$

For gravity near Earth:

$$
V_g=mgy
$$

## 4. Impulse-momentum

Differential impulse:

$$
 d\mathbf J=\mathbf F\,dt
$$

Total impulse from $t_1$ to $t_2$:

$$
\mathbf J_{1\to2}=\int_{t_1}^{t_2}\mathbf F(t)\,dt
$$

Impulse-momentum theorem:

$$
\int_{t_1}^{t_2}\sum\mathbf F_{\text{external}}\,dt=\mathbf p_2-\mathbf p_1
$$

For constant mass:

$$
\int_{t_1}^{t_2}\sum\mathbf F_{\text{external}}\,dt=m\mathbf v_2-m\mathbf v_1
$$

If force is constant:

$$
\mathbf F_{\text{net}}\Delta t=m(\mathbf v_2-\mathbf v_1)
$$

## One-line comparison

$$
\mathbf a=\frac{d\mathbf v}{dt}
$$

$$
\sum\mathbf F=m\mathbf a
$$

$$
\int \mathbf F\cdot d\mathbf r=\Delta T
$$

$$
\int \mathbf F\,dt=\Delta\mathbf p
$$

- **Kinematics:** integrates acceleration over time.
- **Newton's second law:** relates force to instantaneous acceleration.
- **Work-energy:** integrates force over distance.
- **Impulse-momentum:** integrates force over time.

## Important assumptions

- $m$ is constant unless the variable-mass form is explicitly used.
- Work-energy uses the net work of the relevant forces.
- Impulse-momentum uses the net external impulse.
- The constant-acceleration kinematics formulas are special cases, not the general kinematics equations.
