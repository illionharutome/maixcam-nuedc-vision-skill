# References

References are context for design review, not code-generation targets. Prefer MaixCAM-Pro/MaixPy v4 documentation and the current `$MV` protocol. Read `k230_reference_only.md` before consulting any K230/CanMV source.

Authorized upstream references supplied by the user:

- `https://github.com/2262727886-stack/mspm0g3507-car-kit.git`
- `https://gitee.com/allphata/tripod__head/tree/master`

Use the car-kit repository only for MSPM0 architectural ideas. Reserve `tripod__head` for a later MSPM0 execution-layer integration phase. Do not copy either repository's old binary protocol into the current `$MV` mainline.
