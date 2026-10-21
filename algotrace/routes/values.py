"""Reading the list of numbers a visitor typed, for the sorting and searching runs."""


def parse_values(raw, limit):
    """Read the comma separated list the user typed. Returns (values, error)."""
    if isinstance(raw, list):
        items = raw
    else:
        text = (raw or "").replace("\n", ",").strip()
        if not text:
            return None, "Enter some numbers, separated by commas."
        items = [part.strip() for part in text.split(",") if part.strip()]

    if not items:
        return None, "Enter some numbers, separated by commas."
    if len(items) > limit:
        return None, "That is %d values. Use %d or fewer so the cells stay readable." % (
            len(items), limit)

    values = []
    for item in items:
        if isinstance(item, bool) or not isinstance(item, (int, float, str)):
            return None, "%r is not a whole number." % (item,)
        try:
            values.append(int(str(item).strip()))
        except ValueError:
            return None, "%s is not a whole number. Use digits separated by commas." % item
    return values, None
