"""Interactive threshold review. Only the region mask changes; green mapping is fixed.

Run from the project folder: python src/review_mask.py
The Save button writes a new run and its absolute threshold to effective_config.json.
"""
import argparse
import json
from datetime import datetime
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, TextBox
from pipeline import (load_image, prepare_ifft_display, amplitude_map, choose_threshold,
                      render_layers, run_pipeline, display_title)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input");parser.add_argument("--config",default="configs/default.json")
    parser.add_argument("--tem");parser.add_argument("--output")
    args=parser.parse_args()
    if args.input is None:
        from tkinter import Tk, filedialog
        root=Tk();root.withdraw()
        args.input=filedialog.askopenfilename(title="Choose the original signed IFFT",filetypes=[("TIFF","*.tif *.tiff")])
        root.destroy()
        if not args.input:return
    cfg=json.loads(Path(args.config).read_text(encoding="utf-8"))
    a,meta=load_image(args.input)
    if a.ndim!=2:raise ValueError("Choose a single grayscale IFFT, not RGB.")
    linear,bounds,clipped=prepare_ifft_display(a,cfg)
    _,smooth=amplitude_map(a,cfg.get("sigma_px",5))
    initial=choose_threshold(smooth,cfg.get("threshold",{}))
    rgb,_,black=render_layers(linear,smooth>=initial,cfg)
    fig,axs=plt.subplots(1,3,figsize=(13,6))
    fig.subplots_adjust(bottom=.26,top=.84)
    axs[0].imshow(rgb,interpolation="nearest");axs[0].set_title(f"Step 1: {display_title(cfg)}\nWindow {bounds[0]:.2f} to {bounds[1]:.2f}; clipped {100*clipped:.2f}%")
    axs[1].imshow(smooth,cmap="magma",interpolation="nearest");axs[1].set_title("Gaussian(abs(IFFT))")
    result=axs[2].imshow(black,interpolation="nearest");axs[2].set_title("Selected signal on black")
    for ax in axs:ax.axis("off")
    fig.suptitle("Review a signal-selection mask, not a validated physical grain boundary\nUse the toolbar zoom to inspect lattice fringes.")
    threshold_ax=fig.add_axes([.15,.15,.64,.035])
    slider=Slider(threshold_ax,"Threshold",float(smooth.min()),float(smooth.max()),valinit=initial)
    box=TextBox(fig.add_axes([.82,.14,.14,.05]),"Exact T ",initial=f"{initial:.6f}")
    status=fig.text(.15,.09,"",fontsize=10)
    button=Button(fig.add_axes([.38,.015,.24,.05]),"Save new run")
    def update(value):
        mask=smooth>=value
        result.set_data(np.where(mask[...,None],rgb,0))
        status.set_text(f"T={value:.6f}; selected={mask.mean()*100:.2f}%; sigma={cfg.get('sigma_px',5):g} px")
        fig.canvas.draw_idle()
    def submit(value):
        try:
            t=float(value)
            if not smooth.min()<=t<=smooth.max():raise ValueError("outside slider range")
            slider.set_val(t)
        except ValueError:status.set_text("Enter a numeric threshold within the slider range.");fig.canvas.draw_idle()
    def save(event):
        cfg["threshold"]={"mode":"manual","value":float(slider.val)}
        out=Path(args.output) if args.output else Path("runs")/datetime.now().strftime("review_%Y%m%d_%H%M%S_%f")
        status.set_text("Saving native-resolution images...");fig.canvas.draw_idle();fig.canvas.flush_events()
        try:
            run_pipeline(args.input,out,cfg,args.tem)
            status.set_text(f"Saved: {out.resolve()}")
        except Exception as e:status.set_text(f"Not saved: {e}")
        fig.canvas.draw_idle()
    slider.on_changed(update);box.on_submit(submit);button.on_clicked(save)
    update(initial);plt.show()


if __name__=="__main__":main()
