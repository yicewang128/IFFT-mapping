"""Create labeled previews from a run_combined result without changing full images.

python src/preview_combined.py --run runs/current --output runs/current_previews
Optional --reference PATH compares another run_combined output at identical coordinates.
Optional repeated --crop X Y SIZE selects native-pixel square comparison panels.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pipeline import save_png


def font(size):
    for name in ('DejaVuSans.ttf','Arial.ttf','arial.ttf'):
        try:return ImageFont.truetype(name,size)
        except OSError:pass
    return ImageFont.load_default()


def make(run, output, reference=None, crops=None):
    run=Path(run);out=Path(output)
    if out.exists() and any(out.iterdir()):raise FileExistsError('Choose an empty preview directory')
    manifest=json.loads((run/'run_manifest.json').read_text())
    out.mkdir(parents=True,exist_ok=True)
    records=manifest['runs']
    legend=Image.new('RGB',(1200,340),(16,16,16));d=ImageDraw.Draw(legend)
    for i,r in enumerate(records):
        x=i*200;cfg=r['config'];color=np.array(cfg['color_rgb'])
        d.text((x+10,10),r['name'],font=font(21),fill='white')
        d.text((x+10,42),cfg.get('color_name','matrix green'),font=font(17),fill='white')
        d.text((x+10,70),str(cfg['color_rgb']),font=font(16),fill='white')
        for j,L in enumerate((1,.5,.25)):
            y=110+j*62;c=tuple(np.rint(color*L).astype(int))
            d.rectangle((x+10,y,x+190,y+38),fill=c)
            d.text((x+12,y+41),f'L={L:g}',font=font(13),fill='white')
    save_png(out/'palette_legend.png',np.array(legend))
    keys=['Sb_all','K3SbS3_Sb_all']
    current={key:np.array(Image.open(run/f'{key}_black.png').convert('RGB')) for key in keys}
    for key,a in current.items():
        save_png(out/f'{key}_preview.png',np.array(Image.fromarray(a).resize((1024,1024),Image.Resampling.BOX)))
    six=Image.new('RGB',(1536,1100),(16,16,16));d=ImageDraw.Draw(six)
    for i,r in enumerate(records):
        x=(i%3)*512;y=(i//3)*550;d.text((x+8,y+8),r['name'],font=font(22),fill='white')
        im=Image.open(run/f'{r["name"]}_black.png').convert('RGB').resize((512,512),Image.Resampling.BOX)
        six.paste(im,(x,y+38))
    save_png(out/'six_layers_preview.png',np.array(six))
    if reference is not None:
        ref=Path(reference)
        previous={key:np.array(Image.open(ref/f'{key}_black.png').convert('RGB')) for key in keys}
        if any(previous[k].shape!=current[k].shape for k in keys):raise ValueError('Reference dimensions differ')
        selections=[(None,'palette_comparison_fullfield.png')]
        for i,crop in enumerate(crops or []):selections.append((crop,f'palette_comparison_native_{i+1}.png'))
        for crop,filename in selections:
            side=512 if crop is None else int(crop[2]);board=Image.new('RGB',(2*side,2*(side+38)),(16,16,16));d=ImageDraw.Draw(board)
            for row,key in enumerate(keys):
                for col,(a,label) in enumerate([(previous[key],'Previous colors'),(current[key],'Updated colors')]):
                    im=Image.fromarray(a)
                    if crop is None:im=im.resize((side,side),Image.Resampling.BOX)
                    else:
                        x,y,size=map(int,crop)
                        if min(x,y)<0 or size<1 or x+size>im.width or y+size>im.height:raise ValueError('Crop outside image')
                        im=im.crop((x,y,x+size,y+size))
                    xx=col*side;yy=row*(side+38)
                    d.text((xx+8,yy+8),f'{label} | {key}',font=font(18),fill='white');board.paste(im,(xx,yy+38))
            save_png(out/filename,np.array(board))
    (out/'preview_record.json').write_text(json.dumps({'source_run':str(run.resolve()),'reference_run':str(Path(reference).resolve()) if reference else None,'native_crops_xy_size':crops or [],'fullfield_resampling':'BOX, previews only; full-resolution images untouched','source_version':manifest['version']},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',required=True);p.add_argument('--output',required=True)
    p.add_argument('--reference');p.add_argument('--crop',nargs=3,type=int,action='append')
    a=p.parse_args();make(a.run,a.output,a.reference,a.crop)
