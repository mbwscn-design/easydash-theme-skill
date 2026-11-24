#!/usr/bin/env python3
"""将 EasyDash manifest 及其引用的本地素材打包为一个可分享的 JSON 文件。"""

import argparse
import base64
import json
import math
import os
from pathlib import Path
import re
import struct
import sys
import tempfile
from urllib.parse import unquote, urlsplit


MIB = 1024 * 1024
ELEMENT_TYPES = {
    "label", "panel", "metric", "arcGauge", "radialGauge", "barGauge",
    "vehicleDiagram", "traceChart", "line", "grid", "image", "rpmImage",
}
RESOURCE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,119}\.(?:png|jpe?g|webp|wav)", re.ASCII | re.I)


def read_limited(path, limit):
    if not path.is_file():
        raise ValueError(f"找不到文件：{path}")
    with path.open("rb") as source:
        data = source.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"{path.name} 超过 {limit // 1024} KB")
    return data


def finite(value):
    return type(value) in (int, float) and abs(value) <= 1e9 and math.isfinite(value)


def check_manifest(manifest):
    if not isinstance(manifest, dict) or manifest.get("schemaVersion") != 1 or type(manifest["schemaVersion"]) is bool:
        raise ValueError("输入应是 schemaVersion 为 1 的 manifest，或 version 为 1 的 easydash.theme 主题包。")
    identifier = manifest.get("id")
    if not isinstance(identifier, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", identifier) or ".." in identifier:
        raise ValueError("id 需要 1–128 位英文字母、数字、下划线、连字符或点；不能含连续两点。")
    title = manifest.get("title")
    if not isinstance(title, str) or not title.strip() or len(title.encode("utf-16-le")) > 240:
        raise ValueError("请填写有效的 title，长度不超过 120 个 UTF-16 字符单元。")
    if manifest.get("orientation") not in ("portrait", "landscape"):
        raise ValueError("orientation 应填写 portrait 或 landscape")
    canvas = manifest.get("canvas")
    if not isinstance(canvas, dict) or not all(finite(canvas.get(k)) and 0 < canvas[k] <= 8192 for k in ("width", "height")):
        raise ValueError("canvas.width 和 canvas.height 应大于 0 且不超过 8192")
    if canvas["width"] * canvas["height"] > 32 * MIB or canvas.get("fit") not in (None, "contain", "cover", "fill", "fitWidth", "fitHeight"):
        raise ValueError("请检查画布面积和 canvas.fit")
    elements = manifest.get("elements")
    if not isinstance(elements, list) or not 1 <= len(elements) <= 128:
        raise ValueError("可安装的主题需要 1–128 个元素")
    for index, element in enumerate(elements):
        if not isinstance(element, dict) or not isinstance(element.get("type"), str) or element["type"] not in ELEMENT_TYPES:
            raise ValueError(f"elements[{index}].type 不是 EasyDash 支持的组件")
        for key in ("x", "y", "width", "height"):
            value = element.get(key)
            if not finite(value) or abs(value) > 16384 or (key in ("width", "height") and value <= 0):
                raise ValueError(f"elements[{index}].{key} 无效，请检查坐标或尺寸")
        if "min" in element and "max" in element:
            low, high = element["min"], element["max"]
            if not finite(low) or not finite(high) or low >= high:
                raise ValueError(f"elements[{index}] 的 min 和 max 应为数字且 min < max")
        if "decimals" in element and (type(element["decimals"]) is not int or not 0 <= element["decimals"] <= 6):
            raise ValueError(f"elements[{index}].decimals 应为 0–6 的整数")


def resource_name(reference, audio=False):
    if not isinstance(reference, str) or not reference.startswith("resource:"):
        raise ValueError("包内素材应写成 resource:文件名")
    name = reference[9:]
    if not RESOURCE_NAME.fullmatch(name) or ".." in name or name.lower().endswith(".wav") != audio:
        raise ValueError(f"无效资源 {name!r}：使用单层英文文件名，图片支持 PNG、JPEG、WebP；音频使用 WAV。")
    return name


def resources_used(manifest):
    names = set()
    for element in manifest["elements"]:
        if element["type"] == "rpmImage":
            fields = ("idleUrl", "focusUrl", "redlineUrl", "idleAsset", "focusAsset", "redlineAsset")
        elif element["type"] == "image":
            fields = ("url", "asset") if element.get("cueId") is None else ("url", "asset", "focusUrl", "focusAsset")
        else:
            continue
        for field in fields:
            ref = element.get(field)
            if ref is None or ref == "":
                continue
            if not isinstance(ref, str):
                raise ValueError(f"{field} 应填写图片引用")
            if field.lower().endswith("asset") and not ref.startswith("assets/"):
                raise ValueError(f"{field} 专用于应用自带的 assets/，自带文件请使用对应的 url 或 *Url 字段。")
            if ref.startswith("resource:"):
                names.add(resource_name(ref))
                continue
            uri = urlsplit(ref)
            path = uri.path
            for _ in range(5):
                if "\\" in path or any(part in (".", "..") for part in path.split("/")):
                    raise ValueError(f"图片路径含有不支持的路径段：{ref}")
                decoded = unquote(path)
                if path == decoded:
                    break
                path = decoded
            if ref.startswith("assets/") and not uri.query and not uri.fragment:
                continue
            if uri.scheme != "https" or not uri.hostname or uri.username is not None or "\\" in ref:
                raise ValueError(f"图片路径无效：{ref}。本地素材请使用 resource:文件名。")
    cues = manifest.get("soundCues")
    if cues is None:
        cues = []
    if not isinstance(cues, list) or len(cues) > 8:
        raise ValueError("soundCues 应是包含最多 8 条提示音的数组")
    cue_ids = set()
    for cue in cues:
        if not isinstance(cue, dict):
            raise ValueError("soundCues 每项应为对象")
        identifier = cue.get("id")
        if not isinstance(identifier, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", identifier) or identifier in cue_ids:
            raise ValueError("soundCues 中的 id 必须有效且唯一")
        cue_ids.add(identifier)
        for key in ("slot", "parameter"):
            value = cue.get(key)
            if not isinstance(value, str) or not value or value.strip() != value or len(value.encode("utf-16-le")) > 256:
                raise ValueError(f"音效 {identifier} 缺少有效的 {key}")
        hysteresis, interval, volume = cue.get("hysteresis", 200), cue.get("minIntervalMs", 2500), cue.get("volume", .55)
        if not finite(cue.get("threshold")) or not finite(hysteresis) or hysteresis <= 0 or type(interval) is not int or not 250 <= interval <= 60000 or not finite(volume) or not 0 <= volume <= 1:
            raise ValueError(f"请检查音效 {identifier} 的阈值、回差、冷却间隔和音量")
        names.add(resource_name(cue.get("source"), audio=True))
    return names


def image_size(name, data):
    ext = Path(name).suffix.lower()
    if ext == ".png" and len(data) >= 33 and data.startswith(b"\x89PNG\r\n\x1a\n") and data[12:16] == b"IHDR":
        return struct.unpack_from(">II", data, 16)
    if ext in (".jpg", ".jpeg") and data.startswith(b"\xff\xd8\xff") and data.endswith(b"\xff\xd9"):
        pos = 2
        while pos + 4 <= len(data) and data[pos] == 255:
            while pos < len(data) and data[pos] == 255:
                pos += 1
            if pos + 3 > len(data):
                break
            marker = data[pos]
            pos += 1
            if marker in (0xD9, 0xDA):
                break
            if marker == 1 or 0xD0 <= marker <= 0xD7:
                continue
            length = int.from_bytes(data[pos:pos + 2], "big")
            if length < 2 or pos + length > len(data):
                break
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC) and length >= 8:
                height, width = struct.unpack_from(">HH", data, pos + 3)
                return width, height
            pos += length
    if ext == ".webp" and len(data) >= 30 and data.startswith(b"RIFF") and data[8:12] == b"WEBP" and int.from_bytes(data[4:8], "little") + 8 == len(data):
        chunk = data[12:16]
        if chunk == b"VP8X" and int.from_bytes(data[16:20], "little") >= 10:
            return 1 + int.from_bytes(data[24:27], "little"), 1 + int.from_bytes(data[27:30], "little")
        if chunk == b"VP8L" and data[20] == 47:
            bits = int.from_bytes(data[21:25], "little")
            return 1 + (bits & 0x3fff), 1 + ((bits >> 14) & 0x3fff)
        if chunk == b"VP8 " and data[23:26] == b"\x9d\x01\x2a":
            width, height = struct.unpack_from("<HH", data, 26)
            return width & 0x3fff, height & 0x3fff
    raise ValueError(f"{name} 不是有效的 {ext} 图片，请重新导出")


def check_wave(name, data):
    message = f"{name} 需要为 3 秒以内、8–48 kHz、单声道或双声道的 16 位 PCM WAV"
    if len(data) < 44 or data[:4] != b"RIFF" or data[8:12] != b"WAVE" or int.from_bytes(data[4:8], "little") + 8 != len(data):
        raise ValueError(message)
    pos = 12
    bytes_per_second = 0
    has_samples = False
    while pos + 8 <= len(data):
        chunk, length = struct.unpack_from("<4sI", data, pos)
        start = pos + 8
        pos = start + length + (length & 1)
        if pos > len(data):
            raise ValueError(message)
        if chunk == b"fmt ":
            if bytes_per_second or length < 16:
                raise ValueError(message)
            pcm, channels, rate, byte_rate, block, bits = struct.unpack_from("<HHIIHH", data, start)
            if pcm != 1 or channels not in (1, 2) or bits != 16 or not 8000 <= rate <= 48000:
                raise ValueError(message)
            bytes_per_second = rate * channels * 2
            if block != channels * 2 or byte_rate != bytes_per_second:
                raise ValueError(message)
        elif chunk == b"data":
            if not bytes_per_second or has_samples or not 0 < length <= 3 * bytes_per_second or length % block:
                raise ValueError(message)
            has_samples = True
    if pos != len(data) or not has_samples:
        raise ValueError(message)


def unpack_source(document):
    if not isinstance(document, dict) or "format" not in document:
        return document, {}
    if document.get("format") != "easydash.theme" or type(document.get("version")) is not int or document["version"] != 1:
        raise ValueError("仅支持 version 为 1 的 easydash.theme 便携主题包")
    embedded = {}
    for field, audio in (("resources", False), ("audioResources", True)):
        mapping = document.get(field, {})
        if not isinstance(mapping, dict) or len(mapping) > (8 if audio else 64):
            raise ValueError(f"原主题包的 {field} 数量或字段格式无效")
        for name, encoded in mapping.items():
            resource_name("resource:" + name, audio)
            limit = 600 * 1024 if audio else 8 * MIB
            if not isinstance(encoded, str) or len(encoded) > 4 * ((limit + 2) // 3):
                raise ValueError(f"{name} 资源编码无效或文件太大")
            try:
                embedded[name] = base64.b64decode(encoded, validate=True)
            except ValueError as error:
                raise ValueError(f"{name} 不是有效的 base64 资源") from error
    return document.get("watchface"), embedded


def pack(manifest_file, assets, output, force):
    if output.resolve() == manifest_file.resolve():
        raise ValueError("输出路径和输入 manifest 相同，请另选输出文件名。")
    document = json.loads(read_limited(manifest_file, 32 * MIB).decode("utf-8-sig"))
    manifest, embedded = unpack_source(document)
    check_manifest(manifest)
    package = {"format": "easydash.theme", "version": 1, "watchface": manifest, "resources": {}}
    assets = assets.resolve()
    total = 0
    names = resources_used(manifest).union(embedded)
    if len({name.lower() for name in names}) != len(names):
        raise ValueError("资源文件名不能仅大小写不同，请统一引用与文件名")
    if sum(not name.lower().endswith(".wav") for name in names) > 64 or sum(name.lower().endswith(".wav") for name in names) > 8:
        raise ValueError("主题资源上限为 64 张图片和 8 个音效")
    for name in sorted(names):
        audio = name.lower().endswith(".wav")
        limit = 600 * 1024 if audio else 8 * MIB
        if name in embedded:
            data = embedded[name]
            if len(data) > limit:
                raise ValueError(f"{name} 的原有素材超过大小限制")
        else:
            source = (assets / name).resolve()
            if source.parent != assets or source == output.resolve():
                raise ValueError(f"请将 {name} 放在素材目录内，并使用独立的输出文件。")
            data = read_limited(source, limit)
        total += len(data)
        if total > 24 * MIB:
            raise ValueError("未编码的素材总量超过 24 MB")
        if audio:
            check_wave(name, data)
        else:
            w, h = image_size(name, data)
            if not (0 < w <= 8192 and 0 < h <= 8192 and w * h <= 16 * MIB):
                raise ValueError(f"{name} 图片尺寸超限：{w} × {h}")
        target = package.setdefault("audioResources", {}) if audio else package["resources"]
        target[name] = base64.b64encode(data).decode("ascii")
    payload = json.dumps(package, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
    if len(payload) > 32 * MIB:
        raise ValueError("编码后主题超过 32 MB，请压缩素材后重试。")
    output.parent.mkdir(parents=True, exist_ok=True)
    if not force:
        try:
            destination = output.open("xb")
        except FileExistsError as error:
            raise ValueError(f"{output} 已存在；请换名，或使用 --force 更新这份输出。") from error
        try:
            with destination:
                destination.write(payload)
        except OSError:
            output.unlink()
            raise
    else:
        with tempfile.TemporaryDirectory(dir=output.parent) as staging:
            temp = Path(staging) / "theme.json"
            temp.write_bytes(payload)
            os.replace(temp, output)
    print(f"已生成 {output}（{len(package['resources'])} 张图片，{len(package.get('audioResources', {}))} 个音效）")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="manifest.json 或已有的 *.easydash.json")
    parser.add_argument("--assets", type=Path, help="resource: 文件所在目录，默认为 manifest 所在目录")
    parser.add_argument("--out", required=True, type=Path, help="输出文件，例如 赛道.easydash.json")
    parser.add_argument("--force", action="store_true", help="替换已有输出文件")
    args = parser.parse_args()
    try:
        pack(args.manifest, args.assets or args.manifest.parent, args.out, args.force)
    except (ValueError, OSError, RecursionError) as error:
        parser.exit(1, f"打包失败：{error}\n")


if __name__ == "__main__":
    main()
