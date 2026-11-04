# History instrumentation: member enumeration supplement

Record before execution: both reference and instrumented runs temporarily wrap
only the EPCG constructor to keep references to each constructed member, so
member reset/localization lists can be compared individually after the run.
The reference run does not wrap history arrays, index access, concatenation or
numerical methods. Constructor and `RETURN_SIGNALS` hooks are restored in
`finally`; the construction observer does not change constructor arguments,
outputs or numeric state. This additional common observational hook is included
in the meaning of the reference run. All other conditions remain unchanged.
A copied branch may bypass the constructor: record such coverage as a limitation
and do not infer member-event equivalence for an unenumerated copy.
