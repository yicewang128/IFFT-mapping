"""Reuse saved RGB and alpha8 on TEM, including legacy binary runs; never rethreshold."""
import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image
from pipeline import load_image, tem_display, composite, write_tiff, sha256, save_png


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run",required=True,help="Existing reviewed run folder")
    p.add_argument("--tem",required=True);p.add_argument("--output",required=True)
    p.add_argument("--opacity",type=float,default=1.0)
    p.add_argument("--tem-window",type=float,nargs=2)
    args=p.parse_args();source=Path(args.run);out=Path(args.output)
    if out.exists() and any(out.iterdir()):raise FileExistsError("Choose a new or empty output folder.")
    rgb,gm=load_image(source/"01_linear_green_rgb.tif")
    alpha_path=source/"05_alpha_uint8.tif"
    if not alpha_path.exists():alpha_path=source/"04_selection_mask_uint8.tif"
    alpha_pixels,mm=load_image(alpha_path)
    if alpha_pixels.dtype != np.uint8 or alpha_pixels.ndim != 2:raise ValueError("Expected uint8 alpha channel")
    alpha=alpha_pixels.astype(float)/255
    t,tm=load_image(args.tem)
    base,display=tem_display(t,args.tem_window)
    merged=composite(base,rgb,alpha,args.opacity)
    out.mkdir(parents=True,exist_ok=True)
    cal=gm.get("calibration",{})
    write_tiff(out/"TEM_display_reference_rgb.tif",base,cal)
    write_tiff(out/"green_on_TEM_rgb.tif",merged,cal)
    save_png(out/"green_on_TEM.png",merged)
    record={"method":"Composite saved RGB and alpha8/255; no selection recalculation",
            "green":gm,"alpha":mm,"TEM":tm,"TEM_display":display,"opacity":args.opacity,
            "code_sha256":sha256(__file__),
            "validation":{"TEM_input_unchanged":sha256(args.tem)==tm['sha256'],
                          "outside_mask_equals_TEM_display":bool(np.array_equal(merged[alpha==0],base[alpha==0]))},
            "output_sha256":{f.name:sha256(f) for f in out.iterdir() if f.is_file()}}
    if (source/"run_manifest.json").exists():record["source_run_manifest_sha256"]=sha256(source/"run_manifest.json")
    (out/"overlay_manifest.json").write_text(json.dumps(record,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps({"output":str(out.resolve()),"validation":record["validation"]},indent=2))


if __name__=="__main__":main()

