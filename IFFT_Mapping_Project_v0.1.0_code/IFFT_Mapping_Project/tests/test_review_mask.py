"""Headless check that interactive display and saved images use the same LUT."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import matplotlib
matplotlib.use('Agg')
import numpy as np
import tifffile
from PIL import Image
import review_mask


def test_gui_preview_equals_saved_step1_and_mask(tmp_path, monkeypatch):
    a=(np.cos(np.arange(48)[None,:]*2*np.pi/8)*np.linspace(.1,5,48)[:,None]).astype(np.float32)
    source=tmp_path/'input.tif';tifffile.imwrite(source,a)
    cfg={"display_percentiles":[.5,99.5],"color_map":"green_white","white_start":.55,"white_max":230,"sigma_px":5}
    config=tmp_path/'config.json';config.write_text(json.dumps(cfg))
    out=tmp_path/'saved'
    monkeypatch.setattr(sys,'argv',['review_mask.py','--input',str(source),'--config',str(config),'--output',str(out)])
    real_button=review_mask.Button
    buttons=[]
    def capture_button(*args,**kwargs):
        b=real_button(*args,**kwargs);buttons.append(b);return b
    monkeypatch.setattr(review_mask,'Button',capture_button)
    def inspect_and_save():
        fig=review_mask.plt.gcf()
        preview=np.asarray(fig.axes[0].images[0].get_array()).copy()
        selected=np.asarray(fig.axes[2].images[0].get_array()).copy()
        buttons[0]._observers.process('clicked',None)
        np.testing.assert_array_equal(preview,np.array(Image.open(out/'01_linear_green.png')))
        np.testing.assert_array_equal(selected,np.array(Image.open(out/'06_selected_on_black.png')))
        assert 'near-white' in fig.axes[0].get_title()
        review_mask.plt.close(fig)
    monkeypatch.setattr(review_mask.plt,'show',inspect_and_save)
    review_mask.main()
