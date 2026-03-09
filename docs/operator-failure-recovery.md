# Operator Guide: Failure Recovery
(Pending integration features)
- If model crashes: Review `state/logs/model_host.log`
- If memory corrupts: Restore SQLite DB from backup (WIP).
- If update fails: Use `heidi learning rollback`.
