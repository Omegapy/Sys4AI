"""Strict, stable ticket ordering without changing the supplied records."""


def order_tickets(records):
    """Return original records in a new list, ordered by descending urgency.

    IDs are raw, unique, nonblank strings. Urgency is an integer from 0 to 3,
    excluding booleans. Invalid batches raise ValueError at the first defect.
    The input and its nested values are never changed during this call.
    """
    if not isinstance(records, list):
        raise ValueError("records must be a list")

    seen_ids = set()
    for position, record in enumerate(records):
        location = f"records[{position}]"
        if not isinstance(record, dict):
            raise ValueError(f"{location} must be a dictionary")
        for field in ("id", "urgency"):
            if field not in record:
                raise ValueError(f"{location} is missing required field '{field}'")

        ticket_id = record["id"]
        if not isinstance(ticket_id, str) or not ticket_id.strip():
            raise ValueError(f"{location} id must be a nonblank string")
        if ticket_id in seen_ids:
            raise ValueError(f"{location} id is a duplicate")

        urgency = record["urgency"]
        if not isinstance(urgency, int) or isinstance(urgency, bool) or not 0 <= urgency <= 3:
            raise ValueError(f"{location} urgency must be an integer in 0..3, excluding booleans")
        seen_ids.add(ticket_id)

    indexed_records = list(enumerate(records))
    indexed_records.sort(key=lambda item: (-item[1]["urgency"], item[0]))
    return [record for _, record in indexed_records]
