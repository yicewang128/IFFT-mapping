import sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from run_combined import add_layers


def test_add_layers_clips_without_uint8_overflow_and_keeps_hidden_pixels_hidden():
    a=np.array([[[200,20,0,255],[255,255,255,0]]],dtype=np.uint8)
    b=np.array([[[100,0,50,255],[10,20,30,255]]],dtype=np.uint8)
    out,fraction=add_layers([a,b])
    np.testing.assert_array_equal(out,[[[255,20,50],[10,20,30]]])
    assert fraction==.5
    np.testing.assert_array_equal(out,add_layers([b,a])[0])
    with pytest.raises(ValueError):add_layers([])
    with pytest.raises(ValueError):add_layers([a,b[:,:1]])


def test_add_layers_rounds_only_after_sum():
    a=np.array([[[1,0,0,100]]],dtype=np.uint8)
    out,_=add_layers([a,a])
    assert out[0,0,0]==1  # rounding each black layer first would yield 0
