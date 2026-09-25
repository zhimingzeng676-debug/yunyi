def is_ready(samples: list[bool], threshold: int = 3) -> bool:
    if threshold <= 0:
        raise ValueError("threshold must be positive")
    return len(samples) >= threshold and all(samples[-threshold:])
