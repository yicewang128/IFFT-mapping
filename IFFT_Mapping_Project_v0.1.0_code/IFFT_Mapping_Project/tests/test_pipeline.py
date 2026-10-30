"""Scientific invariants, not a claim of physical grain-boundary validation."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
import numpy as np
import pytest
from scipy.ndimage import gaussian_filter
from PIL import Image
import tifffile
from pipeline import (amplitude_map, linear_signed_display, render_layers, composite,
                      run_pipeline, otsu_threshold, tem_display)


def test_signed_linear_mapping_preserves_nonzero_frequency_and_distinguishes_sign():
    x=np.arange(256);f=7*np.cos(2*np.pi*x/16)
    L,_,clipped=linear_signed_display(f)
    # An affine display adds DC but does not double the lattice frequency.
    assert np.argmax(np.abs(np.fft.rfft(L-L.mean())))==16
    assert L[0]>L[8] and clipped==0


def test_abs_smoothing_order_and_no_rms():
    f=np.zeros((101,101));f[50,49]=-4;f[50,51]=4
    absolute,smooth=amplitude_map(f,5)
    np.testing.assert_array_equal(absolute,np.abs(f))
    np.testing.assert_allclose(smooth,gaussian_filter(np.abs(f),5,mode="reflect",truncate=4))
    assert smooth[50,50]>abs(gaussian_filter(f,5)[50,50])
    assert not np.allclose(smooth,np.sqrt(gaussian_filter(f*f,5)))


def test_binary_alpha_preserves_selected_rgb_including_black_minimum():
    L=np.array([[0,.5,1.]])
    mask=np.array([[True,False,True]])
    rgb,rgba,black=render_layers(L,mask)
    assert rgba[0,0,3]==255  # selected darkest lattice pixel must remain opaque
    assert rgba[0,1,3]==0
    np.testing.assert_array_equal(rgba[mask,:3],rgb[mask])
    assert np.all(black[~mask]==0)


def test_original_tem_pixels_outside_selection_are_exact():
    base=np.arange(18,dtype=np.uint8).reshape(2,3,3)
    green=np.full_like(base,80);mask=np.array([[True,False,False],[True,True,False]])
    b=base.copy();out=composite(base,green,mask,.7)
    np.testing.assert_array_equal(base,b)
    np.testing.assert_array_equal(out[~mask],base[~mask])
    with pytest.raises(ValueError):tem_display(np.zeros((2,3),np.float32))
    with pytest.raises(ValueError):composite(base,green[:1],mask)


def test_otsu_separates_clear_modes():
    a=np.concatenate([np.linspace(0,1,500),np.linspace(10,11,500)])
    t=otsu_threshold(a)
    assert 1<=t<10


def test_run_keeps_input_bytes_calibration_and_png_alpha(tmp_path):
    f=np.cos(np.arange(64)[None,:]*2*np.pi/8)*np.linspace(.1,3,64)[:,None]
    p=tmp_path/"source.tif";tifffile.imwrite(p,f.astype(np.float32),imagej=True,resolution=(20,20),metadata={"unit":"nm"})
    before=p.read_bytes();out=tmp_path/"run"
    m=run_pipeline(p,out,{"sigma_px":5,"threshold":{"mode":"otsu"}},make_figures=False)
    assert before==p.read_bytes()
    np.testing.assert_array_equal(tifffile.imread(out/"00_signed_ifft_float32.tif"),f.astype(np.float32))
    alpha=np.array(Image.open(out/"05_selected_green_transparent.png"))[...,3]
    np.testing.assert_array_equal(alpha,tifffile.imread(out/"04_selection_mask_uint8.tif"))
    with tifffile.TiffFile(out/"03_abs_gaussian_float32.tif") as tf:
        assert tf.pages[0].compression==1
        assert tf.imagej_metadata["unit"]=="nm"
    assert m["input"]["calibration"]["pixel_width"]==.05
    with pytest.raises(FileExistsError):run_pipeline(p,out,{})
