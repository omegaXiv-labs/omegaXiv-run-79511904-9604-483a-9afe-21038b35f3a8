from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pypdfium2 as pdfium
import seaborn as sns


def apply_style() -> None:
    sns.set_theme(style="whitegrid", context="talk", palette="deep")
    plt.rcParams["figure.dpi"] = 140
    plt.rcParams["savefig.dpi"] = 200
    plt.rcParams["axes.titlesize"] = 13
    plt.rcParams["axes.labelsize"] = 11
    plt.rcParams["legend.fontsize"] = 9


def verify_pdf_readability(pdf_path: Path, check_dir: Path) -> dict[str, float | bool | str]:
    check_dir.mkdir(parents=True, exist_ok=True)
    doc = pdfium.PdfDocument(str(pdf_path))
    page = doc.get_page(0)
    bitmap = page.render(scale=2.0)
    pil_image = bitmap.to_pil()
    png_path = check_dir / f"{pdf_path.stem}_preview.png"
    pil_image.save(png_path)

    arr = np.asarray(pil_image.convert("L"), dtype=float)
    contrast = float(arr.std())
    non_white = float(np.mean(arr < 245.0))

    page.close()
    doc.close()

    return {
        "pdf": str(pdf_path),
        "preview_png": str(png_path),
        "contrast_std": contrast,
        "ink_fraction": non_white,
        "readable": bool(contrast > 12.0 and non_white > 0.01),
    }
