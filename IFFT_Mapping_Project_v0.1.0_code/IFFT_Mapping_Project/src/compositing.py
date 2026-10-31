"""Display compositing of RGBA8 layers in encoded RGB channel space.

Sb grouping is weighted color plus union opacity, NOT sequential source-over
between Sb families and NOT a physical intensity/probability calculation.
"""
import numpy as np


def _validate(layer, shape=None):
    if not isinstance(layer, np.ndarray) or layer.dtype != np.uint8 or layer.ndim != 3 or layer.shape[-1] != 4:
        raise ValueError('Expected RGBA uint8 layer')
    if shape is not None and layer.shape != shape:
        raise ValueError('Layer dimensions differ; no automatic registration')


def group_rgba(layers):
    """RGB=sum(alpha*RGB)/sum(alpha); A=1-product(1-alpha), independent of order."""
    layers = list(layers)
    if not layers:
        raise ValueError('At least one layer required')
    _validate(layers[0])
    shape = layers[0].shape
    weights = np.zeros(shape[:2], dtype=np.float64)
    numerator = np.zeros((*shape[:2], 3), dtype=np.float64)
    transmittance = np.ones(shape[:2], dtype=np.float64)
    for layer in layers:
        _validate(layer, shape)
        # Integer alpha8 weights avoid order-sensitive floating-point RGB half-ties.
        weight = layer[..., 3].astype(np.float64)
        weights += weight
        numerator += weight[..., None] * layer[..., :3]
        transmittance *= 1 - weight / 255
    color = np.divide(numerator, weights[..., None], out=np.zeros_like(numerator), where=weights[..., None] > 0)
    return np.dstack((np.rint(color).astype(np.uint8), np.rint(255 * (1-transmittance)).astype(np.uint8)))


def source_over_rgba(top, bottom):
    """Ordinary top-over-bottom alpha compositing; output is straight RGBA8."""
    _validate(top)
    _validate(bottom, top.shape)
    at = top[..., 3:4].astype(np.float64) / 255
    ab = bottom[..., 3:4].astype(np.float64) / 255
    alpha = at + ab * (1-at)
    premultiplied = top[..., :3] * at + bottom[..., :3] * ab * (1-at)
    color = np.divide(premultiplied, alpha, out=np.zeros_like(premultiplied), where=alpha > 0)
    result = np.concatenate((np.rint(color).astype(np.uint8), np.rint(255*alpha).astype(np.uint8)), axis=-1)
    # Preserve hidden RGB too when the top has no contribution.
    result[top[..., 3] == 0] = bottom[top[..., 3] == 0]
    return result


def on_black(rgba):
    """Flatten using the exact exported alpha8, matching PNG display on black."""
    _validate(rgba)
    return np.rint(rgba[..., :3] * (rgba[..., 3:4].astype(np.float64)/255)).astype(np.uint8)
