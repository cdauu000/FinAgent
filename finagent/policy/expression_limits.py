"""Iterative pre-validation prevents excessive AST nesting before Pydantic recurses."""

from pydantic import BaseModel

# A61 owner-approved technical budgets; not measured financial/quality thresholds.
AST_MAX_DEPTH = 32
AST_MAX_NODES = 1024
AST_MAX_INPUTS = 100


def check_expression_roots(roots: tuple[object, ...]) -> None:
    stack: list[tuple[object, int, frozenset[int]]] = [(root, 1, frozenset()) for root in roots]
    count = 0
    while stack:
        node, depth, ancestors = stack.pop()
        count += 1
        if depth > AST_MAX_DEPTH:
            raise ValueError("AST_MAX_DEPTH_EXCEEDED")
        if count > AST_MAX_NODES:
            raise ValueError("AST_MAX_NODES_EXCEEDED")
        if id(node) in ancestors:
            raise ValueError("AST_CYCLE_FORBIDDEN")
        if isinstance(node, BaseModel):
            data = node.__dict__
        elif isinstance(node, dict):
            data = node
        else:
            continue  # The ordinary tagged schema rejects malformed leaf values.
        path = ancestors | {id(node)}
        children: tuple[object, ...] = ()
        if data.get("kind") == "binary":
            children = (data.get("left"), data.get("right"))
        elif data.get("kind") == "aggregate":
            values = data.get("inputs")
            if isinstance(values, (list, tuple)):
                if len(values) > AST_MAX_INPUTS:
                    raise ValueError("AST_MAX_INPUTS_EXCEEDED")
                children = tuple(values)
        stack.extend((child, depth + 1, path) for child in children)


def guard_expression(value: object) -> object:
    check_expression_roots((value,))
    return value
