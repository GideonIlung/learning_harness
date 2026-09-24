#!/usr/bin/env -S uv run python
from __future__ import annotations

import ast, base64, json, math, os, re, shutil, sys, time, uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle
import numpy as np

VISUAL_TYPES = {"function_plot", "vectors", "geometry", "sequence", "mapping", "proof_diagram"}
MANIFEST = "manifest.jsonl"

SAFE_FUNCS = {
    "sin": np.sin, "cos": np.cos, "tan": np.tan, "exp": np.exp, "log": np.log,
    "sqrt": np.sqrt, "abs": np.abs, "minimum": np.minimum, "maximum": np.maximum,
    "arcsin": np.arcsin, "arccos": np.arccos, "arctan": np.arctan,
    "sinh": np.sinh, "cosh": np.cosh, "tanh": np.tanh,
    "pi": np.pi, "e": np.e
}
ALLOWED_AST = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Call, ast.Load, ast.Name, ast.Constant,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.USub, ast.UAdd,
)


def project_root() -> Path:
    return Path(os.environ.get("LEARNING_VISUALS_PROJECT_ROOT", os.getcwd())).resolve()


def visuals_dir(root: Path) -> Path:
    return root / ".learning" / "visuals"


def manifest_path(root: Path) -> Path:
    return visuals_dir(root) / MANIFEST


def ensure_dir(root: Path) -> Path:
    d = visuals_dir(root)
    d.mkdir(parents=True, exist_ok=True)
    return d


def slug(s: str) -> str:
    s = re.sub(r"[^A-Za-z0-9_.-]+", "-", s.strip()).strip("-")
    return s[:48] or "visual"


def new_png_path(root: Path, visual_type: str, title: str = "") -> Path:
    d = ensure_dir(root)
    name = f"{time.strftime('%Y%m%d-%H%M%S')}-{visual_type}-{slug(title)}-{uuid.uuid4().hex[:8]}.png"
    return d / name


def write_manifest(root: Path, item: Dict[str, Any]) -> None:
    ensure_dir(root)
    with manifest_path(root).open("a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")


def validate_expr(expr: str) -> ast.AST:
    expr = expr.replace("^", "**")
    tree = ast.parse(expr, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED_AST):
            raise ValueError(f"Unsupported expression syntax: {type(node).__name__}")
        if isinstance(node, ast.Name) and node.id not in SAFE_FUNCS and node.id != "x":
            raise ValueError(f"Unsupported name in expression: {node.id}")
        if isinstance(node, ast.Call) and not isinstance(node.func, ast.Name):
            raise ValueError("Only simple function calls like sin(x) are allowed")
    return compile(tree, "<expression>", "eval")


def eval_expr(expr: str, x: np.ndarray) -> np.ndarray:
    code = validate_expr(expr)
    return eval(code, {"__builtins__": {}}, {**SAFE_FUNCS, "x": x})


def setup_axes(ax, spec):
    if spec.get("axis_labels"):
        labels = spec["axis_labels"]
        ax.set_xlabel(labels[0] if len(labels) > 0 else "x")
        ax.set_ylabel(labels[1] if len(labels) > 1 else "y")
    ax.grid(True, alpha=0.25)


def render_function_plot(ax, spec: Dict[str, Any]) -> None:
    xr = spec.get("x_range", [-5, 5])
    yr = spec.get("y_range")
    x = np.linspace(float(xr[0]), float(xr[1]), int(spec.get("samples", 600)))
    funcs = spec.get("functions", [])
    if isinstance(funcs, dict): funcs = [funcs]
    if not funcs: raise ValueError("function_plot requires spec.functions")
    for f in funcs:
        y = eval_expr(str(f.get("expr", "x")), x)
        ax.plot(x, y, label=f.get("label") or f.get("expr"), linewidth=2)
    if yr: ax.set_ylim(float(yr[0]), float(yr[1]))
    ax.set_xlim(float(xr[0]), float(xr[1]))
    for p in spec.get("highlighted_points", []):
        px, py = float(p["x"]), float(p["y"])
        ax.scatter([px], [py], s=55, zorder=4)
        if p.get("label"): ax.annotate(p["label"], (px, py), xytext=(6, 8), textcoords="offset points")
    for a in spec.get("annotations", []):
        xy = tuple(a.get("xy", [0, 0])); text = a.get("text", "")
        xytext = tuple(a.get("xytext", [xy[0], xy[1]]))
        ax.annotate(text, xy=xy, xytext=xytext, arrowprops=dict(arrowstyle="->", lw=1.2))
    setup_axes(ax, spec)
    if len(funcs) > 1 or any(f.get("label") for f in funcs): ax.legend(frameon=False)


def draw_vector(ax, start, vec, label=None, color=None):
    ax.arrow(start[0], start[1], vec[0], vec[1], head_width=0.12, length_includes_head=True, linewidth=2, color=color)
    if label:
        ax.text(start[0]+vec[0]*0.55, start[1]+vec[1]*0.55, label, fontsize=11, color=color)


def render_vectors(ax, spec):
    if spec.get("show_axes", True):
        ax.axhline(0, color="black", lw=0.8); ax.axvline(0, color="black", lw=0.8)
    points = []
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    for i, v in enumerate(spec.get("vectors", [])):
        start = v.get("start", [0,0]); end = v.get("end"); vec = v.get("coords") or ([end[0]-start[0], end[1]-start[1]] if end else None)
        if vec is None: raise ValueError("Each vector needs coords or end")
        draw_vector(ax, start, vec, v.get("label"), v.get("color") or colors[i % len(colors)])
        points += [start, [start[0]+vec[0], start[1]+vec[1]]]
    for c in spec.get("components", []):
        v = c.get("coords", [0,0]); start = c.get("start", [0,0])
        ax.plot([start[0], start[0]+v[0], start[0]+v[0]], [start[1], start[1], start[1]+v[1]], '--', color='gray')
    if points:
        xs, ys = [p[0] for p in points], [p[1] for p in points]
        pad = 1; ax.set_xlim(min(xs)-pad, max(xs)+pad); ax.set_ylim(min(ys)-pad, max(ys)+pad)
    ax.set_aspect('equal', adjustable='box'); ax.grid(True, alpha=.25)
    if spec.get("axis_labels"):
        ax.set_xlabel(spec["axis_labels"][0]); ax.set_ylabel(spec["axis_labels"][1])


def render_geometry(ax, spec):
    if spec.get("show_axes", False): ax.axhline(0,color='black',lw=.8); ax.axvline(0,color='black',lw=.8); ax.grid(True,alpha=.25)
    allp=[]
    for obj in spec.get("objects", []):
        t=obj.get("type")
        if t=="point":
            p=obj["xy"]; ax.scatter([p[0]],[p[1]],s=40); allp.append(p)
            if obj.get("label"): ax.text(p[0]+.05,p[1]+.05,obj["label"])
        elif t in ("line_segment","segment"):
            a,b=obj["start"],obj["end"]; ax.plot([a[0],b[0]],[a[1],b[1]],lw=2); allp += [a,b]
        elif t=="line":
            a,b=obj["start"],obj["end"]; ax.axline(a,b,lw=1.6); allp += [a,b]
        elif t=="circle":
            c=obj["center"]; r=obj["radius"]; ax.add_patch(Circle(c,r,fill=False,lw=2)); allp += [[c[0]-r,c[1]-r],[c[0]+r,c[1]+r]]
        elif t=="arrow":
            a,b=obj["start"],obj["end"]; ax.annotate("",xy=b,xytext=a,arrowprops=dict(arrowstyle="->",lw=2)); allp += [a,b]
        elif t=="polygon":
            pts=obj["points"]; ax.add_patch(Polygon(pts,closed=True,alpha=obj.get("alpha",.2),fill=obj.get("fill",True),lw=2)); allp += pts
        elif t=="label":
            p=obj["xy"]; ax.text(p[0],p[1],obj.get("text",""),fontsize=11); allp.append(p)
    if allp:
        xs=[p[0] for p in allp]; ys=[p[1] for p in allp]; pad=1
        ax.set_xlim(min(xs)-pad,max(xs)+pad); ax.set_ylim(min(ys)-pad,max(ys)+pad)
    ax.set_aspect('equal', adjustable='box')


def render_sequence(ax, spec):
    vals = np.array(spec.get("values", []), dtype=float)
    if len(vals)==0: raise ValueError("sequence requires spec.values")
    n = np.arange(len(vals)) if not spec.get("iterations") else np.array(spec["iterations"])
    marker='o' if spec.get("markers", True) else None
    ax.plot(n, vals, '-'+(marker or ''), lw=2)
    if "target" in spec:
        ax.axhline(float(spec["target"]), ls='--', color='red', label=spec.get("target_label","target")); ax.legend(frameon=False)
    ax.set_xlabel(spec.get("x_label","iteration n")); ax.set_ylabel(spec.get("y_label","value")); ax.grid(True,alpha=.25)
    for lab in spec.get("labels", []): ax.annotate(lab.get("text",""), xy=lab.get("xy",[0,0]), xytext=lab.get("xytext", lab.get("xy",[0,0])), arrowprops=dict(arrowstyle="->"))


def render_node_flow(ax, spec, proof=False):
    nodes=spec.get("nodes",[])
    if not nodes: raise ValueError("mapping/proof_diagram requires spec.nodes")
    n=len(nodes)
    positions={}
    for i,node in enumerate(nodes):
        if "xy" in node: pos=tuple(node["xy"])
        elif proof: pos=(0, -i*1.4)
        else: pos=(i*2.6, 0)
        positions[node.get("id", str(i))]=pos
        w=node.get("width",2.0); h=node.get("height",.75)
        ax.add_patch(Rectangle((pos[0]-w/2,pos[1]-h/2),w,h,fc="#f7f7f7",ec="#333",lw=1.4))
        ax.text(pos[0],pos[1],node.get("label",node.get("id",str(i))),ha='center',va='center',fontsize=10,wrap=True)
    arrows=spec.get("arrows")
    if arrows is None:
        ids=[node.get("id", str(i)) for i,node in enumerate(nodes)]
        arrows=[{"from":ids[i],"to":ids[i+1]} for i in range(n-1)]
    for ar in arrows:
        a=positions[ar["from"]]; b=positions[ar["to"]]
        ax.annotate(ar.get("label",""), xy=b, xytext=a, ha='center', va='center', arrowprops=dict(arrowstyle="->", lw=1.5, shrinkA=28, shrinkB=28))
    for g in spec.get("groups", []):
        ids=g.get("nodes",[]); pts=[positions[i] for i in ids if i in positions]
        if pts:
            xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
            ax.add_patch(Rectangle((min(xs)-1.25,min(ys)-.75), max(xs)-min(xs)+2.5, max(ys)-min(ys)+1.5, fill=False, ls='--', ec='gray'))
            ax.text(min(xs)-1.2, max(ys)+.55, g.get("label",""), fontsize=9, color='gray')
    ax.autoscale_view(); ax.axis('off'); ax.set_aspect('equal', adjustable='datalim')


def create_visual(root: Path, params: Dict[str, Any]) -> Dict[str, Any]:
    vt=params.get("visual_type")
    if vt not in VISUAL_TYPES: raise ValueError(f"visual_type must be one of {sorted(VISUAL_TYPES)}")
    spec=params.get("spec") or {}
    if not isinstance(spec, dict): raise ValueError("spec must be an object")
    title=params.get("title") or spec.get("title") or vt.replace('_',' ').title()
    desc=params.get("description") or spec.get("description") or title
    fig, ax = plt.subplots(figsize=tuple(spec.get("figsize", [7, 4.8])), dpi=int(spec.get("dpi", 140)))
    if vt=="function_plot": render_function_plot(ax,spec)
    elif vt=="vectors": render_vectors(ax,spec)
    elif vt=="geometry": render_geometry(ax,spec)
    elif vt=="sequence": render_sequence(ax,spec)
    elif vt=="mapping": render_node_flow(ax,spec,False)
    elif vt=="proof_diagram": render_node_flow(ax,spec,True)
    if title: ax.set_title(title)
    fig.tight_layout()
    path = new_png_path(root, vt, title)
    fig.savefig(path, bbox_inches='tight')
    plt.close(fig)
    item={"timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "filename": path.name, "path": str(path), "visual_type": vt, "description": desc}
    write_manifest(root,item)
    result={
        "path": str(path),
        "description": desc,
        "visual_type": vt,
        "content_type": "image/png",
        "display_guidance": {
            "preferred_for_current_environment": "browser",
            "reason": "VS Code integrated terminal does not support the needed inline image protocol.",
            "teacher_action_if_show_image_available": {
                "tool": "show_image",
                "source": str(path),
                "mode": "browser"
            }
        },
        "note": "Saved PNG under .learning/visuals/. If the pi-imgview show_image tool is available, display it with mode='browser'. Do not force Kitty/iTerm2 terminal graphics protocols in VS Code."
    }
    if params.get("include_base64", False):
        result["image_base64_png"] = base64.b64encode(path.read_bytes()).decode("ascii")
    return result


def recent_visuals(root: Path, limit=20) -> List[Dict[str,Any]]:
    mp=manifest_path(root)
    if not mp.exists(): return []
    out=[]
    for line in mp.read_text(encoding='utf-8').splitlines()[-limit:]:
        try: out.append(json.loads(line))
        except Exception: pass
    return out


def print_visuals(root: Path):
    rows=recent_visuals(root)
    if not rows:
        print("No generated visuals found."); return
    print(f"{'Filename':48} {'Type':15} Description")
    print(f"{'-'*48} {'-'*15} {'-'*30}")
    for r in rows:
        print(f"{r.get('filename','')[:48]:48} {r.get('visual_type','')[:15]:15} {r.get('description','')}")


def clear_visuals(root: Path, assume_yes=False):
    d=visuals_dir(root).resolve()
    root_res=root.resolve()
    if not str(d).startswith(str(root_res / '.learning' / 'visuals')):
        raise RuntimeError("Refusing to clear outside .learning/visuals")
    if not d.exists(): print("No visuals directory exists."); return
    files=[p for p in d.iterdir() if p.is_file()]
    if not assume_yes:
        resp=input(f"Delete {len(files)} generated file(s) from {d}? Type CLEAR to confirm: ")
        if resp != "CLEAR": print("Cancelled."); return
    for p in files: p.unlink()
    print(f"Deleted {len(files)} generated file(s) from {d}.")


def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser()
    sub=parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('visuals')
    c=sub.add_parser('clear-visuals'); c.add_argument('--yes', action='store_true')
    args=parser.parse_args(argv); root=project_root()
    if args.cmd=='visuals': print_visuals(root)
    elif args.cmd=='clear-visuals': clear_visuals(root,args.yes)
    return 0

if __name__=='__main__': raise SystemExit(main())
