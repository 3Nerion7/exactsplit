# Third-party tooling

ExactSplit source is MIT-licensed. This repository does not redistribute compiler binaries or an external allocation implementation.

* **Fe 26.5.0**: external compiler and standard library, from the [official Argot repository release](https://github.com/argotorg/fe/releases/tag/v26.5.0), commit `3dab95f8eebdccf9a2382bb59a33f7bbd03540ca`. The release source includes [Apache-2.0 licensing](https://github.com/argotorg/fe/blob/v26.5.0/LICENSE-APACHE). The verifier pins the published Windows and Linux executable hashes. Downloads are stored in ignored `.tools/`.
* **Python**: an independently installed interpreter. Verification uses only its standard library, including exact fractions, integer arithmetic and subprocess execution. No Python packages are vendored or installed.

The Fe documentation was consulted for language and effect syntax. The allocation implementation, fixtures and Python reference are project-specific work. Generated Fe tests are produced locally from the reviewable JSON fixtures and excluded from source distribution.
