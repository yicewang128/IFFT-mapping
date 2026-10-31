"""Process separately supplied Sb reflection-family IFFTs without combining them.
python src/run_sb_batch.py --input-dir data/sb --output runs/sb_first_preview
Each family must match exactly one 'IFFT (hkl) Sb*.tif' file in input-dir.
"""
import argparse
import csv
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pipeline import load_image, run_pipeline, save_png, sha256

PLANES=('012','104','110','202','024')


def font(size):
    for name in ['DejaVuSans.ttf','Arial.ttf','arial.ttf']:
        try:return ImageFont.truetype(name,size)
        except OSError:pass
    return ImageFont.load_default()


def comparison_panel(left,right,plane,stats,native=False,color_name="configured color"):
    side=512 if native else 768
    panel=Image.new('RGB',(2*side+48,side+120),(20,22,27))
    d=ImageDraw.Draw(panel)
    d.text((16,12),f'Sb {{{plane}}} | {color_name} | '+('native-pixel center crop' if native else 'full field'),font=font(24),fill='white')
    d.text((16,47),'1. Signed IFFT color (no alpha)',font=font(20),fill='white')
    d.text((side+32,47),'2. Continuous alpha on black',font=font(20),fill='white')
    for i,arr in enumerate([left,right]):
        im=Image.fromarray(arr)
        if native:
            w,h=im.size;x=(w-side)//2;y=(h-side)//2;im=im.crop((x,y,x+side,y+side))
        else:im=im.resize((side,side),Image.Resampling.BOX)
        panel.paste(im,(16+i*(side+16),80))
    d.text((16,side+89),f'Sigma=5 px | T_low={stats["low"]:.4f} | T_full={stats["full"]:.4f} | scalar gamma=1',font=font(17),fill=(210,215,220))
    return np.array(panel)


def run_batch(input_dir,output_dir,config_dir=None):
    input_dir=Path(input_dir);out=Path(output_dir)
    if out.exists() and any(out.iterdir()):raise FileExistsError('Choose an empty output directory')
    config_dir=Path(config_dir) if config_dir else Path(__file__).resolve().parents[1]/'configs'
    # Validate all inputs and configurations before producing the first run.
    inputs={};shape=None;cal=None
    for hkl in PLANES:
        files=sorted(input_dir.glob(f'IFFT ({hkl}) Sb*.tif'))
        if len(files)!=1:raise ValueError(f'{hkl}: expected exactly one input, found {len(files)}')
        a,m=load_image(files[0])
        if a.ndim!=2 or not np.issubdtype(a.dtype,np.number) or np.iscomplexobj(a):raise ValueError(f'{hkl}: require real 2D signed IFFT')
        if shape is None:shape=a.shape;cal=m.get('calibration',{})
        if shape!=a.shape or cal!=m.get('calibration',{}):raise ValueError('Plane images differ in shape or pixel calibration')
        cfg=json.loads((config_dir/f'sb_{hkl}.json').read_text())
        inputs[hkl]=(files[0],cfg)
    out.mkdir(parents=True,exist_ok=True);previews=out/'previews';previews.mkdir()
    records=[];rows=[]
    for hkl in PLANES:
        source,cfg=inputs[hkl];dest=out/f'Sb_{hkl}'
        record=run_pipeline(source,dest,cfg,make_figures=False)
        record['reflection_family']=hkl
        rgb=np.array(Image.open(dest/'01_linear_green.png'))
        black=np.array(Image.open(dest/'06_selected_on_black.png'))
        rgba=np.array(Image.open(dest/'05_selected_green_transparent.png'))
        assert np.array_equal(rgb,rgba[...,:3])
        assert np.array_equal(black,np.rint(rgb*(rgba[...,3].astype(float)/255)[...,None]).astype(np.uint8))
        aa=record['statistics']['alpha_endpoints'];bounds=record['config_effective']['display_window']
        save_png(previews/f'Sb_{hkl}_step1_full.png',rgb)
        save_png(previews/f'Sb_{hkl}_mapping_black_full.png',black)
        save_png(previews/f'Sb_{hkl}_comparison_full.png',comparison_panel(rgb,black,hkl,aa,color_name=cfg.get("color_name",hkl)))
        save_png(previews/f'Sb_{hkl}_comparison_native.png',comparison_panel(rgb,black,hkl,aa,True,color_name=cfg.get("color_name",hkl)))
        rows.append({'plane':hkl,'color':cfg.get('color_name',hkl),'color_rgb':str(cfg['color_rgb']),
            'display_low':bounds[0],'display_high':bounds[1],'T_low':aa['low'],'T_full':aa['full'],
            'mean_alpha':record['statistics']['mean_alpha'],'zero_fraction_float':record['statistics']['transparent_fraction_float'],
            'zero_fraction_PNG8':record['statistics']['transparent_fraction_PNG8'],
            'source_min':record['statistics']['min'],'source_max':record['statistics']['max'],
            'input_sha256':record['input']['sha256']})
        records.append(record)
        print(json.dumps(rows[-1]),flush=True)
    with open(out/'Sb_parameters.csv','w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    summary={'pipeline_version':records[0]['project_version'],'planes':list(PLANES),
        'status':'Separate-family rendering with configurable endpoints; confirmed thresholds and v0.4.0 colors.',
        'input_correspondence':'Supplied filenames; matching dimensions/calibration do not prove alignment or phase specificity.',
        'display':'Per-image P0.5/P99.5 of signed IFFT; scalar gamma=1; configured tint LUT; defaults to fixed hue (white_max=0)',
        'alpha':'Gaussian(abs(real signed IFFT)), sigma5; configured endpoints; each Sb preset defaults to its own P25 to P99.5; continuous linear ramp',
        'comparability':'Separate display and alpha normalizations: cross-plane brightness is not absolute diffraction intensity or phase fraction',
        'signal_note':'No RMS, correlation, Otsu, morphology, spatial filtering of displayed fringes, resizing of standalone images, or registration.',
        'code_sha256':sha256(__file__),'plane_parameters':rows,'runs':records}
    (out/'Sb_batch_record.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input-dir',required=True);p.add_argument('--output',required=True);p.add_argument('--config-dir')
    args=p.parse_args();run_batch(args.input_dir,args.output,args.config_dir)


if __name__=='__main__':main()
