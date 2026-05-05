"""Domain exceptions."""


class OAWMError(Exception):
    """Base exception."""


class InvariantError(OAWMError):
    """A core invariant was violated."""


class TransitionError(InvariantError):
    """A lane transition is not admissible."""


class FailClosedError(OAWMError):
    """The strict profile blocked an action because evidence was insufficient."""


class NotFoundError(OAWMError):
    """Requested object was not found."""

