"""Render six corresponding IFFTs; group Sb and place it above the matrix.

No registration is performed; input coordinates must already correspond.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import tifffile
from PIL import Image
from pipeline import (VERSION, load_image, prepare_ifft_display, amplitude_map, choose_alpha,
                      render_layers, save_png, sha256, write_tiff)
from compositing import group_rgba, source_over_rgba, on_black


def add_layers(layers):
    """Sum premultiplied RGB in float64; clip and round only once at the end."""
    total = None
    for rgba in layers:
        if rgba.dtype != np.uint8 or rgba.ndim != 3 or rgba.shape[-1] != 4:
            raise ValueError('Expected RGBA uint8 layers')
        value = rgba[..., :3].astype(float) * (rgba[..., 3:4].astype(float)/255)
        if total is None:
            total = np.zeros_like(value)
        if total.shape != value.shape:
            raise ValueError('Layer dimensions differ; no automatic registration')
        total += value
    if total is None:
        raise ValueError('At least one layer required')
    clipped_fraction = float(np.mean(np.any(total > 255, axis=-1)))
    return np.rint(np.clip(total, 0, 255)).astype(np.uint8), clipped_fraction


def run(k3, sb_dir, output, config_dir=None, compositing='sb-over-matrix'):
    if compositing not in ('sb-over-matrix', 'additive'):
        raise ValueError('Choose sb-over-matrix or additive compositing')
    out = Path(output)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError('Choose a new or empty output directory')
    configs = Path(config_dir) if config_dir else Path(__file__).resolve().parents[1]/'configs'
    sources = [('K3SbS3', Path(k3), configs/'default.json')]
    for h in ('012','104','110','202','024'):
        files = sorted(Path(sb_dir).glob(f'IFFT ({h}) Sb*.tif'))
        if len(files) != 1:
            raise ValueError(f'{h}: expected exactly one IFFT')
        sources.append((f'Sb_{h}', files[0], configs/f'sb_{h}.json'))
    loaded=[]
    for name, path, cp in sources:
        a, meta = load_image(path)
        if a.ndim != 2 or np.iscomplexobj(a):
            raise ValueError('Real 2D IFFT required')
        if loaded and (a.shape != loaded[0][1].shape or meta.get('calibration') != loaded[0][2].get('calibration')):
            raise ValueError('Input shape/calibration mismatch')
        loaded.append((name,a,meta,json.loads(cp.read_text()),path))
    out.mkdir(parents=True,exist_ok=True)
    records=[]; layers=[]
    for name,a,meta,cfg,path in loaded:
        L,bounds,clipped=prepare_ifft_display(a,cfg)
        _,S=amplitude_map(a,cfg['sigma_px'])
        alpha,endpoints=choose_alpha(S,cfg)
        rgb,rgba,black=render_layers(L,alpha,cfg)
        for suffix,pixels in [('step1',rgb),('transparent',rgba),('black',black)]:
            dest=out/f'{name}_{suffix}.png';save_png(dest,pixels)
            with Image.open(dest) as im:
                if not np.array_equal(np.array(im),pixels):raise RuntimeError('PNG verification failed')
        write_tiff(out/f'{name}_alpha_float32.tif',alpha.astype(np.float32),meta.get('calibration'))
        write_tiff(out/f'{name}_black.tif',black,loaded[0][2].get('calibration'))
        if sha256(path)!=meta['sha256']:raise RuntimeError('Source changed')
        effective=dict(cfg,display_window=bounds)
        records.append(dict(name=name,input=meta,config=effective,alpha=endpoints,
            smooth_min=float(S.min()),mean_alpha=float(alpha.mean()),
            display_clipped_fraction=clipped,alpha_zero_fraction=float(np.mean(alpha==0)),
            alpha8_zero_fraction=float(np.mean(rgba[...,3]==0))))
        layers.append(rgba)
        print(name,endpoints,flush=True)
    overlays={}
    if compositing == 'sb-over-matrix':
        sb_group=group_rgba(layers[1:])
        merged=source_over_rgba(sb_group,layers[0])
        composites=[('Sb_all',on_black(sb_group),sb_group,None),
                    ('K3SbS3_Sb_all',on_black(merged),merged,None)]
    else:
        composites=[]
        for name,selected in [('Sb_all',layers[1:]),('K3SbS3_Sb_all',layers)]:
            black,clipped=add_layers(selected)
            composites.append((name,black,None,clipped))
    for name,black,rgba,clipped in composites:
        save_png(out/f'{name}_black.png',black)
        write_tiff(out/f'{name}_black.tif',black,loaded[0][2].get('calibration'))
        if rgba is not None:
            save_png(out/f'{name}_transparent.png',rgba)
        overlays[name]={'clipped_pixel_fraction':clipped,
                        'transparent_png':rgba is not None}
    manifest=dict(version=VERSION,runs=records,overlays=overlays,
        compositing=compositing,
        compositing_rules=({'Sb_color':'sum(alpha_i*RGB_i)/sum(alpha_i); zero at zero total weight',
                            'Sb_alpha':'1-product(1-alpha_i)',
                            'layer_order_bottom_to_top':['black','K3SbS3','Sb_group'],
                            'outer_rule':'ordinary source-over, straight RGBA8 export; black uses exported alpha8',
                            'numeric_domain':'encoded RGB8 channels, float64 arithmetic; no linear-light conversion'}
                           if compositing=='sb-over-matrix' else
                           {'rule':'round(clip(sum(alpha8/255 * RGB),0,255)); only final rounding'}),
        source_code_sha256=sha256(__file__),
        processing_code_sha256={name:sha256(Path(__file__).with_name(name)) for name in ['pipeline.py','compositing.py']},
        caveats=['No registration; shape/calibration checks do not prove alignment.',
                 'Mixed or white colors indicate overlapping display layers, not a new phase.',
                 'Independent per-image normalization is not an absolute intensity comparison.',
                 'K3 low=0 preserves positive background amplitude; Sb percentile thresholds are display choices, not verified boundaries.',
                 'Display layering does not establish physical depth or absence of the covered matrix.'])
    (out/'run_manifest.json').write_text(json.dumps(manifest,indent=2))
    return manifest


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--k3',required=True);p.add_argument('--sb-dir',required=True)
    p.add_argument('--output',required=True);p.add_argument('--config-dir')
    p.add_argument('--compositing',choices=['sb-over-matrix','additive'],default='sb-over-matrix')
    a=p.parse_args();run(a.k3,a.sb_dir,a.output,a.config_dir,a.compositing)
