# Bounded sprintf-js compatibility package

Derived from sprintf-js 1.1.3 under its retained BSD license. This local dependency preserves formatting behavior while rejecting format strings longer than 65,536 characters and field widths or precisions above 10,000 before parsing or allocation. It mitigates GHSA-hp3w-g68c-fv3c. The package version records the local patch; it is not an upstream release. The root npm override applies it to every transitive consumer. Regression tests cover normal formatting and hostile width/precision values.
