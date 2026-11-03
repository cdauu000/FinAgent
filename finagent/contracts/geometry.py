import math
from dataclasses import dataclass

from finagent.contracts.errors import ProcessingError
from finagent.store.models import BoundingBox


@dataclass(frozen=True)
class Affine:
    """Column-vector transform: (a*x+c*y+e, b*x+d*y+f)."""

    a: float = 1
    b: float = 0
    c: float = 0
    d: float = 1
    e: float = 0
    f: float = 0

    def __post_init__(self) -> None:
        if not all(math.isfinite(v) for v in (self.a, self.b, self.c, self.d, self.e, self.f)):
            raise ProcessingError("INVALID_TRANSFORM")
        if abs(self.a * self.d - self.b * self.c) < 1e-12:
            raise ProcessingError("SINGULAR_TRANSFORM")

    def point(self, x: float, y: float) -> tuple[float, float]:
        return self.a * x + self.c * y + self.e, self.b * x + self.d * y + self.f

    def then(self, other: "Affine") -> "Affine":
        return Affine(
            other.a * self.a + other.c * self.b,
            other.b * self.a + other.d * self.b,
            other.a * self.c + other.c * self.d,
            other.b * self.c + other.d * self.d,
            other.a * self.e + other.c * self.f + other.e,
            other.b * self.e + other.d * self.f + other.f,
        )

    def inverse(self) -> "Affine":
        det = self.a * self.d - self.b * self.c
        return Affine(
            self.d / det,
            -self.b / det,
            -self.c / det,
            self.a / det,
            (self.c * self.f - self.d * self.e) / det,
            (self.b * self.e - self.a * self.f) / det,
        )

    def bounds(self, box: BoundingBox) -> BoundingBox:
        points = [self.point(x, y) for x in (box.x1, box.x2) for y in (box.y1, box.y2)]
        return BoundingBox(
            x1=min(p[0] for p in points),
            y1=min(p[1] for p in points),
            x2=max(p[0] for p in points),
            y2=max(p[1] for p in points),
        )


def expanded_rotation(width: int, height: int, degrees: float) -> tuple[Affine, int, int]:
    if width <= 0 or height <= 0 or not math.isfinite(degrees):
        raise ProcessingError("INVALID_ROTATION")
    radians = math.radians(degrees)
    cosine, sine = math.cos(radians), math.sin(radians)
    # Snap quarter turns to avoid ceil(width+epsilon) introducing an extra pixel.
    cosine, sine = (0 if abs(v) < 1e-12 else v for v in (cosine, sine))
    base = Affine(cosine, sine, -sine, cosine)
    corners = [base.point(x, y) for x in (0, width) for y in (0, height)]
    left, top = min(p[0] for p in corners), min(p[1] for p in corners)
    w = math.ceil(max(p[0] for p in corners) - left - 1e-10)
    h = math.ceil(max(p[1] for p in corners) - top - 1e-10)
    return base.then(Affine(e=-left, f=-top)), w, h


def crop_bounds(box: BoundingBox, width: int, height: int) -> tuple[int, int, int, int]:
    if box.x2 > width or box.y2 > height:
        raise ProcessingError("CROP_OUTSIDE_RASTER")
    return math.floor(box.x1), math.floor(box.y1), math.ceil(box.x2), math.ceil(box.y2)
