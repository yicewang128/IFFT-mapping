import sys
from pathlib import Path
from itertools import permutations
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from compositing import group_rgba, source_over_rgba, on_black


def test_group_preserves_single_layer_and_ignores_hidden_color():
    a=np.array([[[80,150,255,128],[255,255,255,0]]],dtype=np.uint8)
    transparent=np.array([[[255,0,0,0],[255,0,0,0]]],dtype=np.uint8)
    np.testing.assert_array_equal(on_black(group_rgba([a])),on_black(a))
    np.testing.assert_array_equal(group_rgba([a]),group_rgba([a,transparent]))
    assert np.all(group_rgba([transparent])==0)


def test_group_union_and_color_are_independent_of_family_order():
    layers=[np.array([[[255,0,0,128]]],dtype=np.uint8),
            np.array([[[0,0,255,128]]],dtype=np.uint8),
            np.array([[[90,255,1,0]]],dtype=np.uint8)]
    reference=np.array([[[128,0,128,192]]],dtype=np.uint8)
    for order in permutations(layers):np.testing.assert_array_equal(group_rgba(order),reference)


def test_top_layer_occlusion_and_transparency_endpoints():
    bottom=np.array([[[0,255,0,255],[0,200,0,100],[3,4,5,0]]],dtype=np.uint8)
    top=np.array([[[255,0,0,255],[1,2,3,0],[255,0,0,0]]],dtype=np.uint8)
    got=source_over_rgba(top,bottom)
    np.testing.assert_array_equal(got[0,0],top[0,0])
    np.testing.assert_array_equal(got[0,1:],bottom[0,1:])
    # Half-opacity red over opaque green: confirms direction, not additive mixing.
    got=source_over_rgba(np.array([[[255,0,0,128]]],dtype=np.uint8),bottom[:,:1])
    np.testing.assert_array_equal(got,[[[128,127,0,255]]])


def test_compositing_rejects_incompatible_inputs():
    a=np.zeros((2,3,4),dtype=np.uint8)
    with pytest.raises(ValueError):group_rgba([])
    with pytest.raises(ValueError):group_rgba([a,a.astype(float)])
    with pytest.raises(ValueError):source_over_rgba(a,a[:,:1])
    with pytest.raises(ValueError):on_black(a[...,:3])
