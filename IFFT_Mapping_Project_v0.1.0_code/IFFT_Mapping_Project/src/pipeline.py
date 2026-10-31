"""Version 0.3.0: signed IFFT colors and independent continuous amplitude alpha.

No RMS, gamma adjustment, sharpening, morphology, resizing, or registration.
See docs/METHODS_zh.md for the meaning and limitations of each operation.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import importlib.metadata
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import tifffile
from PIL import Image
from scipy.ndimage import gaussian_filter

VERSION = "0.3.0"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_image(path):
    """Read single-frame TIFF/PNG without display rescaling; Pillow decodes LZW."""
    path = Path(path)
    meta = {"filename": path.name, "sha256": sha256(path)}
    with Image.open(path) as im:
        if getattr(im, "n_frames", 1) != 1:
            raise ValueError("Only single-frame images are supported. Select one frame explicitly.")
        a = np.array(im)
        meta["pillow_mode"] = im.mode
    if path.suffix.lower() in (".tif", ".tiff"):
        with tifffile.TiffFile(path) as tf:
            page = tf.pages[0]
            tags = page.tags
            ij = tf.imagej_metadata or {}
            cal = {}
            # Gatan TIFF tags carry physical sampling, distinct from 72-dpi printing tags.
            if 65009 in tags and 65010 in tags:
                cal = {"pixel_width": float(tags[65009].value),
                       "pixel_height": float(tags[65010].value),
                       "unit": str(tags[65003].value) if 65003 in tags else "unknown",
                       "source": "Gatan TIFF private calibration tags"}
            elif ij.get("unit") and "XResolution" in tags and "YResolution" in tags:
                xr, yr = tags["XResolution"].value, tags["YResolution"].value
                cal = {"pixel_width": xr[1] / xr[0], "pixel_height": yr[1] / yr[0],
                       "unit": ij["unit"], "source": "ImageJ TIFF calibration"}
            meta["calibration"] = cal
            meta["source_compression"] = str(page.compression.name)
    meta.update(shape=list(a.shape), dtype=str(a.dtype))
    if not np.isfinite(a).all():
        raise ValueError("NaN/Inf found. Resolve invalid pixels explicitly before processing.")
    return a, meta


def linear_signed_display(a, bounds=None):
    """Affine map, preserving signed ordering; default uses every input value."""
    a = np.asarray(a, dtype=np.float64)
    lo, hi = (float(a.min()), float(a.max())) if bounds is None else map(float, bounds)
    if not np.isfinite([lo, hi]).all() or hi <= lo:
        raise ValueError("Display maximum must exceed minimum; constant images are unsupported.")
    clipped = float(np.mean((a < lo) | (a > hi)))
    return np.clip((a - lo) / (hi - lo), 0, 1), [lo, hi], clipped


def prepare_ifft_display(a, cfg):
    """Choose one global IFFT window; explicit bounds take precedence over percentiles.

    Scalar gamma is fixed at 1. This does not affect TEM display or the mask.
    Absent percentile settings preserve the v0.1.0 full-range behavior.
    """
    bounds = cfg.get("display_window")
    percentiles = cfg.get("display_percentiles")
    if bounds is None and percentiles is not None:
        q = np.asarray(percentiles, dtype=np.float64)
        if q.shape != (2,) or not np.isfinite(q).all() or not 0 <= q[0] < q[1] <= 100:
            raise ValueError("display_percentiles must contain two increasing values in [0,100].")
        bounds = np.percentile(np.asarray(a, dtype=np.float64), q).tolist()
    return linear_signed_display(a, bounds)


def color_settings(cfg=None):
    """Validate and resolve the display LUT; no spatial filtering is performed."""
    cfg = cfg or {}
    mode = cfg.get("color_map", "green")
    if mode not in ("green", "green_white", "tint_white"):
        raise ValueError("color_map must be green, green_white, or tint_white")
    settings = {"color_map": mode, "scalar_gamma": 1}
    if mode in ("green_white", "tint_white"):
        start = float(cfg.get("white_start", 0.55))
        maximum = float(cfg.get("white_max", 230))
        if not np.isfinite([start, maximum]).all() or not 0 <= start < 1 or not 0 <= maximum <= 255:
            raise ValueError("white_start must be in [0,1); white_max must be in [0,255].")
        settings.update(white_start=start, white_max=maximum)
    if mode == "tint_white":
        color = np.asarray(cfg.get("color_rgb"), dtype=float)
        if color.shape != (3,) or not np.isfinite(color).all() or np.any(color < 0) or np.any(color > 255) or color.max() != 255:
            raise ValueError("color_rgb requires 3 finite values in [0,255], with maximum 255")
        settings["color_rgb"] = color.tolist()
    return settings


def display_title(cfg=None):
    mode = color_settings(cfg)["color_map"]
    if mode == "tint_white":
        return "Tint to near-white LUT"
    return "Green to near-white LUT" if mode == "green_white" else "Green LUT"


def amplitude_map(a, sigma=5.0):
    """G_sigma * abs(original signed IFFT), NOT RMS and NOT abs(normalized green)."""
    if not np.isfinite(sigma) or sigma <= 0:
        raise ValueError("sigma_px must be positive and finite.")
    absolute = np.abs(np.asarray(a, dtype=np.float64))
    smooth = gaussian_filter(absolute, sigma=float(sigma), mode="reflect", truncate=4.0)
    return absolute, smooth


def otsu_threshold(a, bins=4096):
    """Histogram Otsu: exploratory threshold, not a statistical boundary confidence."""
    lo, hi = float(a.min()), float(a.max())
    if hi <= lo:
        raise ValueError("Constant amplitude map: a two-class threshold is undefined.")
    hist, edges = np.histogram(a, bins=int(bins), range=(lo, hi))
    c = (edges[:-1] + edges[1:]) * 0.5
    w = np.cumsum(hist).astype(float)
    s = np.cumsum(hist * c)
    denom = w[:-1] * (w[-1] - w[:-1])
    score = np.full(len(denom), -np.inf)
    ok = denom > 0
    score[ok] = (s[-1] * w[:-1][ok] - s[:-1][ok] * w[-1]) ** 2 / denom[ok]
    return float(edges[int(np.argmax(score)) + 1])


def choose_threshold(smooth, cfg):
    mode = cfg.get("mode", "otsu")
    if mode == "otsu":
        return otsu_threshold(smooth, cfg.get("bins", 4096))
    if mode == "manual":
        t = float(cfg["value"])
    elif mode == "percentile":
        q = float(cfg["value"])
        if not 0 <= q <= 100:
            raise ValueError("Percentile must be between 0 and 100.")
        t = float(np.percentile(smooth, q))
    else:
        raise ValueError("threshold.mode must be otsu, manual, or percentile")
    if not np.isfinite(t):
        raise ValueError("Threshold must be finite.")
    return t


def resolve_alpha_endpoint(smooth, endpoint, allow_max=False):
    mode = endpoint.get("mode")
    if mode == "max" and allow_max:
        return float(np.max(smooth))
    if mode == "percentile":
        q = float(endpoint["value"])
        if not np.isfinite(q) or not 0 <= q <= 100:
            raise ValueError("Alpha percentile must lie in [0,100]")
        return float(np.percentile(smooth, q))
    if mode == "manual":
        value = float(endpoint["value"])
        if np.isfinite(value) and value >= 0:
            return value
    raise ValueError("Invalid alpha endpoint; use percentile/manual, or max for full")


def choose_alpha(smooth, cfg):
    """Return unquantized opacity and effective endpoints. Missing alpha keeps legacy behavior."""
    smooth = np.asarray(smooth, dtype=np.float64)
    if not np.isfinite(smooth).all() or np.any(smooth < 0):
        raise ValueError("Amplitude must be finite and nonnegative")
    spec = cfg.get("alpha", {"mode": "binary"})
    mode = spec.get("mode", "continuous")
    if mode == "binary":
        t = choose_threshold(smooth, cfg.get("threshold", {}))
        return (smooth >= t).astype(float), {"mode": "binary", "threshold": t}
    if mode != "continuous":
        raise ValueError("alpha.mode must be continuous or binary")
    low = resolve_alpha_endpoint(smooth, spec.get("low", {"mode":"percentile", "value":10}))
    full = resolve_alpha_endpoint(smooth, spec.get("full", {"mode":"max"}), allow_max=True)
    if full <= low:
        raise ValueError("T_full must exceed T_low; check constant images or endpoint choices")
    return np.clip((smooth-low)/(full-low), 0, 1), {"mode":"continuous", "low":low, "full":full}


def effective_alpha_config(spec):
    if spec["mode"] == "binary":
        return {"mode":"binary"}
    return {"mode":"continuous", "low":{"mode":"manual", "value":spec["low"]},
            "full":{"mode":"manual", "value":spec["full"]}}


def validate_alpha(alpha, shape):
    alpha = np.asarray(alpha, dtype=np.float64)
    if alpha.shape != shape or not np.isfinite(alpha).all() or np.any(alpha < 0) or np.any(alpha > 1):
        raise ValueError("Alpha must match image dimensions and contain finite values in [0,1]")
    return alpha


def save_png(path, pixels):
    """Encode completely before writing; avoid partially encoded exported PNGs."""
    data = io.BytesIO()
    Image.fromarray(pixels).save(data, format="PNG")
    Path(path).write_bytes(data.getvalue())


def render_layers(linear, alpha, cfg=None):
    """RGB is independent of opacity; black output uses the exact exported PNG alpha8."""
    alpha = validate_alpha(alpha, linear.shape)
    rgb = np.zeros((*linear.shape, 3), dtype=np.uint8)
    rgb[..., 1] = np.rint(255 * linear).astype(np.uint8)
    settings = color_settings(cfg)
    if settings["color_map"] == "green_white":
        start = settings["white_start"]
        highlight = np.clip((linear - start) / (1 - start), 0, 1)
        rb = np.rint(settings["white_max"] * highlight).astype(np.uint8)
        rgb[..., 0] = rb
        rgb[..., 2] = rb
    elif settings["color_map"] == "tint_white":
        base = np.asarray(settings["color_rgb"], dtype=float)/255
        white = settings["white_max"] * np.clip((linear-settings["white_start"])/(1-settings["white_start"]), 0, 1)
        rgb = np.rint(255*linear[...,None]*base + white[...,None]*(1-base)).astype(np.uint8)
    alpha8 = np.rint(255*alpha).astype(np.uint8)
    rgba = np.dstack((rgb, alpha8))
    black = np.rint(rgb*(alpha8.astype(float)/255)[...,None]).astype(np.uint8)
    return rgb, rgba, black


def composite(base_rgb, foreground_rgb, mask, opacity=1.0):
    if base_rgb.shape != foreground_rgb.shape:
        raise ValueError("TEM/IFFT dimensions differ: no automatic registration or resizing is performed.")
    if not np.isfinite(opacity) or not 0 <= opacity <= 1:
        raise ValueError("opacity must be between 0 and 1")
    alpha = validate_alpha(mask, base_rgb.shape[:2])[..., None] * opacity
    return np.rint(alpha * foreground_rgb + (1 - alpha) * base_rgb).astype(np.uint8)


def tem_display(a, window=None):
    """Display only: never rewrite raw TEM. Float/16-bit TEM needs an explicit window."""
    if a.dtype == np.uint8 and a.ndim == 3 and a.shape[-1] == 3:
        return a.copy(), {"mode": "native uint8 RGB"}
    if a.dtype == np.uint8 and a.ndim == 2 and window is None:
        return np.repeat(a[..., None], 3, axis=-1), {"mode": "native uint8 gray"}
    if a.ndim != 2:
        raise ValueError("TEM must be 2D grayscale or uint8 RGB, without an alpha channel.")
    if window is None:
        raise ValueError("For float/16-bit TEM, specify tem_window=[display_min,display_max] from DM/ImageJ.")
    linear, bounds, clipped = linear_signed_display(a, window)
    g = np.rint(255 * linear).astype(np.uint8)
    return np.repeat(g[..., None], 3, axis=-1), {"mode": "explicit linear display window", "window": bounds, "clipped_fraction": clipped}


def write_tiff(path, a, calibration=None):
    """Uncompressed TIFF, native sampling; ImageJ calibration plus Gatan scale tags."""
    cal = calibration or {}
    kw = {"compression": None, "metadata": {"axes": "YX" if a.ndim == 2 else "YXS"}}
    if cal:
        px, py, unit = cal["pixel_width"], cal["pixel_height"], cal["unit"]
        kw.update(resolution=(1 / px, 1 / py), resolutionunit="NONE")
        kw["metadata"]["unit"] = unit
        kw["extratags"] = [(65003, "s", 0, unit, False), (65004, "s", 0, unit, False),
                           (65009, "d", 1, px, False), (65010, "d", 1, py, False)]
    if a.ndim == 2 or a.shape[-1] == 3:
        kw["imagej"] = True
    if a.ndim == 3:
        kw["photometric"] = "rgb"
    if a.ndim == 3 and a.shape[-1] == 4:
        kw["extrasamples"] = "unassalpha"
    tifffile.imwrite(path, a, **kw)


def make_preview(out, raw, linear, smooth, alpha, rgb, rgba, black, threshold, sigma, cfg=None):
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    yy, xx = np.indices(raw.shape)
    checker = np.where(((xx // 64 + yy // 64) % 2)[..., None], 65, 105)
    checker = np.repeat(checker, 3, axis=-1).astype(np.uint8)
    transparent_view = composite(checker, rgb, rgba[...,3].astype(float)/255)
    fig = Figure(figsize=(12, 8.7), dpi=160); FigureCanvasAgg(fig)
    axs = fig.subplots(2, 3)
    items = [(raw, "Original signed IFFT", "gray"), (rgb, f"1. {display_title(cfg)} / scalar gamma = 1", None),
             (smooth, f"2. Gaussian(abs(IFFT)), sigma = {sigma:g} px", "magma"),
             (alpha, "3. Alpha: 0 transparent, 1 opaque", "gray"),
             (transparent_view, "4. Selected green / checkerboard preview", None),
             (black, "5. Selected green on black", None)]
    for ax, (im, title, cmap) in zip(axs.flat, items):
        options = {"vmin":0, "vmax":1} if im is alpha else {}
        ax.imshow(im, cmap=cmap, interpolation="nearest", **options)
        ax.set_title(title, fontsize=10); ax.axis("off")
    fig.suptitle("Exploratory lattice-signal selection; not a validated grain-boundary map", fontsize=12)
    fig.tight_layout(); fig.savefig(out / "overview.png")
    # Native-pixel crops: preview downsampling can hide genuine lattice fringes.
    h, w = raw.shape; cy, cx = h // 2, w // 2
    y0, x0 = max(0, cy-256), max(0, cx-256)
    sl = np.s_[y0:min(h,y0+512), x0:min(w,x0+512)]
    gray = np.repeat(np.rint(255 * linear[sl]).astype(np.uint8)[...,None],3,axis=-1)
    save_png(out / "native_crop_gray_green_selected.png", np.concatenate([gray, rgb[sl], black[sl]], axis=1))
    if (cfg or {}).get("alpha", {}).get("mode", "binary") != "binary":
        return
    # Threshold sensitivity: ±20% are exploratory settings, NOT confidence bounds.
    fig = Figure(figsize=(12, 4.5), dpi=160); FigureCanvasAgg(fig)
    axs = fig.subplots(1, 3)
    for ax, f in zip(axs, (0.8,1.0,1.2)):
        m = smooth >= threshold*f
        ax.imshow(np.where(m[...,None], rgb,0), interpolation="nearest")
        ax.set_title(f"T x {f:.1f}: {100*m.mean():.1f}% selected", fontsize=10);ax.axis("off")
    fig.suptitle("Threshold sensitivity only; no change to the green intensity mapping")
    fig.tight_layout();fig.savefig(out / "threshold_sensitivity.png")


def run_pipeline(input_path, output_dir, cfg, tem_path=None, make_figures=True):
    output_dir = Path(output_dir)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError("Output folder is not empty. Choose a new folder to preserve earlier runs.")
    a, meta = load_image(input_path)
    if a.ndim != 2 or not np.issubdtype(a.dtype, np.number) or np.iscomplexobj(a):
        raise ValueError("Input must be a single real-valued 2D grayscale IFFT, not RGB or complex data.")
    linear, bounds, clipped = prepare_ifft_display(a, cfg)
    colors = color_settings(cfg)
    absolute, smooth = amplitude_map(a, cfg.get("sigma_px", 5))
    alpha, alpha_spec = choose_alpha(smooth, cfg)
    threshold = alpha_spec.get("threshold", alpha_spec.get("low"))
    mask = alpha > 0
    rgb, rgba, black = render_layers(linear, alpha, cfg)
    alpha_png = rgba[...,3].astype(float)/255
    # Validate TEM before writing so invalid input does not create a partial run.
    tem_data = None
    if tem_path:
        t, tm = load_image(tem_path)
        if t.shape[:2] != a.shape:
            raise ValueError("TEM/IFFT dimensions differ. Supply an already aligned TEM.")
        base, disp = tem_display(t, cfg.get("tem_window"))
        tem_data = (base, tm, disp, composite(base, rgb, alpha_png, cfg.get("tem_opacity", 1.0)))
    output_dir.mkdir(parents=True, exist_ok=True)
    cal = meta.get("calibration", {})
    arrays = {
        "00_signed_ifft_float32.tif": a.astype(np.float32),
        "01_linear_green_channel_float32.tif": linear.astype(np.float32),
        "01_linear_green_rgb.tif": rgb,
        "02_abs_ifft_float32.tif": absolute.astype(np.float32),
        "03_abs_gaussian_float32.tif": smooth.astype(np.float32),
        "04_selection_mask_uint8.tif": mask.astype(np.uint8)*255,
        "05_alpha_uint8.tif": rgba[...,3],
        "05_alpha_float32.tif": alpha.astype(np.float32),
        "06_selected_on_black_rgb.tif": black,
    }
    # Keep the floating-point field at its original dtype, even for future float64 inputs.
    if a.dtype != np.float32:
        arrays.pop("00_signed_ifft_float32.tif")
        np.save(output_dir / "00_signed_ifft_original_dtype.npy", a)
    for name, arr in arrays.items():
        write_tiff(output_dir / name, arr, cal)
    save_png(output_dir / "01_linear_green.png", rgb)
    save_png(output_dir / "05_selected_green_transparent.png", rgba)
    save_png(output_dir / "06_selected_on_black.png", black)
    if tem_data:
        base, tm, disp, merged = tem_data
        write_tiff(output_dir / "07_TEM_display_reference_rgb.tif", base, cal)
        write_tiff(output_dir / "08_green_on_TEM_rgb.tif", merged, cal)
        save_png(output_dir / "08_green_on_TEM.png", merged)
    effective = dict(cfg)
    effective.update({k: v for k, v in colors.items() if k != "scalar_gamma"})
    effective.update(display_window=bounds, alpha=effective_alpha_config(alpha_spec))
    if alpha_spec["mode"] == "binary":
        effective["threshold"] = {"mode":"manual", "value":threshold}
    else:
        effective.pop("threshold", None)
    (output_dir / "effective_config.json").write_text(json.dumps(effective, indent=2),encoding="utf-8")
    validation = {
        "source_file_unchanged": sha256(input_path) == meta["sha256"],
        "signed_display_clipped_fraction": clipped,
        "signed_display_clipped_low_fraction": float(np.mean(a < bounds[0])),
        "signed_display_clipped_high_fraction": float(np.mean(a > bounds[1])),
        "selected_display_clipped_fraction": float(np.mean((a[mask] < bounds[0]) | (a[mask] > bounds[1]))) if mask.any() else None,
        "selected_RGB_equals_step1": bool(np.array_equal(rgba[mask,:3], rgb[mask])),
        "alpha_is_binary": bool(np.all(np.isin(rgba[...,3], [0,255]))),
        "alpha_range_valid": bool(np.isfinite(alpha).all() and alpha.min() >= 0 and alpha.max() <= 1),
        "all_hidden_RGB_equals_step1": bool(np.array_equal(rgba[...,:3],rgb)),
        "black_uses_exact_PNG_alpha": bool(np.array_equal(black, composite(np.zeros_like(rgb),rgb,alpha_png))),
        "outside_alpha_is_zero": bool(np.all(rgba[~mask,3] == 0)),
        "black_background_is_zero": bool(np.all(black[~mask] == 0)),
        "gaussian_preserves_nonnegative_values": bool(smooth.min() >= 0),
    }
    if tem_data:
        validation["TEM_source_file_unchanged"] = sha256(tem_path) == tm["sha256"]
        validation["outside_mask_TEM_display_unchanged"] = bool(np.array_equal(merged[alpha_png==0],base[alpha_png==0]))
    manifest = {
        "project_version": VERSION, "created_utc": datetime.now(timezone.utc).isoformat(),
        "input": meta, "config_requested": cfg, "config_effective": effective,
        "statistics": {"min": float(a.min()), "max": float(a.max()), "mean": float(np.mean(a,dtype=np.float64)),
                       "negative_fraction": float(np.mean(a<0)), "zero_green_level_0_255": float(np.clip(-bounds[0]/(bounds[1]-bounds[0]),0,1)*255),
                       "threshold": threshold, "selected_fraction": float(mask.mean()),
                       "alpha_endpoints": alpha_spec,
                       "transparent_fraction_float": float(np.mean(alpha==0)),
                       "opaque_fraction_float": float(np.mean(alpha==1)),
                       "transparent_fraction_PNG8": float(np.mean(rgba[...,3]==0)),
                       "opaque_fraction_PNG8": float(np.mean(rgba[...,3]==255)),
                       "mean_alpha": float(alpha.mean()),
                       "sigma_physical_xy": [cfg.get("sigma_px",5)*cal[k] for k in ("pixel_width","pixel_height")] if cal else None},
        "algorithm": {"mapping": "gaussian_filter(abs(original_IFFT))", "sigma_unit": "pixels",
                      "gaussian_mode": "reflect", "gaussian_truncate": 4.0,
                      "gamma": 1, "RMS": False, "morphology": False, "registration": False,
                      "alpha": "clip((S-T_low)/(T_full-T_low),0,1)" if alpha_spec["mode"] == "continuous" else "binary: S>=T",
                      "alpha_gamma": 1, "alpha_endpoints": alpha_spec,
                      "alpha_export": "float32 TIFF reference; PNG alpha8=round(255*alpha); composites use alpha8/255",
                      "support_mask": "alpha_float>0; auxiliary only, not a replacement for continuous alpha",
                      "display": {**colors,
                                  "window": bounds,
                                  "window_source": "explicit" if cfg.get("display_window") is not None else ("global percentiles" if cfg.get("display_percentiles") is not None else "full min/max"),
                                  "scalar_formula": "L=clip((F-low)/(high-low),0,1)",
                                  "lut_formula": "RGB=round(255*L*b+white_max*clip((L-white_start)/(1-white_start),0,1)*(1-b)); b=color_rgb/255" if colors["color_map"] == "tint_white" else ("G=round(255*L); R=B=round(white_max*clip((L-white_start)/(1-white_start),0,1))" if colors["color_map"] == "green_white" else "G=round(255*L); R=B=0"),
                                  "high_endpoint_rgb": render_layers(np.ones((1,1)),np.ones((1,1)),cfg)[0][0,0].tolist(),
                                  "intensity_note": "Window clipping, piecewise color LUT and RGB8 quantization affect rendered intensities; measure original signed IFFT."},
                      "numeric_precision": "float64 calculation, float32 intermediate TIFF exports",
                      "status": "exploratory lattice-signal selection, not a validated grain boundary"},
        "validation": validation,
        "environment": {"python": platform.python_version(), **{n:importlib.metadata.version(n) for n in ("numpy","scipy","Pillow","tifffile","matplotlib")}},
        "code_sha256": {p.name:sha256(p) for p in sorted(Path(__file__).parent.glob("*.py"))},
        "TEM": None if tem_data is None else {"input":tm,"display":disp,"opacity":cfg.get("tem_opacity",1.0)},
    }
    if make_figures:
        make_preview(output_dir,a,linear,smooth,alpha,rgb,rgba,black,threshold,cfg.get("sigma_px",5),cfg)
    manifest["output_sha256"] = {p.name:sha256(p) for p in sorted(output_dir.iterdir()) if p.is_file()}
    (output_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2,ensure_ascii=False),encoding="utf-8")
    return manifest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",required=True);p.add_argument("--output",required=True)
    p.add_argument("--config",default="configs/default.json");p.add_argument("--tem")
    p.add_argument("--threshold",type=float,help="Override with an absolute threshold in raw IFFT units")
    p.add_argument("--alpha-low-percentile",type=float)
    full_group=p.add_mutually_exclusive_group()
    full_group.add_argument("--alpha-full-percentile",type=float)
    full_group.add_argument("--alpha-full-value",type=float)
    full_group.add_argument("--alpha-full-max",action="store_true")
    p.add_argument("--sigma",type=float,help="Override Gaussian sigma in native pixels")
    p.add_argument("--tem-opacity",type=float)
    p.add_argument("--tem-window",type=float,nargs=2,metavar=("MIN","MAX"))
    args=p.parse_args()
    cfg=json.loads(Path(args.config).read_text(encoding="utf-8"))
    alpha_override=any(v is not None for v in [args.alpha_low_percentile,args.alpha_full_percentile,args.alpha_full_value]) or args.alpha_full_max
    if args.threshold is not None:
        if alpha_override:p.error("--threshold (binary) cannot be combined with continuous-alpha overrides")
        cfg["threshold"]={"mode":"manual","value":args.threshold}
        cfg["alpha"]={"mode":"binary"}
    if alpha_override:
        spec=cfg.setdefault("alpha",{})
        spec["mode"]="continuous"
        if args.alpha_low_percentile is not None:spec["low"]={"mode":"percentile","value":args.alpha_low_percentile}
        if args.alpha_full_percentile is not None:spec["full"]={"mode":"percentile","value":args.alpha_full_percentile}
        if args.alpha_full_value is not None:spec["full"]={"mode":"manual","value":args.alpha_full_value}
        if args.alpha_full_max:spec["full"]={"mode":"max"}
    if args.sigma is not None:cfg["sigma_px"]=args.sigma
    if args.tem_opacity is not None:cfg["tem_opacity"]=args.tem_opacity
    if args.tem_window is not None:cfg["tem_window"]=args.tem_window
    m=run_pipeline(args.input,args.output,cfg,args.tem)
    print(json.dumps({"output":str(Path(args.output).resolve()),"statistics":m["statistics"],"validation":m["validation"]},indent=2))


if __name__ == "__main__":
    main()

