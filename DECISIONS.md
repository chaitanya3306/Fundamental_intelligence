# FinSight AI Decision Log

Decisions may be marked Accepted, Proposed or Superseded. A decision is not implemented until code/tests support it.

| ID | Decision | Status |
|---|---|---|
| D-001 | Initial product scope is supported US-listed companies, aligned to the six references. | Accepted product direction |
| D-002 | Streamlit is the initial UI. | Accepted |
| D-003 | FastAPI and Pydantic provide typed application contracts. | Accepted target |
| D-004 | PostgreSQL is target persistence; SQLAlchemy and Alembic manage access/schema. SQLite may be used for compatible tests. | Accepted target |
| D-005 | Build reliable fundamental analysis before AI/ML, WhaleWatch AI or Combined Analysis. | Accepted scope |
| D-006 | Financial formulas live in testable analysis modules, not Streamlit. | Accepted |
| D-007 | Missing is not zero; distinguish reported zero, missing, unavailable, invalid and not applicable. | Accepted |
| D-008 | Annual, quarterly and TTM observations are distinct. | Accepted data requirement |
| D-009 | Provider adapters and explicit source/freshness provenance are preferred. | Accepted target |
| D-010 | No fabricated financial/market data or news. | Accepted |
| D-011 | Build vertical slices and verify provider → DB → calculation → API → UI. | Accepted delivery method |

## Decision record template
### D-XXX — Title
- Status:
- Context/problem:
- Decision:
- Alternatives considered:
- Trade-offs:
- Migration/implementation impact:
- Date:
