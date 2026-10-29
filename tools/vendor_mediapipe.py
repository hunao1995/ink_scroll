#!/usr/bin/env python3
"""
把 MediaPipe（手势 / 面庞）下载到本地，展厅断网也能用。

    python3 tools/vendor_mediapipe.py          # 下载到 web/vendor/mediapipe/（约 37 MB，不进 git）
    python3 tools/vendor_mediapipe.py --check  # 只检查本地是否齐全

页面启动时会 HEAD 一次 vendor/mediapipe/hands/hands.js：有就全用本地，没有就回退 jsdelivr。
"""
import os, sys, urllib.request

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "vendor", "mediapipe")
PKGS = {
    "camera_utils": ("https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils@0.3/", ["camera_utils.js"]),
    "hands": ("https://cdn.jsdelivr.net/npm/@mediapipe/hands@0.4.1675469240/", [
        "hands.js", "hands.binarypb", "hands_solution_packed_assets.data", "hands_solution_packed_assets_loader.js",
        "hands_solution_simd_wasm_bin.js", "hands_solution_simd_wasm_bin.wasm", "hands_solution_simd_wasm_bin.data",
        "hands_solution_wasm_bin.js", "hands_solution_wasm_bin.wasm", "hand_landmark_lite.tflite"]),
    "face_mesh": ("https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh@0.4.1633559619/", [
        "face_mesh.js", "face_mesh.binarypb", "face_mesh_solution_packed_assets.data", "face_mesh_solution_packed_assets_loader.js",
        "face_mesh_solution_simd_wasm_bin.js", "face_mesh_solution_simd_wasm_bin.wasm", "face_mesh_solution_simd_wasm_bin.data",
        "face_mesh_solution_wasm_bin.js", "face_mesh_solution_wasm_bin.wasm"]),
}

def main():
    check = "--check" in sys.argv
    missing, total = [], 0
    for pkg, (base, files) in PKGS.items():
        d = os.path.join(ROOT, pkg); os.makedirs(d, exist_ok=True)
        for f in files:
            dst = os.path.join(d, f)
            if os.path.exists(dst) and os.path.getsize(dst) > 0:
                total += os.path.getsize(dst); continue
            if check:
                missing.append(f"{pkg}/{f}"); continue
            print(f"  ↓ {pkg}/{f}", flush=True)
            try:
                urllib.request.urlretrieve(base + f, dst)
                total += os.path.getsize(dst)
            except Exception as e:
                if f.endswith("_wasm_bin.data"):      # 有的版本是 0 字节 / 不存在，可忽略
                    open(dst, "wb").close(); continue
                print(f"  ✗ {pkg}/{f}: {e}"); missing.append(f"{pkg}/{f}")
    print(f"\n  vendor: {ROOT}\n  {total/1048576:.1f} MB on disk; missing: {missing or 'none'}")
    sys.exit(1 if missing else 0)

if __name__ == "__main__":
    main()
