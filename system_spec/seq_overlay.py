from .styles import _e

# ── Sequence playback overlay (hidden step paths drawn on the architecture diagram) ──

def render_sequence_overlay_svg(spec: dict, positions: dict) -> str:
    sequences = spec.get("sequences", [])
    if not sequences or not positions:
        return ""

    parts = []
    for seq in sequences:
        seq_id = seq.get("id", "")
        steps = seq.get("steps", [])
        for i, step in enumerate(steps):
            src = step.get("from")
            dst = step.get("to")
            if src not in positions or dst not in positions:
                continue

            gid = f"ov-{seq_id}-{i}"
            parts.append(
                f'<g class="seq-step-ov" id="{_e(gid)}" data-seq="{_e(seq_id)}" data-step="{i}" '
                f'data-from="{_e(src)}" data-to="{_e(dst)}" style="opacity:0">'
            )

            if src == dst:
                # Self-referential step: small loop arc off the right side of the node
                p  = positions[src]
                cx = p["x"] + p["w"]
                cy = p["y"] + p["h"] / 2
                path_d = (
                    f'M{cx:.1f},{cy-8:.1f} Q{cx+24:.1f},{cy-8:.1f} {cx+24:.1f},{cy:.1f} '
                    f'Q{cx+24:.1f},{cy+8:.1f} {cx:.1f},{cy+8:.1f}'
                )
                dot_x, dot_y = cx, cy - 8
            else:
                # Same bezier curve shape used for real edges in svg_architecture.py,
                # so playback paths look consistent with the static diagram.
                sp, dp   = positions[src], positions[dst]
                sx       = sp["x"] + sp["w"] / 2
                sy       = sp["y"] + sp["h"]
                ex       = dp["x"] + dp["w"] / 2
                ey       = dp["y"]
                dy       = ey - sy
                cx1, cy1 = sx, sy + dy * 0.45
                cx2, cy2 = ex, ey - dy * 0.45
                path_d   = f'M{sx:.1f},{sy:.1f} C{cx1:.1f},{cy1:.1f} {cx2:.1f},{cy2:.1f} {ex:.1f},{ey:.1f}'
                dot_x, dot_y = sx, sy

            parts.append(
                f'<path class="seq-ov-path" d="{path_d}" fill="none" stroke="#D97757" stroke-width="2"/>'
            )
            parts.append(
                f'<circle class="seq-dot" cx="{dot_x:.1f}" cy="{dot_y:.1f}" r="5" fill="#D97757"/>'
            )
            parts.append("</g>")

    return "\n".join(parts)
