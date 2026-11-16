# BizFlow ERP — Engineering Case Study & Quality Roadmap

**Portfolio:** [Digital Solution9](https://github.com/shakaleita/teamforge-saas/blob/main/PORTFOLIO.md) · **Repository:** [Source](https://github.com/shakaleita/bizflow-erp)  
**Stack:** Python, Flask, SQLite · **Status:** Local portfolio MVP; not certified production software.

## Implemented domain workflow
Suppliers, catalogue, purchase orders, single goods receipt and stock balances.

## Domain invariants
Goods receipts must not double-count; order quantities and pricing must remain nonnegative and precise; supplier and catalogue relationships must hold.

## Verification backlog (not yet proven)
- Repeated goods receipts do not duplicate stock
- Invalid purchase-order lines reject atomically
- Concurrent receipt simulation preserves ledger totals

## High-value engineering upgrades
1. Add approval states and staff authorization
2. Build stock-ledger reconciliation and database migrations
3. Stress test simultaneous receipts and backup restore

## Production release gate

Verify authentication and authorization, concurrency and rollback scenarios, schema migrations, CI and browser tests, backup/restore, synthetic-data staging deployment, accessibility, security review, and reproducible performance measurements. The current README describes a local MVP and should remain honest until this evidence is available.

**Scope:** The improvement list is a plan; it does not claim implementations or tests already exist.
