# Contextual maintenance selection

A clear “do it” selects one fresh offered item with exact item, operation, source
and authority versions. It does not require command syntax. Questions, multiple
offers, expired offers and changed source/authority return read-only or selection
required; no guessed execution starts.

`Application.handoff` calls selection and complete original-work retention in
one route. The supplied original objective, Task/execution, source references,
constraints, assumptions and authority must equal the offered original record.
The retained record is not a second Task ledger. Current Task intake still owns
activation and all action permissions remain separate.

After maintenance completes or is blocked, reread original work and relevant
integrity, scope, sources, assumptions and authority. `continue_original` requires
the retained record still matches its selected offer and current original hash;
only a completed prerequisite with current checks returns continuation-ready.
It never activates a Task itself. Preserve remaining blockers and current owners.

If the original work does not depend on the selected maintenance outcome, the
caller can explicitly pass `maintenance_required=False` to `continue_original`.
A blocked maintenance item then permits original-work continuation only when
its retained objective, sources, assumptions, scope, integrity and authority are
still current. The default remains a required prerequisite, which holds
continuation while maintenance is blocked. This choice does not create a Task or
change either execution's owner.
