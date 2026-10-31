"""Review continuous-alpha endpoints or a legacy binary threshold, with fixed RGB."""
import argparse
import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, TextBox
from pipeline import (load_image, prepare_ifft_display, amplitude_map, choose_alpha,
                      render_layers, run_pipeline, display_title)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input');parser.add_argument('--config',default='configs/default.json')
    parser.add_argument('--tem');parser.add_argument('--output')
    args=parser.parse_args()
    if args.input is None:
        from tkinter import Tk, filedialog
        root=Tk();root.withdraw()
        args.input=filedialog.askopenfilename(title='Choose the original signed IFFT',filetypes=[('TIFF','*.tif *.tiff')])
        root.destroy()
        if not args.input:return
    cfg=json.loads(Path(args.config).read_text(encoding='utf-8'))
    a,_=load_image(args.input)
    if a.ndim!=2:raise ValueError('Choose a single grayscale IFFT')
    linear,bounds,clipped=prepare_ifft_display(a,cfg)
    _,smooth=amplitude_map(a,cfg.get('sigma_px',5))
    alpha,spec=choose_alpha(smooth,cfg)
    continuous=spec['mode']=='continuous'
    rgb,_,black=render_layers(linear,alpha,cfg)
    fig,axs=plt.subplots(1,3,figsize=(13,6))
    fig.subplots_adjust(bottom=.32,top=.84)
    axs[0].imshow(rgb,interpolation='nearest');axs[0].set_title(f'Step 1: {display_title(cfg)}\nWindow {bounds[0]:.2f} to {bounds[1]:.2f}; clipped {100*clipped:.2f}%')
    axs[1].imshow(smooth,cmap='magma',interpolation='nearest');axs[1].set_title('Gaussian(abs(IFFT))')
    result=axs[2].imshow(black,interpolation='nearest');axs[2].set_title('Signal on black')
    for ax in axs:ax.axis('off')
    fig.suptitle('Review amplitude opacity; not a validated physical grain boundary\nUse toolbar zoom to inspect lattice fringes.')
    lo=spec['low'] if continuous else spec['threshold']
    limit=max(float(smooth.max()),spec.get('full',0),lo)*1.1
    slider=Slider(fig.add_axes([.15,.22,.58,.035]),'T_low' if continuous else 'Threshold',0,limit,valinit=lo)
    box=TextBox(fig.add_axes([.82,.21,.14,.05]),'Exact low ',initial=f'{lo:.8g}')
    full_slider=None;full_box=None
    if continuous:
        full_slider=Slider(fig.add_axes([.15,.15,.58,.035]),'T_full',0,limit,valinit=spec['full'])
        full_box=TextBox(fig.add_axes([.82,.14,.14,.05]),'Exact full ',initial=f'{spec["full"]:.8g}')
    status=fig.text(.15,.085,'',fontsize=9)
    button=Button(fig.add_axes([.38,.015,.24,.05]),'Save new run')

    def selected_config():
        selected=deepcopy(cfg)
        if continuous:
            selected['alpha']={'mode':'continuous','low':{'mode':'manual','value':float(slider.val)},
                               'full':{'mode':'manual','value':float(full_slider.val)}}
        else:
            selected['alpha']={'mode':'binary'}
            selected['threshold']={'mode':'manual','value':float(slider.val)}
        return selected

    def update(value):
        try:
            aa,ss=choose_alpha(smooth,selected_config())
            _,_,bb=render_layers(linear,aa,cfg)
            result.set_data(bb)
            detail=f'T_low={ss["low"]:.6f}; T_full={ss["full"]:.6f}' if continuous else f'T={ss["threshold"]:.6f}'
            status.set_text(f'{detail}; transparent={100*np.mean(aa==0):.2f}%; opaque={100*np.mean(aa==1):.2f}%')
        except ValueError as e:status.set_text(str(e))
        fig.canvas.draw_idle()

    def submit(value,target):
        try:
            v=float(value)
            if not np.isfinite(v) or not 0<=v<=limit:raise ValueError('outside slider range')
            target.set_val(v)
        except ValueError:status.set_text('Enter a finite number within the slider range.');fig.canvas.draw_idle()

    def save(event):
        out=Path(args.output) if args.output else Path('runs')/datetime.now().strftime('review_%Y%m%d_%H%M%S_%f')
        try:
            selected=selected_config();choose_alpha(smooth,selected)
            status.set_text('Saving native-resolution images...');fig.canvas.draw_idle();fig.canvas.flush_events()
            run_pipeline(args.input,out,selected,args.tem)
            status.set_text(f'Saved: {out.resolve()}')
        except Exception as e:status.set_text(f'Not saved: {e}')
        fig.canvas.draw_idle()
    slider.on_changed(update);box.on_submit(lambda v:submit(v,slider));button.on_clicked(save)
    if continuous:
        full_slider.on_changed(update);full_box.on_submit(lambda v:submit(v,full_slider))
    update(lo);plt.show()


if __name__=='__main__':main()
