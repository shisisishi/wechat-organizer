"""
OCR 助手：接收图片路径，返回结构化文本块(坐标+文字) JSON。
被 node_repl(sky) 通过子进程调用，或可单独使用。
"""
import sys, json, tempfile, os
from rapidocr_onnxruntime import RapidOCR

_OCR = None
def get_ocr():
    global _OCR
    if _OCR is None:
        _OCR = RapidOCR()
    return _OCR

def ocr_file(path, min_score=0.45):
    ocr = get_ocr()
    result, elapse = ocr(path)
    items = []
    if result:
        for box, text, score in result:
            try:
                sc = float(score)
            except Exception:
                sc = 0.0
            if sc < min_score:
                continue
            xs = [p[0] for p in box]; ys = [p[1] for p in box]
            items.append({
                "text": text,
                "score": round(sc, 4),
                "x0": int(min(xs)), "y0": int(min(ys)),
                "x1": int(max(xs)), "y1": int(max(ys)),
                "cx": int(sum(xs)/4), "cy": int(sum(ys)/4),
            })
    # 按从上到下、从左到右排序
    items.sort(key=lambda it: (it["cy"]//10, it["cx"]))
    return {"count": len(items), "items": items}

if __name__ == "__main__":
    # usage: python ocr.py <image_path> [min_score]
    img = sys.argv[1]
    ms = float(sys.argv[2]) if len(sys.argv) > 2 else 0.45
    out = ocr_file(img, ms)
    sys.stdout.write(json.dumps(out, ensure_ascii=False))
