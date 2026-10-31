// Import Python's exact outputs; do not recompute Gaussian/alpha in ImageJ.
// File > New > Script, choose IJ1 Macro, or Plugins > Macros > Run.
// Optional argument is the run folder (used for reproducibility checks).
dir = getArgument();
interactive = dir == "";
if (interactive) dir = getDirectory("Choose a Python run folder");
if (!endsWith(dir, "/") && !endsWith(dir, "\\")) dir = dir + "/";
if (!File.exists(dir+"04_selection_mask_uint8.tif")) exit("No selection mask in this folder.");

open(dir+"00_signed_ifft_float32.tif");
rename("IFFT_source_copy");
open(dir+"01_linear_green_channel_float32.tif");
rename("Normalized_scalar_Green_LUT_reference");
setMinAndMax(0,1);
run("Green"); // LUT changes display, not the 32-bit values.
// The scalar Green LUT is not the green-white color map. Open Python's exact RGB.
open(dir+"01_linear_green_rgb.tif");
rename("Step1_exact_color_RGB");
open(dir+"03_abs_gaussian_float32.tif");
rename("Abs_Gaussian_mapping_float32");
open(dir+"06_selected_on_black_rgb.tif");
rename("Selected_color_on_black");
if (File.exists(dir+"05_alpha_float32.tif")) {
    open(dir+"05_alpha_float32.tif");
    rename("Continuous_alpha_0_to_1");
    setMinAndMax(0,1);
}
open(dir+"04_selection_mask_uint8.tif");
rename("Auxiliary_support_mask_0_255");
setThreshold(255,255);
run("Create Selection");
if (selectionType != -1) {
    roiManager("Add");
    selectionIndex = roiManager("count")-1;
    roiManager("Select",selectionIndex);
    roiManager("Rename","IFFT_signal_selection");
    // A green contour can be transferred to a TEM already in the same coordinates.
    if (interactive) {
        Dialog.create("Optional original TEM reference");
        Dialog.addCheckbox("Open aligned original TEM and add a contour overlay",false);
        Dialog.show();
        if (Dialog.getCheckbox()) {
            w=getWidth(); h=getHeight();
            path=File.openDialog("Choose aligned original TEM");
            open(path);
            if (getWidth()!=w || getHeight()!=h) exit("Size mismatch; no resizing or registration was performed.");
            roiManager("Select",selectionIndex);
            Overlay.addSelection("green",1);
            run("Select None");
            Overlay.show;
        }
    }
}
print("Imported exact Python outputs. No input pixel values were modified.");
print("RGBA PNG transparency may be lost in ImageJ. The support mask/ROI does not reproduce continuous alpha; use Python's final composite.");

