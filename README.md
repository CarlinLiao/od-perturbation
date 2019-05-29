# od-perturbation

How does the result of the Traffic Assignment Problem (TAP) change we perturb some or all the flows in the origin-destination (OD) matrix? These perturbations simulate sampling uncertainty or errors.

## Setup

This package depends on a modified version of Dr. Stephen Boyles's [Algorithm B implementation in C](https://github.com/spartalab/tap-b), specifically [my fork](https://github.com/CarlinLiao/tap-b) (as well as a bunch of other Python packages managed by `pip` or `conda`).

Begin by cloning [my fork](https://github.com/CarlinLiao/tap-b.git) into a subdirectory called `tap-b/` that the rest of the repository can refer to.
