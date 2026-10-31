"""Scientific and file-format regressions for continuous alpha and plane colors."""
import json
import sys
from pathlib import Path
import numpy as np
import pytest
import tifffile
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from pipeline import choose_alpha, render_layers, run_pipeline, composite, color_settings
import overlay_saved_run


def test_percentile_endpoints_and_linear_midpoint():
    s=np.arange(101,dtype=float).reshape(1,-1)
    cfg={'alpha':{'mode':'continuous','low':{'mode':'percentile','value':10},'full':{'mode':'percentile','value':90}}}
    a,spec=choose_alpha(s,cfg)
    assert spec=={'mode':'continuous','low':10.,'full':90.}
    assert a[0,10]==0 and a[0,50]==.5 and a[0,90]==1
    assert np.all(np.diff(a.ravel())>=0)
    cfg['alpha']['full']={'mode':'max'}
    maximum,_=choose_alpha(s,cfg)
    assert np.all(a>=maximum)
    assert np.mean(a==0)==np.mean(maximum==0)
    with pytest.raises(ValueError):choose_alpha(np.ones((2,2)),cfg)
    cfg['alpha']['low']={'mode':'percentile','value':float('nan')}
    with pytest.raises(ValueError):choose_alpha(s,cfg)


def test_tint_preserves_green_and_rgb_is_independent_of_alpha():
    L=np.linspace(0,1,10001).reshape(1,-1)
    cfg={'color_map':'green_white','white_start':.55,'white_max':230}
    green=render_layers(L,np.ones_like(L),cfg)[0]
    tint={**cfg,'color_map':'tint_white','color_rgb':[0,255,0]}
    np.testing.assert_array_equal(green,render_layers(L,np.ones_like(L),tint)[0])
    tint['color_rgb']=[0,160,255]
    rgb,rgba,black=render_layers(L,np.full_like(L,.25),tint)
    np.testing.assert_array_equal(rgb,render_layers(L,np.ones_like(L),tint)[0])
    np.testing.assert_array_equal(rgba[...,:3],rgb)
    np.testing.assert_array_equal(black,composite(np.zeros_like(rgb),rgb,rgba[...,3]/255))
    np.testing.assert_array_equal(rgb[0,0],[0,0,0])
    np.testing.assert_array_equal(rgb[0,-1],[230,246,255])
    for bad in ([0,10,200],[255,-1,0],[255,0],[255,float('nan'),0]):
        with pytest.raises(ValueError):color_settings({'color_map':'tint_white','color_rgb':bad})
    with pytest.raises(ValueError):render_layers(L,np.full_like(L,255),tint)


def test_saved_alpha_tem_replay_and_effective_config(tmp_path,monkeypatch):
    x=np.arange(64)[None,:]
    f=(np.cos(2*np.pi*x/8)*np.linspace(.1,5,64)[:,None]).astype(np.float32)
    source=tmp_path/'ifft.tif';tem_path=tmp_path/'tem.tif'
    tifffile.imwrite(source,f);tifffile.imwrite(tem_path,np.arange(4096,dtype=np.uint16).reshape(64,64))
    cfg={'sigma_px':5,'display_percentiles':[.5,99.5],'color_map':'tint_white','color_rgb':[255,140,0],
         'alpha':{'mode':'continuous','low':{'mode':'percentile','value':10},'full':{'mode':'max'}},'tem_window':[0,4095]}
    out=tmp_path/'run';m=run_pipeline(source,out,cfg,tem_path,make_figures=False)
    rgba=np.array(Image.open(out/'05_selected_green_transparent.png'))
    assert np.unique(rgba[...,3]).size>2
    aa=tifffile.imread(out/'05_alpha_float32.tif')
    np.testing.assert_array_equal(rgba[...,3],tifffile.imread(out/'05_alpha_uint8.tif'))
    assert np.all(aa[tifffile.imread(out/'04_selection_mask_uint8.tif')==0]==0)
    assert m['statistics']['alpha_endpoints']['mode']=='continuous'
    effective=json.loads((out/'effective_config.json').read_text())
    run_pipeline(source,tmp_path/'replay',effective,make_figures=False)
    np.testing.assert_array_equal(rgba,np.array(Image.open(tmp_path/'replay/05_selected_green_transparent.png')))
    saved=tmp_path/'on_tem'
    monkeypatch.setattr(sys,'argv',['overlay_saved_run.py','--run',str(out),'--tem',str(tem_path),
                       '--output',str(saved),'--tem-window','0','4095'])
    overlay_saved_run.main()
    np.testing.assert_array_equal(np.array(Image.open(saved/'green_on_TEM.png')),np.array(Image.open(out/'08_green_on_TEM.png')))


def test_gui_continuous_controls_save_same_pixels(tmp_path,monkeypatch):
    import matplotlib
    matplotlib.use('Agg')
    import review_mask
    source=tmp_path/'source.tif'
    f=(np.cos(np.arange(48)[None,:]*2*np.pi/8)*np.linspace(.1,5,48)[:,None]).astype(np.float32)
    tifffile.imwrite(source,f)
    cfg={'sigma_px':5,'color_map':'tint_white','color_rgb':[0,160,255],'display_percentiles':[.5,99.5],
         'alpha':{'mode':'continuous','low':{'mode':'percentile','value':10},'full':{'mode':'max'}}}
    c=tmp_path/'config.json';c.write_text(json.dumps(cfg));out=tmp_path/'out'
    monkeypatch.setattr(sys,'argv',['review_mask.py','--input',str(source),'--config',str(c),'--output',str(out)])
    sliders=[];buttons=[];real_slider=review_mask.Slider;real_button=review_mask.Button
    def capture_slider(*args,**kwargs):
        s=real_slider(*args,**kwargs);sliders.append(s);return s
    def capture_button(*args,**kwargs):
        b=real_button(*args,**kwargs);buttons.append(b);return b
    monkeypatch.setattr(review_mask,'Slider',capture_slider);monkeypatch.setattr(review_mask,'Button',capture_button)
    def inspect():
        assert len(sliders)==2
        sliders[1].set_val(sliders[1].val*.8)
        fig=review_mask.plt.gcf();preview=np.array(fig.axes[2].images[0].get_array())
        buttons[0]._observers.process('clicked',None)
        np.testing.assert_array_equal(preview,np.array(Image.open(out/'06_selected_on_black.png')))
        assert json.loads((out/'effective_config.json').read_text())['alpha']['full']['value']==sliders[1].val
        review_mask.plt.close(fig)
    monkeypatch.setattr(review_mask.plt,'show',inspect);review_mask.main()
