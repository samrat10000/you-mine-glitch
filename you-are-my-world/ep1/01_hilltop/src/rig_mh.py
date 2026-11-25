"""Pure-NumPy MakeHuman CC0 rig, analytic 2-bone IK, sculpted draped garments/hair, and 2x SSAA rasterizer.
Zero Blender / zero scipy dependencies. Supports --preview to verify Gate G3 cast turnaround & contacts.
"""
from __future__ import annotations

import json
import math
import os
import sys
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
MH_DIR = os.path.join(PROJ_ROOT, "assets", "mh")

_OBJ_CACHE: Optional[Tuple[np.ndarray, np.ndarray, int]] = None
_SKEL_CACHE: Optional[dict] = None
_WEIGHTS_CACHE: Optional[dict] = None


def gauss_blur_f32(arr: np.ndarray, sigma: float) -> np.ndarray:
    """Fast pure-NumPy separable 1D Gaussian blur for float32 (H, W) or (H, W, C)."""
    if sigma < 0.2:
        return arr
    rad = max(1, int(math.ceil(3.0 * sigma)))
    x = np.arange(-rad, rad + 1, dtype=np.float32)
    k = np.exp(-0.5 * (x / sigma) ** 2)
    k /= k.sum()
    is_2d = arr.ndim == 2
    a = arr[..., None] if is_2d else arr
    pad_x = np.pad(a, ((0, 0), (rad, rad), (0, 0)), mode="edge")
    out_x = np.zeros_like(a)
    for i, w in enumerate(k):
        if w > 1e-6:
            out_x += float(w) * pad_x[:, i : i + a.shape[1], :]
    pad_y = np.pad(out_x, ((rad, rad), (0, 0), (0, 0)), mode="edge")
    out = np.zeros_like(a)
    for i, w in enumerate(k):
        if w > 1e-6:
            out += float(w) * pad_y[i : i + a.shape[0], :, :]
    return out[..., 0] if is_2d else out


def _norm(v: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if n > eps else np.zeros_like(v)


def _rot_axis_angle(axis: np.ndarray, rad: float) -> np.ndarray:
    if abs(rad) < 1e-9:
        return np.eye(3, dtype=np.float64)
    ax = _norm(axis)
    x, y, z = float(ax[0]), float(ax[1]), float(ax[2])
    c, s = math.cos(rad), math.sin(rad)
    t = 1.0 - c
    return np.array(
        [
            [t * x * x + c, t * x * y - s * z, t * x * z + s * y],
            [t * x * y + s * z, t * y * y + c, t * y * z - s * x],
            [t * x * z - s * y, t * y * z + s * x, t * z * z + c],
        ],
        dtype=np.float64,
    )


def _rot_between(u: np.ndarray, v: np.ndarray) -> np.ndarray:
    u, v = _norm(u), _norm(v)
    d = float(np.clip(np.dot(u, v), -1.0, 1.0))
    if d > 0.999999:
        return np.eye(3, dtype=np.float64)
    if d < -0.999999:
        ortho = np.array([1.0, 0.0, 0.0]) if abs(u[0]) < 0.8 else np.array([0.0, 1.0, 0.0])
        return _rot_axis_angle(_norm(np.cross(u, ortho)), math.pi)
    return _rot_axis_angle(np.cross(u, v), math.acos(d))


def _euler_xyz_deg(rx: float, ry: float, rz: float) -> np.ndarray:
    ax, ay, az = math.radians(rx), math.radians(ry), math.radians(rz)
    cx, sx = math.cos(ax), math.sin(ax)
    cy, sy = math.cos(ay), math.sin(ay)
    cz, sz = math.cos(az), math.sin(az)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]], dtype=np.float64)
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], dtype=np.float64)
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]], dtype=np.float64)
    return Rz @ Ry @ Rx


def load_base_obj() -> Tuple[np.ndarray, np.ndarray, int]:
    global _OBJ_CACHE
    if _OBJ_CACHE is not None:
        return _OBJ_CACHE
    vs: List[List[float]] = []
    tris: List[List[int]] = []
    g = None
    with open(os.path.join(MH_DIR, "base.obj"), "r", encoding="utf-8") as f:
        for ln in f:
            if ln.startswith("v "):
                vs.append([float(x) for x in ln.split()[1:4]])
            elif ln.startswith("g "):
                g = ln.split()[1]
            elif ln.startswith("f ") and g == "body":
                idx = [int(p.split("/")[0]) - 1 for p in ln.split()[1:]]
                if len(idx) == 4:
                    tris.append([idx[0], idx[1], idx[2]])
                    tris.append([idx[0], idx[2], idx[3]])
                elif len(idx) == 3:
                    tris.append(idx)
    _OBJ_CACHE = (np.array(vs, dtype=np.float64), np.array(tris, dtype=np.int32), 13380)
    return _OBJ_CACHE


def load_skel_weights() -> Tuple[dict, dict]:
    global _SKEL_CACHE, _WEIGHTS_CACHE
    if _SKEL_CACHE is None:
        with open(os.path.join(MH_DIR, "default.mhskel"), "r", encoding="utf-8") as f:
            _SKEL_CACHE = json.load(f)
    if _WEIGHTS_CACHE is None:
        with open(os.path.join(MH_DIR, "default_weights.mhw"), "r", encoding="utf-8") as f:
            _WEIGHTS_CACHE = json.load(f)["weights"]
    return _SKEL_CACHE, _WEIGHTS_CACHE


def _check_outward_winding(V: np.ndarray, T: np.ndarray, center=(0.0, -0.05, 0.90)) -> np.ndarray:
    p0, p1, p2 = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    fn = np.cross(p1 - p0, p2 - p0)
    cen = (p0 + p1 + p2) / 3.0
    dots = np.sum(fn * (cen - np.array(center, dtype=np.float64)), axis=1)
    if float(np.mean(dots > 0)) < 0.5:
        return T[:, [0, 2, 1]].copy()
    return T


def _smooth_vertex_normals(V: np.ndarray, T: np.ndarray) -> np.ndarray:
    p0, p1, p2 = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    fn = np.cross(p1 - p0, p2 - p0)
    vn = np.zeros_like(V)
    np.add.at(vn, T[:, 0], fn)
    np.add.at(vn, T[:, 1], fn)
    np.add.at(vn, T[:, 2], fn)
    return vn / np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-8)


def _laplacian_smooth_mesh(V: np.ndarray, T: np.ndarray, iters: int = 4, lam: float = 0.45) -> np.ndarray:
    """Smooth extracted garment mesh vertices to eliminate underlying muscle contours while keeping silhouette drape."""
    n = len(V)
    adj: List[set] = [set() for _ in range(n)]
    for a, b, c in T:
        adj[a].update((b, c))
        adj[b].update((a, c))
        adj[c].update((a, b))
    # Identify boundary vertices (edges occurring once) so hems stay crisp
    edge_cnt: Dict[Tuple[int, int], int] = {}
    for a, b, c in T:
        for u, v in ((a, b), (b, c), (c, a)):
            key = (u, v) if u < v else (v, u)
            edge_cnt[key] = edge_cnt.get(key, 0) + 1
    boundary = set()
    for (u, v), cnt in edge_cnt.items():
        if cnt == 1:
            boundary.add(u)
            boundary.add(v)
    Vc = V.copy()
    for _ in range(iters):
        Vn = Vc.copy()
        for i in range(n):
            if i in boundary or not adj[i]:
                continue
            nb = Vc[list(adj[i])].mean(axis=0)
            Vn[i] = Vc[i] * (1.0 - lam) + nb * lam
        Vc = Vn
    return Vc


def _bone_frame(head: np.ndarray, tail: np.ndarray) -> np.ndarray:
    d = tail - head
    by = np.array([0.0, 0.0, 1.0], dtype=np.float64) if float(np.linalg.norm(d)) < 1e-5 else _norm(d)
    ref = np.array([0.0, 0.0, 1.0]) if abs(by[1]) > 0.7 else np.array([0.0, -1.0, 0.0])
    bx = np.cross(by, ref)
    if float(np.linalg.norm(bx)) < 1e-5:
        bx = np.cross(by, np.array([1.0, 0.0, 0.0]))
    bx = _norm(bx)
    bz = _norm(np.cross(bx, by))
    return np.column_stack([bx, by, bz])


def _tube_mesh(
    pts: np.ndarray,
    rx_list: np.ndarray,
    rz_list: np.ndarray,
    seg: int = 6,
    cap_tip: bool = True,
    base_v: int = 0,
) -> Tuple[np.ndarray, np.ndarray]:
    n_pts = len(pts)
    angs = np.linspace(0.0, 2.0 * math.pi, seg, endpoint=False)
    verts: List[np.ndarray] = []
    t_prev = _norm(pts[1] - pts[0])
    up0 = np.array([0.0, 1.0, 0.0]) if abs(t_prev[1]) < 0.85 else np.array([1.0, 0.0, 0.0])
    n_vec = _norm(np.cross(up0, t_prev))
    for k in range(n_pts):
        if k == 0:
            t_cur = _norm(pts[1] - pts[0])
        elif k == n_pts - 1:
            t_cur = _norm(pts[-1] - pts[-2])
        else:
            t_cur = _norm(pts[k + 1] - pts[k - 1])
        R = _rot_between(t_prev, t_cur)
        n_vec = _norm(R @ n_vec)
        b_vec = _norm(np.cross(t_cur, n_vec))
        t_prev = t_cur
        rx, rz = float(rx_list[k]), float(rz_list[k])
        for a in angs:
            verts.append(pts[k] + (rx * math.cos(a)) * n_vec + (rz * math.sin(a)) * b_vec)
    tris: List[List[int]] = []
    for k in range(n_pts - 1):
        r0, r1 = base_v + k * seg, base_v + (k + 1) * seg
        for j in range(seg):
            jn = (j + 1) % seg
            tris.append([r0 + j, r0 + jn, r1 + jn])
            tris.append([r0 + j, r1 + jn, r1 + j])
    if cap_tip:
        tip_idx = base_v + len(verts)
        verts.append(pts[-1] + _norm(pts[-1] - pts[-2]) * 0.008)
        rl = base_v + (n_pts - 1) * seg
        for j in range(seg):
            jn = (j + 1) % seg
            tris.append([rl + j, rl + jn, tip_idx])
    return np.array(verts, dtype=np.float64), np.array(tris, dtype=np.int32)


class HairStrand:
    def __init__(
        self,
        rest_pts: np.ndarray,
        rx: np.ndarray,
        rz: np.ndarray,
        seg: int,
        phase: float,
        wind_amp: float,
        kind: str,
        tuck_weight: float = 0.0,
    ):
        self.rest_pts = rest_pts
        self.rx = rx
        self.rz = rz
        self.seg = seg
        self.phase = phase
        self.wind_amp = wind_amp
        self.kind = kind
        self.tuck_weight = tuck_weight


class MHRig:
    """Rigged MakeHuman character with draped garments, cohesive hair, and 2-bone IK."""

    def __init__(self, role: str, targets: Dict[str, float], target_height: float):
        self.role = role
        V0, T_body, n_body = load_base_obj()
        sk, W_raw = load_skel_weights()
        V_all = V0.copy()
        for fn, w in targets.items():
            with open(os.path.join(MH_DIR, "t", fn), "r", encoding="utf-8") as f:
                for ln in f:
                    if not ln.strip() or ln.startswith("#"):
                        continue
                    a = ln.split()
                    V_all[int(a[0])] += np.array([float(a[1]), float(a[2]), float(a[3])]) * w
        V_all = np.stack([V_all[:, 0], -V_all[:, 2], V_all[:, 1]], axis=1) * 0.1
        V_all[:, 2] -= float(V_all[:n_body, 2].min())
        V_all *= target_height / float(V_all[:n_body, 2].max())
        self.height = target_height

        # Youthful Boy head-to-shoulder ratio BEFORE extracting rest mesh & bone joints (keep Girl natural slender anatomy)
        if role == "boy":
            w_head = np.clip((V_all[:, 2] - 1.40) / 0.10, 0.0, 1.0)
            piv = np.array([0.0, -0.02, 1.42], dtype=np.float64)
            V_all = piv + (V_all - piv) * (1.0 + 0.10 * w_head[:, None])

        self.V_body_rest = V_all[:n_body].copy()
        self.T_body = _check_outward_winding(self.V_body_rest, T_body)
        if role == "girl":
            # Strip bare skeletal MakeHuman feet/toes (< 0.088 m) so closed shoes completely replace bare toes
            v_foot = self.V_body_rest[:, 2] < 0.088
            keep_tri = ~(v_foot[self.T_body[:, 0]] & v_foot[self.T_body[:, 1]] & v_foot[self.T_body[:, 2]])
            self.T_body = self.T_body[keep_tri]

        bones_raw = sk["bones"]
        self.joints_rest = {k: V_all[v].mean(0) for k, v in sk["joints"].items()}
        self.bone_names: List[str] = []
        visited = set()

        def visit(bn: str):
            if bn in visited:
                return
            if bones_raw[bn]["parent"] is not None:
                visit(bones_raw[bn]["parent"])
            visited.add(bn)
            self.bone_names.append(bn)

        for bn in sorted(bones_raw.keys()):
            visit(bn)
        self.bone_idx = {bn: i for i, bn in enumerate(self.bone_names)}
        self.parents = [self.bone_idx[bones_raw[bn]["parent"]] if bones_raw[bn]["parent"] else -1 for bn in self.bone_names]
        self.heads_rest = np.array([self.joints_rest[bones_raw[bn]["head"]] for bn in self.bone_names], dtype=np.float64)
        self.tails_rest = np.array([self.joints_rest[bones_raw[bn]["tail"]] for bn in self.bone_names], dtype=np.float64)

        self.B_rest: List[np.ndarray] = []
        self.B_rest_inv: List[np.ndarray] = []
        self.B_local_rest: List[np.ndarray] = []
        for i in range(len(self.bone_names)):
            R0 = _bone_frame(self.heads_rest[i], self.tails_rest[i])
            M = np.eye(4, dtype=np.float64)
            M[:3, :3] = R0
            M[:3, 3] = self.heads_rest[i]
            self.B_rest.append(M)
            self.B_rest_inv.append(np.linalg.inv(M))
            pi = self.parents[i]
            self.B_local_rest.append(M.copy() if pi < 0 else self.B_rest_inv[pi] @ M)

        K = 6
        vert_w: List[List[Tuple[int, float]]] = [[] for _ in range(n_body)]
        for bn, lst in W_raw.items():
            bi = self.bone_idx.get(bn)
            if bi is None:
                continue
            for vi, wt in lst:
                if vi < n_body and wt > 1e-5:
                    vert_w[vi].append((bi, float(wt)))
        self.body_bidx, self.body_bwt = self._pack_weights(vert_w, K)

        self.extra_meshes: List[dict] = []
        self.hair_strands: List[HairStrand] = []
        self.skirt_spec: Optional[dict] = None
        self.hair_veil_spec: Optional[dict] = None
        if role == "girl":
            self._build_girl_wardrobe()
            self._build_girl_hair()
        else:
            self._build_boy_wardrobe()
            self._build_boy_hair()

    def _pack_weights(self, vert_w: List[List[Tuple[int, float]]], K: int) -> Tuple[np.ndarray, np.ndarray]:
        n = len(vert_w)
        bidx = np.zeros((n, K), dtype=np.int32)
        bwt = np.zeros((n, K), dtype=np.float64)
        for vi, lst in enumerate(vert_w):
            if not lst:
                bwt[vi, 0] = 1.0
                continue
            lst_sorted = sorted(lst, key=lambda x: -x[1])[:K]
            tot = sum(w for _, w in lst_sorted)
            for j, (bi, w) in enumerate(lst_sorted):
                bidx[vi, j] = bi
                bwt[vi, j] = w / tot
        return bidx, bwt

    def _extract_shell_from_bones(
        self,
        allowed_bones: set,
        offset_fn,
        min_weight: float = 0.55,
        extra_pred=None,
        smooth_iters: int = 0,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        vn = _smooth_vertex_normals(self.V_body_rest, self.T_body)
        allowed_ids = {self.bone_idx[b] for b in allowed_bones if b in self.bone_idx}
        v_ok = np.zeros(len(self.V_body_rest), dtype=bool)
        for vi in range(len(self.V_body_rest)):
            w_sum = sum(
                self.body_bwt[vi, j]
                for j in range(self.body_bidx.shape[1])
                if self.body_bidx[vi, j] in allowed_ids
            )
            if w_sum >= min_weight and (extra_pred is None or extra_pred(self.V_body_rest[vi])):
                v_ok[vi] = True
        tri_ok = v_ok[self.T_body[:, 0]] & v_ok[self.T_body[:, 1]] & v_ok[self.T_body[:, 2]]
        sel_tris = self.T_body[tri_ok]
        used_verts = np.unique(sel_tris)
        remap = np.full(len(self.V_body_rest), -1, dtype=np.int32)
        remap[used_verts] = np.arange(len(used_verts), dtype=np.int32)
        T_out = remap[sel_tris]
        V_out = self.V_body_rest[used_verts].copy()
        N_out = vn[used_verts]
        for idx_local in range(len(used_verts)):
            V_out[idx_local] = offset_fn(V_out[idx_local], N_out[idx_local])
        if smooth_iters > 0:
            V_out = _laplacian_smooth_mesh(V_out, T_out, iters=smooth_iters, lam=0.50)
        return V_out, T_out, self.body_bidx[used_verts], self.body_bwt[used_verts]

    def _build_girl_wardrobe(self):
        # Soft cozy sweater/blouse bodice + sleeves (hides bare MakeHuman clavicles/ribs/elbows while keeping slim waist)
        blouse_bones = {
            "spine05", "spine04", "spine03", "spine02", "spine01",
            "clavicle.L", "clavicle.R", "shoulder01.L", "shoulder01.R",
            "upperarm01.L", "upperarm01.R", "upperarm02.L", "upperarm02.R",
            "lowerarm01.L", "lowerarm01.R", "lowerarm02.L", "lowerarm02.R",
            "breast.L", "breast.R",
        }

        def blouse_offset(p: np.ndarray, n: np.ndarray) -> np.ndarray:
            if abs(p[0]) > 0.185:
                t_arm = min(1.0, max(0.0, (abs(p[0]) - 0.185) / 0.20))
                t_cuff = min(1.0, max(0.0, (0.408 - abs(p[0])) / 0.025))
                drape = (0.016 * (1.0 - t_arm) + 0.012 * t_arm) * t_cuff
                return p + n * drape
            q = p + n * (0.014 if p[2] > 1.12 else 0.010)
            if 1.24 <= q[2] <= 1.38 and abs(q[0]) < 0.16:
                q[1] = min(q[1], -0.075 * math.sqrt(max(0.0, 1.0 - min(1.0, (q[0] / 0.165) ** 2))))
            if q[1] < -0.02 and 1.12 <= q[2] <= 1.35 and abs(q[0]) < 0.14:
                r_x = 0.142
                arc_y = -0.142 * math.sqrt(max(0.0, 1.0 - min(1.0, (q[0] / r_x) ** 2)))
                blend = min(1.0, (q[2] - 1.12) / 0.10)
                q[1] = q[1] * (1.0 - 0.72 * blend) + min(q[1], arc_y) * (0.72 * blend)
            return q

        V_b, T_b, bi_b, bw_b = self._extract_shell_from_bones(
            blouse_bones,
            blouse_offset,
            min_weight=0.50,
            extra_pred=lambda p: 0.94 <= p[2] <= 1.38 and abs(p[0]) <= 0.408,
            smooth_iters=10,
        )
        self.extra_meshes.append(dict(name="girl_blouse", V=V_b, T=T_b, bidx=bi_b, bwt=bw_b))

        # Two dainty closed flat / low bootie shells skinned 100% to foot.L and foot.R (short rounded profile, ZERO bare toes)
        n_rings_s, n_seg_s = 10, 24
        angs_s = np.linspace(0.0, 2.0 * math.pi, n_seg_s, endpoint=False)
        for side, sign_x in (("L", 1.0), ("R", -1.0)):
            ft_idx = self.bone_idx[f"foot.{side}"]
            ft_verts_rest = self.V_body_rest[(self.V_body_rest[:, 2] < 0.095) & (self.V_body_rest[:, 0] * sign_x > 0.05)]
            cx_ft = float(ft_verts_rest[:, 0].mean()) if len(ft_verts_rest) > 0 else sign_x * 0.217
            y_toe = max(-0.156, float(ft_verts_rest[:, 1].min()) + 0.028) if len(ft_verts_rest) > 0 else -0.154
            y_heel = float(ft_verts_rest[:, 1].max()) + 0.002 if len(ft_verts_rest) > 0 else 0.050
            cy_sole = 0.5 * (y_toe + y_heel)
            ry_sole = 0.5 * (y_heel - y_toe)
            rx_sole = 0.041

            verts_s: List[List[float]] = []
            for ri in range(n_rings_s):
                u = ri / (n_rings_s - 1)
                t_cuff = max(0.0, (u - 0.28) / 0.72)
                cuff_blend = t_cuff ** 1.35
                z_base = 0.001 + u * 0.095
                rx = rx_sole * (1.0 - 0.22 * cuff_blend)
                ry = ry_sole * (1.0 - 0.62 * cuff_blend)
                cy = cy_sole * (1.0 - cuff_blend) + 0.004 * cuff_blend
                for th in angs_s:
                    front_fac = max(0.0, -math.sin(th))
                    z_v = z_base - 0.052 * (front_fac ** 1.35) * (u ** 0.85)
                    verts_s.append([cx_ft + rx * math.cos(th), cy + ry * math.sin(th), max(0.000, z_v)])

            tris_s: List[List[int]] = []
            for ri in range(n_rings_s - 1):
                for ti in range(n_seg_s):
                    tn = (ti + 1) % n_seg_s
                    a, b = ri * n_seg_s + ti, ri * n_seg_s + tn
                    c, d = (ri + 1) * n_seg_s + tn, (ri + 1) * n_seg_s + ti
                    tris_s.extend([[a, b, c], [a, c, d]])
            i_bot = len(verts_s)
            verts_s.append([cx_ft, cy_sole, 0.000])
            i_top = len(verts_s)
            verts_s.append([cx_ft, 0.004, 0.088])
            top_ring = (n_rings_s - 1) * n_seg_s
            for ti in range(n_seg_s):
                tn = (ti + 1) % n_seg_s
                tris_s.append([i_bot, tn, ti])
                tris_s.append([i_top, top_ring + ti, top_ring + tn])

            V_sh = np.array(verts_s, dtype=np.float64)
            T_sh = _check_outward_winding(V_sh, np.array(tris_s, dtype=np.int32), center=(cx_ft, cy_sole * 0.5, 0.040))
            bi_sh = np.zeros((len(V_sh), 6), dtype=np.int32)
            bw_sh = np.zeros((len(V_sh), 6), dtype=np.float64)
            bi_sh[:, 0] = ft_idx
            bw_sh[:, 0] = 1.0
            self.extra_meshes.append(dict(name=f"girl_shoe_{side}", V=V_sh, T=T_sh, bidx=bi_sh, bwt=bw_sh))

        # Flowing silk/cotton sundress skirt tucked inside bodice (z=1.05..0.50, organic undulating wind hem!)
        n_rings, n_seg = 18, 64
        s_vals = np.linspace(0.0, 1.0, n_rings)
        thetas = np.linspace(0.0, 2.0 * math.pi, n_seg, endpoint=False)
        z_top, z_bot = 1.05, 0.50
        verts, grid_info = [], []
        for s in s_vals:
            flare = s ** 1.15
            rx = 0.106 + 0.098 * flare
            ry = 0.086 + 0.088 * flare
            cy = -0.032 * (1.0 - s) - 0.026 * s
            fold_amp = s ** 1.05
            for th in thetas:
                z_hem = (
                    z_bot
                    + 0.020 * math.cos(th - 0.5)
                    + 0.010 * math.sin(3.0 * th + 0.8)
                    + 0.005 * math.cos(5.0 * th - 1.2)
                )
                z = z_top * (1.0 - s) + z_hem * s
                fold = (
                    0.013 * math.sin(5.0 * th + 0.4)
                    + 0.008 * math.cos(8.0 * th - 1.1)
                    + 0.004 * math.sin(13.0 * th + 2.0)
                ) * fold_amp
                verts.append([(rx + fold) * math.cos(th), cy + (ry + fold) * math.sin(th), z])
                grid_info.append((s, th))
        tris = []
        for ri in range(n_rings - 1):
            for ti in range(n_seg):
                tn = (ti + 1) % n_seg
                a, b, c, d = ri * n_seg + ti, ri * n_seg + tn, (ri + 1) * n_seg + tn, (ri + 1) * n_seg + ti
                tris.extend([[a, b, c], [a, c, d]])
        V_sk = np.array(verts, dtype=np.float64)
        T_sk = np.array(tris, dtype=np.int32)
        p0, p1, p2 = V_sk[T_sk[:, 0]], V_sk[T_sk[:, 1]], V_sk[T_sk[:, 2]]
        fn = np.cross(p1 - p0, p2 - p0)
        cen = (p0 + p1 + p2) / 3.0
        rad_out = np.stack([cen[:, 0], cen[:, 1] + 0.03, np.zeros(len(cen))], axis=1)
        if float(np.mean(np.sum(fn * rad_out, axis=1) > 0)) < 0.5:
            T_sk = T_sk[:, [0, 2, 1]].copy()

        bi_sk = np.zeros((len(V_sk), 6), dtype=np.int32)
        bw_sk = np.zeros((len(V_sk), 6), dtype=np.float64)
        idx_root, idx_sp5 = self.bone_idx["root"], self.bone_idx["spine05"]
        for i, (s, _) in enumerate(grid_info):
            w_sp = max(0.25, 1.0 - s * 0.65)
            bi_sk[i, 0], bi_sk[i, 1] = idx_sp5, idx_root
            bw_sk[i, 0], bw_sk[i, 1] = w_sp, 1.0 - w_sp
        self.skirt_spec = dict(
            V=V_sk, T=T_sk, bidx=bi_sk, bwt=bw_sk,
            s=np.array([g[0] for g in grid_info]), th=np.array([g[1] for g in grid_info]),
        )

    def _build_boy_wardrobe(self):
        # Cozy loose oversized jacket: thick relaxed shoulder padding, raised collar, deep diagonal back folds
        jacket_bones = {
            "neck01", "spine05", "spine04", "spine03", "spine02", "spine01",
            "clavicle.L", "clavicle.R", "shoulder01.L", "shoulder01.R",
            "upperarm01.L", "upperarm01.R", "upperarm02.L", "upperarm02.R",
            "lowerarm01.L", "lowerarm01.R", "lowerarm02.L", "lowerarm02.R",
            "pelvis.L", "pelvis.R",
        }

        def boy_jacket_offset(p: np.ndarray, n: np.ndarray) -> np.ndarray:
            if abs(p[0]) > 0.195:
                t_arm = min(1.0, max(0.0, (abs(p[0]) - 0.195) / 0.24))
                crease = 0.010 * math.sin(abs(p[0]) * 42.0 + p[1] * 28.0) * math.sin(t_arm * math.pi)
                drape = 0.042 * (1.0 - t_arm) + 0.018 * t_arm + max(0.0, crease)
                return p + n * drape
            collar = 0.0
            if 1.33 <= p[2] <= 1.46 and abs(p[0]) < 0.145:
                c_t = max(0.0, (p[2] - 1.33) / 0.12)
                collar = 0.026 * c_t
            drape = 0.044 + 0.016 * max(0.0, 1.32 - p[2]) + collar
            if p[1] > -0.02 and 0.68 < p[2] < 1.39:
                diag1 = 0.016 * math.sin(p[2] * 25.0 + p[0] * 21.0 + 0.4)
                diag2 = 0.010 * math.cos(p[2] * 40.0 - p[0] * 17.0)
                drape += max(0.0, diag1 + diag2 * 0.6)
            q = p + n * drape
            if 1.35 <= p[2] <= 1.46 and abs(p[0]) < 0.12:
                q[2] += 0.018
            if q[1] > 0.0 and 0.68 <= q[2] <= 1.38 and abs(q[0]) < 0.20:
                q[1] = max(q[1], 0.114 * math.sqrt(max(0.0, 1.0 - min(1.0, (q[0] / 0.21) ** 2))))
            if q[1] < -0.02 and 0.72 < q[2] < 1.39 and abs(q[0]) < 0.20:
                r_x = 0.195
                arc_y = -0.190 * math.sqrt(max(0.0, 1.0 - min(1.0, (q[0] / r_x) ** 2)))
                q[1] = min(q[1], arc_y)
            return q

        V_j, T_j, bi_j, bw_j = self._extract_shell_from_bones(
            jacket_bones,
            boy_jacket_offset,
            min_weight=0.45,
            extra_pred=lambda p: 0.68 <= p[2] <= 1.45 and abs(p[0]) <= 0.445,
            smooth_iters=4,
        )
        self.extra_meshes.append(dict(name="boy_jacket", V=V_j, T=T_j, bidx=bi_j, bwt=bw_j))

        pants_bones = {
            "pelvis.L", "pelvis.R", "upperleg01.L", "upperleg01.R",
            "upperleg02.L", "upperleg02.R", "lowerleg01.L", "lowerleg01.R",
            "lowerleg02.L", "lowerleg02.R",
        }
        V_p, T_p, bi_p, bw_p = self._extract_shell_from_bones(
            pants_bones,
            lambda p, n: p + n * (0.024 + 0.008 * max(0.0, 0.9 - p[2])),
            min_weight=0.60,
            extra_pred=lambda p: 0.10 <= p[2] <= 0.92,
            smooth_iters=3,
        )
        self.extra_meshes.append(dict(name="boy_pants", V=V_p, T=T_p, bidx=bi_p, bwt=bw_p))

    def _build_girl_hair(self):
        V_cap, T_cap, bi_c, bw_c = self._extract_shell_from_bones(
            {"head", "neck03"},
            lambda p, n: p + n * 0.013,
            min_weight=0.52,
            extra_pred=lambda p: p[2] > 1.53 or (p[2] > 1.43 and p[1] > -0.092),
        )
        self.extra_meshes.append(dict(name="girl_hair_cap", V=V_cap, T=T_cap, bidx=bi_c, bwt=bw_c))

        # Full seamless cascading veil emerging tangent to rounded crown (ZERO top ear-horn bumps!)
        n_rows, n_cols = 20, 32
        s_vals = np.linspace(0.0, 1.0, n_rows)
        ang_vals = np.linspace(math.radians(-138.0), math.radians(138.0), n_cols)
        v_veil, veil_info = [], []
        for s in s_vals:
            length = 0.48 * (1.0 - 0.16 * (ang_vals / math.radians(138.0)) ** 2)
            for ci, ang in enumerate(ang_vals):
                r_arc = 0.056 + 0.068 * math.sin(min(1.0, s * 1.45) * math.pi * 0.5)
                x = r_arc * math.sin(ang) * 0.98
                y = -0.052 + r_arc * math.cos(ang) * 0.92 + 0.034 * (s ** 0.78)
                z = 1.608 - 0.026 * abs(math.sin(ang)) - length[ci] * s
                wave_r = 0.004 * math.sin(ang * 5.0 + s * 4.0)
                v_veil.append([x + wave_r * math.sin(ang), y + wave_r * math.cos(ang), z])
                veil_info.append((s, ang))
        t_veil = []
        for ri in range(n_rows - 1):
            for ci in range(n_cols - 1):
                a = ri * n_cols + ci
                b, c, d = a + 1, a + n_cols + 1, a + n_cols
                t_veil.extend([[a, b, c], [a, c, d], [a, c, b], [a, d, c]])
        self.hair_veil_spec = dict(
            V=np.array(v_veil, dtype=np.float64),
            T=np.array(t_veil, dtype=np.int32),
            s=np.array([g[0] for g in veil_info]),
            ang=np.array([g[1] for g in veil_info]),
        )

        # Soft silky trailing outer locks starting flush inside crown & cascading smoothly (no ear-horns)
        rng = np.random.default_rng(101)
        strand_defs = []
        for i in range(14):
            u = i / 13.0
            ang = math.radians(-116.0 + u * 232.0)
            x0, y0, z0 = 0.064 * math.sin(ang), -0.050 + 0.064 * math.cos(ang), 1.568 - 0.022 * abs(math.sin(ang))
            length = 0.42 - 0.07 * (ang / math.radians(116.0)) ** 2 + float(rng.uniform(-0.02, 0.03))
            pts = []
            n_s = 14
            for k in range(n_s):
                t = k / (n_s - 1)
                pts.append([
                    x0 * (1.0 + 0.36 * math.sin(min(1.0, t * 1.4) * math.pi * 0.5)) + 0.008 * math.sin(t * 3.0 + i * 0.6) * t,
                    y0 + (0.042 + 0.018 * math.cos(ang)) * (t ** 0.80) + 0.004 * math.cos(t * 3.5 + i) * t,
                    z0 - length * t,
                ])
            strand_defs.append(
                HairStrand(
                    np.array(pts), np.linspace(0.017, 0.0050, n_s), np.linspace(0.011, 0.0035, n_s),
                    seg=6, phase=i * 0.35, wind_amp=0.82, kind="girl_back",
                )
            )
        for i in range(4):
            side_s = -1.0 if i < 2 else 1.0
            t_off = float(i % 2)
            x0 = side_s * (0.062 + 0.005 * t_off)
            y0 = -0.084 + 0.016 * t_off
            z0 = 1.562 - 0.010 * t_off
            pts = []
            n_s = 12
            for k in range(n_s):
                t = k / (n_s - 1)
                pts.append([
                    x0 - side_s * 0.014 * (t ** 1.15),
                    y0 + 0.026 * (t ** 1.1),
                    z0 - (0.22 + 0.05 * t_off) * t,
                ])
            strand_defs.append(
                HairStrand(
                    np.array(pts), np.linspace(0.013, 0.0042, n_s), np.linspace(0.008, 0.0030, n_s),
                    seg=6, phase=1.8 + i * 0.45, wind_amp=0.45, kind="girl_side",
                )
            )
        self.hair_strands = strand_defs

    def _build_boy_hair(self):
        # Measure actual scaled skull center so tapered cap & surface-sampled curls never bury inside skull
        head_v = self.V_body_rest[self.V_body_rest[:, 2] > 1.50]
        hx = float(head_v[:, 0].mean())
        hy = float(head_v[head_v[:, 2] > 1.58, 1].mean())
        hz_top = float(head_v[:, 2].max())
        hz_cen = hz_top - 0.112

        def _boy_hair_keep(p: np.ndarray) -> bool:
            in_face_oval = (p[1] < hy - 0.032) and (p[2] < hz_cen + 0.048) and (abs(p[0] - hx) < 0.064)
            return (p[2] > hz_cen - 0.045) and not in_face_oval

        def _boy_cap_offset(p: np.ndarray, n: np.ndarray) -> np.ndarray:
            t_nape = max(0.0, min(1.0, (p[2] - (hz_cen - 0.045)) / 0.038))
            off = (0.018 + 0.005 * math.sin(p[0] * 38.0) * math.cos(p[1] * 38.0)) * t_nape
            return p + n * off

        V_cap, T_cap, bi_c, bw_c = self._extract_shell_from_bones(
            {"head", "neck03"},
            _boy_cap_offset,
            min_weight=0.46,
            extra_pred=_boy_hair_keep,
            smooth_iters=0,
        )
        self.extra_meshes.append(dict(name="boy_hair_cap", V=V_cap, T=T_cap, bidx=bi_c, bwt=bw_c))

        # Sample 80 evenly spaced curl roots directly ON the evaluated boy_hair_cap surface (100% flush!)
        N_cap = _smooth_vertex_normals(V_cap, T_cap)
        cand_idx = [
            vi for vi, p in enumerate(V_cap)
            if p[2] > hz_cen - 0.035 and not (p[1] < hy - 0.015 and p[2] < hz_cen + 0.055)
        ]
        rng = np.random.default_rng(202)
        perm = rng.permutation(len(cand_idx))
        selected: List[np.ndarray] = []
        strand_defs = []
        min_d2 = 0.024 * 0.024
        for idx_p in perm:
            vi = cand_idx[int(idx_p)]
            p_cand = V_cap[vi]
            if any(float(np.sum((p_cand - p_sel) ** 2)) < min_d2 for p_sel in selected):
                continue
            selected.append(p_cand)
            n_loc = N_cap[vi]
            out_h = _norm(n_loc + np.array([0.0, 0.0, 0.25]))
            p0 = p_cand + n_loc * 0.002
            curl_reach = 0.012 + 0.008 * float(rng.uniform(0.0, 1.0))
            length = 0.038 + 0.020 * float(rng.uniform(0.0, 1.0))
            pts = []
            n_s = 7
            k_f = len(strand_defs)
            for k in range(n_s):
                t = k / (n_s - 1)
                arch = math.sin(t * math.pi) * curl_reach
                curl_w = 0.008 * math.sin(t * 4.2 + k_f * 1.1)
                pts.append(
                    p0
                    + out_h * (arch + curl_reach * 0.42 * t)
                    + np.array([curl_w, 0.006 * math.cos(t * 3.4 + k_f), -length * (t ** 1.05)])
                )
            strand_defs.append(
                HairStrand(
                    np.array(pts), np.linspace(0.017, 0.007, n_s), np.linspace(0.014, 0.006, n_s),
                    seg=6, phase=k_f * 0.45, wind_amp=0.22, kind="boy_curl",
                )
            )
            if len(strand_defs) >= 80:
                break
        self.hair_strands = strand_defs

    def compute_bone_world(
        self,
        rots_deg: Optional[Dict[str, Tuple[float, float, float]]] = None,
        rot_mats: Optional[Dict[str, np.ndarray]] = None,
        root_pos: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        root_yaw_deg: float = 0.0,
    ) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        rots_deg = rots_deg or {}
        rot_mats = rot_mats or {}
        T_root = np.eye(4, dtype=np.float64)
        T_root[:3, :3] = _euler_xyz_deg(0.0, 0.0, root_yaw_deg)
        T_root[:3, 3] = np.array(root_pos, dtype=np.float64)

        B_pose: List[np.ndarray] = [None] * len(self.bone_names)  # type: ignore
        M_skin: List[np.ndarray] = [None] * len(self.bone_names)  # type: ignore
        for i, bn in enumerate(self.bone_names):
            pi = self.parents[i]
            parent_M = T_root if pi < 0 else B_pose[pi]
            M_loc = np.eye(4, dtype=np.float64)
            if bn in rot_mats:
                M_loc[:3, :3] = rot_mats[bn]
            elif bn in rots_deg:
                M_loc[:3, :3] = _euler_xyz_deg(*rots_deg[bn])
            B_pose[i] = parent_M @ self.B_local_rest[i] @ M_loc
            M_skin[i] = B_pose[i] @ self.B_rest_inv[i]
        return B_pose, M_skin

    def _solve_two_bone_ik(
        self,
        upper_name: str,
        lower_name: str,
        end_name: str,
        clear_names: Tuple[str, ...],
        target_world: np.ndarray,
        pole_world: np.ndarray,
        rots_deg: Dict[str, Tuple[float, float, float]],
        rot_mats: Dict[str, np.ndarray],
        root_pos: Tuple[float, float, float],
        root_yaw_deg: float,
    ) -> float:
        for k in clear_names:
            rot_mats.pop(k, None)

        B_pose, _ = self.compute_bone_world(rots_deg, rot_mats, root_pos, root_yaw_deg)
        iu, il, ie = self.bone_idx[upper_name], self.bone_idx[lower_name], self.bone_idx[end_name]
        S, M0, E0 = B_pose[iu][:3, 3], B_pose[il][:3, 3], B_pose[ie][:3, 3]
        v1 = M0 - S
        L1, L2 = float(np.linalg.norm(v1)), float(np.linalg.norm(E0 - M0))

        D = target_world - S
        d_clamped = float(np.clip(float(np.linalg.norm(D)), abs(L1 - L2) + 1e-4, L1 + L2 - 1e-4))
        e_d = _norm(D)
        pole_d = pole_world - S
        pole_perp = pole_d - float(np.dot(pole_d, e_d)) * e_d
        if float(np.linalg.norm(pole_perp)) < 1e-5:
            pole_perp = np.array([0.0, -1.0, 0.0])
        pole_perp = _norm(pole_perp)

        cos_a = float(np.clip((L1 * L1 + d_clamped * d_clamped - L2 * L2) / (2.0 * L1 * d_clamped), -1.0, 1.0))
        sin_a = math.sqrt(max(0.0, 1.0 - cos_a * cos_a))
        M_tar = S + (L1 * cos_a) * e_d + (L1 * sin_a) * pole_perp
        E_reach = S + d_clamped * e_d

        R_parent_up = B_pose[self.parents[iu]][:3, :3] @ self.B_local_rest[iu][:3, :3]
        rot_mats[upper_name] = R_parent_up.T @ (_rot_between(v1, M_tar - S) @ R_parent_up)

        B_pose2, _ = self.compute_bone_world(rots_deg, rot_mats, root_pos, root_yaw_deg)
        M2, E2 = B_pose2[il][:3, 3], B_pose2[ie][:3, 3]
        R_parent_lo = B_pose2[self.parents[il]][:3, :3] @ self.B_local_rest[il][:3, :3]
        rot_mats[lower_name] = R_parent_lo.T @ (_rot_between(E2 - M2, E_reach - M2) @ R_parent_lo)

        B_fin, _ = self.compute_bone_world(rots_deg, rot_mats, root_pos, root_yaw_deg)
        return float(np.linalg.norm(B_fin[ie][:3, 3] - target_world)) * 100.0

    def solve_arm_ik(
        self,
        side: str,
        target_world: np.ndarray,
        pole_world: np.ndarray,
        rots_deg: Dict[str, Tuple[float, float, float]],
        rot_mats: Dict[str, np.ndarray],
        root_pos: Tuple[float, float, float],
        root_yaw_deg: float,
    ) -> float:
        up_n, lo_n, wr_n = f"upperarm01.{side}", f"lowerarm01.{side}", f"wrist.{side}"
        return self._solve_two_bone_ik(
            up_n, lo_n, wr_n,
            (up_n, lo_n, f"upperarm02.{side}", f"lowerarm02.{side}"),
            target_world, pole_world, rots_deg, rot_mats, root_pos, root_yaw_deg,
        )

    def solve_leg_ik(
        self,
        side: str,
        target_ankle_world: np.ndarray,
        pole_world: np.ndarray,
        foot_yaw_deg: float,
        rots_deg: Dict[str, Tuple[float, float, float]],
        rot_mats: Dict[str, np.ndarray],
        root_pos: Tuple[float, float, float],
        root_yaw_deg: float,
    ) -> float:
        up_n, lo_n, ft_n = f"upperleg01.{side}", f"lowerleg01.{side}", f"foot.{side}"
        err_cm = self._solve_two_bone_ik(
            up_n, lo_n, ft_n,
            (up_n, lo_n, f"upperleg02.{side}", f"lowerleg02.{side}", ft_n),
            target_ankle_world, pole_world, rots_deg, rot_mats, root_pos, root_yaw_deg,
        )
        # Level foot sole horizontally at desired world yaw (eliminates MakeHuman splayed duck ankle roll)
        ift = self.bone_idx[ft_n]
        B_pose2, _ = self.compute_bone_world(rots_deg, rot_mats, root_pos, root_yaw_deg)
        R_parent_ft = B_pose2[self.parents[ift]][:3, :3] @ self.B_local_rest[ift][:3, :3]
        R_ft_desired_world = _euler_xyz_deg(0.0, 0.0, foot_yaw_deg) @ self.B_rest[ift][:3, :3]
        rot_mats[ft_n] = R_parent_ft.T @ R_ft_desired_world
        return err_cm

    def pose_all(
        self,
        rots_deg: Dict[str, Tuple[float, float, float]],
        rot_mats: Dict[str, np.ndarray],
        root_pos: Tuple[float, float, float],
        root_yaw_deg: float,
        phi: float = 0.0,
        wind_swell: float = 1.0,
        ground_feet: bool = False,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
        B_pose, M_skin = self.compute_bone_world(rots_deg, rot_mats, root_pos, root_yaw_deg)
        M_arr = np.stack(M_skin, axis=0)

        def skin_verts(V_rest: np.ndarray, bidx: np.ndarray, bwt: np.ndarray) -> np.ndarray:
            Vh = np.concatenate([V_rest, np.ones((len(V_rest), 1), dtype=np.float64)], axis=1)
            V_out = np.zeros((len(V_rest), 3), dtype=np.float64)
            for j in range(bidx.shape[1]):
                w = bwt[:, j : j + 1]
                if float(w.max()) < 1e-6:
                    continue
                V_out += w * np.einsum("nij,nj->ni", M_arr[bidx[:, j], :3, :], Vh)
            return V_out

        V_body = skin_verts(self.V_body_rest, self.body_bidx, self.body_bwt)
        z_offset = -float(V_body[:, 2].min()) if ground_feet else 0.0
        if z_offset != 0.0:
            V_body[:, 2] += z_offset

        verts_parts = [V_body]
        tris_parts = [self.T_body]
        v_off = len(V_body)

        for em in self.extra_meshes:
            Ve = skin_verts(em["V"], em["bidx"], em["bwt"])
            if z_offset != 0.0:
                Ve[:, 2] += z_offset
            verts_parts.append(Ve)
            tris_parts.append(em["T"] + v_off)
            v_off += len(Ve)

        if self.skirt_spec is not None:
            sk = self.skirt_spec
            Vs = skin_verts(sk["V"], sk["bidx"], sk["bwt"])
            if z_offset != 0.0:
                Vs[:, 2] += z_offset
            s, th = sk["s"], sk["th"]
            gust = 0.60 + 0.42 * wind_swell
            # Asymmetric organic sundress wind billow (softly ripples hem up & right, ZERO straight ruler line!)
            swell_hem = np.clip(0.50 + 0.50 * np.cos(th - 0.30), 0.0, 1.0)
            wave_x = np.sin(2.0 * phi - 2.0 * th - 3.2 * s) * 0.016 + np.cos(3.0 * phi + 2.6 * th - 4.0 * s) * 0.009
            wave_z = np.sin(2.0 * phi - 1.8 * th - 2.5 * s) * 0.012
            Vs[:, 0] += ((0.018 + 0.052 * swell_hem) * gust + wave_x) * (s ** 1.55)
            Vs[:, 1] += (0.014 * np.sin(phi - th) + 0.014 * np.sin(th) * gust) * (s ** 1.45)
            Vs[:, 2] += ((0.006 + 0.042 * swell_hem) * gust + wave_z) * (s ** 1.55)
            verts_parts.append(Vs)
            tris_parts.append(sk["T"] + v_off)
            v_off += len(Vs)

        i_head = self.bone_idx["head"]
        M_head = M_arr[i_head]
        if self.hair_veil_spec is not None:
            hv = self.hair_veil_spec
            Vh_h = np.concatenate([hv["V"], np.ones((len(hv["V"]), 1), dtype=np.float64)], axis=1)
            Vv = (M_head[:3, :] @ Vh_h.T).T
            if z_offset != 0.0:
                Vv[:, 2] += z_offset
            s, ang = hv["s"], hv["ang"]
            gust = 0.50 + 0.45 * wind_swell
            # Gravity-first silky curve lifting softly only toward tips (zero stiff wing flare)
            Vv[:, 0] += (0.042 * gust + 0.018 * np.sin(2.0 * phi - s * 3.2 + ang)) * (s ** 1.70)
            Vv[:, 1] += 0.010 * np.cos(2.0 * phi - s * 3.0 + ang) * (s ** 1.55)
            Vv[:, 2] += 0.006 * np.sin(3.0 * phi - s * 3.8 + ang) * (s ** 1.60)
            verts_parts.append(Vv)
            tris_parts.append(hv["T"] + v_off)
            v_off += len(Vv)

        for st in self.hair_strands:
            n_pts = len(st.rest_pts)
            pts_h = np.concatenate([st.rest_pts, np.ones((n_pts, 1), dtype=np.float64)], axis=1)
            pts_w = (M_head[:3, :] @ pts_h.T).T
            if z_offset != 0.0:
                pts_w[:, 2] += z_offset
            s = np.linspace(0.0, 1.0, n_pts)
            if st.kind.startswith("girl"):
                gust = 0.50 + 0.45 * wind_swell
                pts_w[:, 0] += (
                    (0.048 * gust + 0.022 * np.sin(2.0 * phi - s * 3.2 + st.phase)) * (s ** 1.75) * st.wind_amp
                    + 0.008 * np.sin(4.0 * phi - s * 5.0 + st.phase) * (s ** 1.8)
                )
                pts_w[:, 1] += 0.012 * np.cos(2.0 * phi - s * 3.0 + st.phase) * (s ** 1.6) * st.wind_amp
                pts_w[:, 2] += 0.006 * np.sin(3.0 * phi - s * 4.0 + st.phase) * (s ** 1.6) * st.wind_amp
            else:
                pts_w[:, 0] += (0.006 + 0.005 * np.sin(2.0 * phi + st.phase - s * 2.2)) * (s ** 1.4) * st.wind_amp
                pts_w[:, 2] += 0.003 * np.cos(3.0 * phi + st.phase) * (s ** 1.4) * st.wind_amp
            V_st, T_st = _tube_mesh(pts_w, st.rx, st.rz, seg=st.seg, cap_tip=True, base_v=v_off)
            verts_parts.append(V_st)
            tris_parts.append(T_st)
            v_off += len(V_st)

        V_all = np.concatenate(verts_parts, axis=0)
        T_all = np.concatenate(tris_parts, axis=0)
        N_all = _smooth_vertex_normals(V_all, T_all)

        wrist_r_w = B_pose[self.bone_idx["wrist.R"]][:3, 3].copy()
        wrist_l_w = B_pose[self.bone_idx["wrist.L"]][:3, 3].copy()
        head_w = B_pose[i_head][:3, 3].copy()
        chest_w = B_pose[self.bone_idx["spine02"]][:3, 3].copy()
        for p in (wrist_r_w, wrist_l_w, head_w, chest_w):
            p[2] += z_offset
        diag = dict(
            foot_z_cm=float(V_body[:, 2].min()) * 100.0,
            head_top_m=float(V_body[:, 2].max()),
            wrist_R=wrist_r_w,
            wrist_L=wrist_l_w,
            head_pos=head_w,
            chest_pos=chest_w,
        )
        return V_all, T_all, N_all, diag


def make_camera(
    cam_pos: Tuple[float, float, float] = (0.0, -5.20, 1.15),
    target: Tuple[float, float, float] = (0.03, 0.12, 1.56),
    lens_mm: float = 44.0,
    sensor_h_mm: float = 36.0,
    width: int = 1080,
    height: int = 1920,
) -> dict:
    pos = np.array(cam_pos, dtype=np.float64)
    tar = np.array(target, dtype=np.float64)
    fwd = _norm(tar - pos)
    right = _norm(np.cross(fwd, np.array([0.0, 0.0, 1.0])))
    up = _norm(np.cross(right, fwd))
    fy = height * (lens_mm / sensor_h_mm)
    return dict(pos=pos, fwd=fwd, right=right, up=up, fx=fy, fy=fy, cx=width * 0.5, cy=height * 0.5, w=width, h=height)


def project_points(cam: dict, pts: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    rel = pts - cam["pos"]
    x_c, y_c, z_c = rel @ cam["right"], rel @ cam["up"], rel @ cam["fwd"]
    z_safe = np.maximum(z_c, 0.05)
    return np.stack([cam["cx"] + cam["fx"] * (x_c / z_safe), cam["cy"] - cam["fy"] * (y_c / z_safe)], axis=1), z_c


def render_character_pass(
    V: np.ndarray,
    T: np.ndarray,
    N: np.ndarray,
    cam: dict,
    mode: str,
    light_center: np.ndarray,
    ssaa: int = 2,
) -> Image.Image:
    uv, depth = project_points(cam, V)
    p0, p1, p2 = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    fn = np.cross(p1 - p0, p2 - p0)
    tri_c = (p0 + p1 + p2) / 3.0
    view_dir = cam["pos"] - tri_c
    front_mask = (np.sum(fn * view_dir, axis=1) > 0.0) & (depth[T[:, 0]] > 0.2) & (depth[T[:, 1]] > 0.2) & (depth[T[:, 2]] > 0.2)
    Tf = T[front_mask]
    if len(Tf) == 0:
        return Image.new("RGBA", (cam["w"], cam["h"]), (0, 0, 0, 0))

    tri_cf = tri_c[front_mask]
    order = np.argsort(-np.sum((tri_cf - cam["pos"]) * cam["fwd"], axis=1))
    Tf, tri_cf = Tf[order], tri_cf[order]

    tn = N[Tf[:, 0]] + N[Tf[:, 1]] + N[Tf[:, 2]]
    tn /= np.maximum(np.linalg.norm(tn, axis=1, keepdims=True), 1e-8)

    vd = cam["pos"] - tri_cf
    vd /= np.maximum(np.linalg.norm(vd, axis=1, keepdims=True), 1e-8)
    ndotv = np.clip(np.sum(tn * vd, axis=1), 0.0, 1.0)
    fresnel = np.power(1.0 - ndotv, 1.65)

    if mode == "girl":
        l_soft = _norm(np.array([0.45, -0.70, 0.55], dtype=np.float64))
        ndotl_soft = np.clip(0.50 + 0.50 * (tn @ l_soft), 0.0, 1.0)
        R = np.full(len(Tf), 255, dtype=np.uint8)
        G = np.clip(ndotl_soft * 255.0, 0, 255).astype(np.uint8)
        B = np.clip(fresnel * 255.0, 0, 255).astype(np.uint8)
    else:
        eff_light = light_center + np.array([0.08, -0.10, 0.12], dtype=np.float64)
        lv = eff_light - tri_cf
        lv /= np.maximum(np.linalg.norm(lv, axis=1, keepdims=True), 1e-8)
        raw_nl = np.sum(tn * lv, axis=1)
        # Self-shadowing left-to-right Chiaroscuro across jacket back: far-left stays velvet shadow; right folds glow!
        height_mask = np.clip((tri_cf[:, 2] - 0.44) / 0.24, 0.0, 1.0)
        x_wrap = np.clip((tri_cf[:, 0] - (-0.34)) / 0.24, 0.0, 1.0)
        lit = np.power(np.clip(raw_nl * 0.85 + 0.22, 0.0, 1.0), 1.25) * height_mask * (0.12 + 0.88 * x_wrap)
        rim = np.power(1.0 - ndotv, 1.45) * np.clip(raw_nl + 0.35, 0.0, 1.0) * height_mask * (0.15 + 0.85 * x_wrap)
        vol = np.clip(0.5 + 0.5 * (tn @ _norm(np.array([0.35, -0.75, 0.45]))), 0.0, 1.0)
        R = np.clip(lit * 255.0, 0, 255).astype(np.uint8)
        G = np.clip(rim * 255.0, 0, 255).astype(np.uint8)
        B = np.clip(vol * 255.0, 0, 255).astype(np.uint8)

    uv_used = uv[Tf.ravel()]
    pad = 8
    x0 = max(0, int(math.floor(float(uv_used[:, 0].min()))) - pad)
    y0 = max(0, int(math.floor(float(uv_used[:, 1].min()))) - pad)
    x1 = min(cam["w"], int(math.ceil(float(uv_used[:, 0].max()))) + pad)
    y1 = min(cam["h"], int(math.ceil(float(uv_used[:, 1].max()))) + pad)
    rw, rh = x1 - x0, y1 - y0
    if rw <= 0 or rh <= 0:
        return Image.new("RGBA", (cam["w"], cam["h"]), (0, 0, 0, 0))

    im_hi = Image.new("RGBA", (rw * ssaa, rh * ssaa), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im_hi)
    tri_xy = ((uv - np.array([x0, y0], dtype=np.float64)) * ssaa)[Tf]
    for pts_tri, (rc, gc, bc) in zip(tri_xy.tolist(), zip(R.tolist(), G.tolist(), B.tolist())):
        dr.polygon(
            [(pts_tri[0][0], pts_tri[0][1]), (pts_tri[1][0], pts_tri[1][1]), (pts_tri[2][0], pts_tri[2][1])],
            fill=(rc, gc, bc, 255),
        )
    im_roi = im_hi.resize((rw, rh), Image.Resampling.LANCZOS)

    arr = np.asarray(im_roi, dtype=np.float32) / 255.0
    a = arr[..., 3:4]
    sig = max(2.0, 3.0 * (cam["h"] / 1920.0))
    num = gauss_blur_f32(arr[..., :3] * a, sig)
    den = np.maximum(gauss_blur_f32(a, sig), 1e-4)
    smooth_rgb = np.clip(num / den, 0.0, 1.0)
    # Alpha-normalized smoothing turns flat triangle facets into continuous painterly chiaroscuro
    arr[..., 0] = smooth_rgb[..., 0]
    arr[..., 1] = 0.45 * arr[..., 1] + 0.55 * smooth_rgb[..., 1]
    arr[..., 2] = smooth_rgb[..., 2]
    im_roi = Image.fromarray((np.clip(arr, 0, 1) * 255.0 + 0.5).astype(np.uint8), mode="RGBA")

    out = Image.new("RGBA", (cam["w"], cam["h"]), (0, 0, 0, 0))
    out.paste(im_roi, (x0, y0))
    return out


def curl_hand_fingers(rots_deg: Dict[str, Tuple[float, float, float]], side: str, amount: float = 1.0):
    s_sign = 1.0 if side == "L" else -1.0
    for fi, base_ang in [(1, 22.0), (2, 48.0), (3, 52.0), (4, 54.0), (5, 56.0)]:
        for j in (1, 2, 3):
            bn = f"finger{fi}-{j}.{side}"
            rots_deg[bn] = (
                (base_ang * amount * 0.6, 0.0, s_sign * 14.0 * amount) if fi == 1
                else (base_ang * amount * (0.85 if j == 1 else 0.95), 0.0, 0.0)
            )


def build_cast() -> Tuple[MHRig, MHRig]:
    girl = MHRig(
        role="girl",
        targets={
            "universal-female-young-minmuscle-minweight.target": 1.0,
            "head-fat-decr.target": 0.40,
            "nose-point-width-decr.target": 0.35,
        },
        target_height=1.62,
    )
    boy = MHRig(
        role="boy",
        targets={
            "universal-male-young-averagemuscle-minweight.target": 1.0,
            "male-young-averagemuscle-averageweight-idealproportions.target": 0.45,
            "head-fat-decr.target": 0.35,
            "chin-prominent-incr.target": 0.35,
        },
        target_height=1.70,
    )
    return girl, boy


def pose_couple_frame(
    girl: MHRig,
    boy: MHRig,
    f: int,
    n_frames: int = 240,
) -> Tuple[Tuple[np.ndarray, np.ndarray, np.ndarray, dict], Tuple[np.ndarray, np.ndarray, np.ndarray, dict], dict]:
    fpose = f - ((f - 1) % 2)
    phi = 2.0 * math.pi * (fpose - 1) / float(n_frames)
    t_norm = (fpose - 1) / float(n_frames)
    wind_swell = 0.50 + 0.35 * math.sin(2.0 * phi - 0.6) + 0.15 * math.cos(phi + 0.4)

    # Smooth periodic gaze curve: softly toward Boy -> gentle lift toward shooting star/sky -> back to Boy
    gaze_u = float(np.clip((t_norm - 0.20) / 0.48, 0.0, 1.0))
    gaze_up = math.sin(math.pi * gaze_u) ** 1.4

    # --- GIRL (natural contrapposto standing right of center, feet straight via leg IK, ZERO head-scratch!) ---
    g_root_pos = (0.27 + 0.005 * math.sin(phi), 0.18, 0.0)
    g_root_yaw = -30.0 + 1.5 * math.sin(phi)
    g_rots: Dict[str, Tuple[float, float, float]] = {
        "spine05": (2.5 + 1.4 * math.sin(phi), 0.0, 2.0 + 1.2 * math.cos(phi)),
        "spine03": (3.0, 0.0, 1.5 - 1.0 * math.cos(phi)),
        "spine01": (2.5, 0.0, 1.5),
        "neck01": (5.0 - 3.5 * gaze_up, -3.0 + 3.0 * gaze_up, 2.0),
        "head": (13.0 - 11.0 * gaze_up + 1.5 * math.sin(phi), -10.0 + 11.0 * gaze_up, 4.0 - 2.5 * gaze_up),
        "wrist.R": (4.0, 18.0, -6.0),
        "wrist.L": (4.0, -10.0, 6.0),
    }
    curl_hand_fingers(g_rots, "R", 0.55)
    curl_hand_fingers(g_rots, "L", 0.30)
    g_rmats: Dict[str, np.ndarray] = {}

    # Solve 2-bone leg IK in Girl's yaw frame for natural relaxed contrapposto legs + flat level feet
    R_gyaw = _euler_xyz_deg(0.0, 0.0, g_root_yaw)
    g_rp = np.array(g_root_pos, dtype=np.float64)
    err_leg_R = girl.solve_leg_ik(
        "R",
        g_rp + R_gyaw @ np.array([-0.072, -0.006, 0.072]),
        g_rp + R_gyaw @ np.array([-0.072, -0.50, 0.44]),
        g_root_yaw - 3.0,
        g_rots, g_rmats, g_root_pos, g_root_yaw,
    )
    err_leg_L = girl.solve_leg_ik(
        "L",
        g_rp + R_gyaw @ np.array([0.072, -0.016, 0.072]),
        g_rp + R_gyaw @ np.array([0.074, -0.52, 0.44]),
        g_root_yaw + 4.0,
        g_rots, g_rmats, g_root_pos, g_root_yaw,
    )

    # Relaxed hanging left arm softly by her skirt edge (gentle natural hang, ZERO sharp chicken-wing bend!)
    g_target_L = np.array([0.435 + 0.010 * math.sin(phi - 0.8), 0.110, 0.875 + 0.008 * math.cos(phi)])
    g_pole_L = np.array([0.465, 0.24, 1.08])
    err_gL = girl.solve_arm_ik("L", g_target_L, g_pole_L, g_rots, g_rmats, g_root_pos, g_root_yaw)

    # Relaxed lowered right arm in open gap beside hip/waist so Boy's hand clasps clearly
    g_target_R = np.array([0.075, 0.140, 0.875 + 0.008 * math.sin(phi)])
    g_pole_R = np.array([0.14, 0.28, 1.08])
    err_gR = girl.solve_arm_ik("R", g_target_R, g_pole_R, g_rots, g_rmats, g_root_pos, g_root_yaw)

    girl_res = girl.pose_all(
        g_rots, g_rmats, g_root_pos, g_root_yaw, phi=phi, wind_swell=wind_swell, ground_feet=True
    )
    B_pose_g, _ = girl.compute_bone_world(g_rots, g_rmats, g_root_pos, g_root_yaw)
    z_g_shift = float(girl_res[3]["wrist_R"][2] - B_pose_g[girl.bone_idx["wrist.R"]][2, 3])
    P_g_palm = B_pose_g[girl.bone_idx["finger3-1.R"]][:3, 3].copy() + np.array([0.0, 0.0, z_g_shift - 0.025])

    # --- BOY (cozy 3/4 back view seated close beside her, yaw=152, lower hips/knees below meadow knoll) ---
    b_root_pos = (-0.28, 0.03, -0.60 + 0.004 * math.sin(2.0 * phi))
    b_root_yaw = 152.0 + 1.0 * math.sin(phi)
    meteor_look = math.sin(((t_norm - 0.06) / 0.32) * math.pi) ** 1.4 if 0.06 < t_norm < 0.38 else 0.0
    b_rots: Dict[str, Tuple[float, float, float]] = {
        "spine05": (5.0, 0.0, 0.0),
        "spine03": (4.0 + 1.2 * math.sin(2.0 * phi), 0.0, 0.0),
        "spine02": (3.0 + 0.8 * math.sin(2.0 * phi), 0.0, 0.0),
        "spine01": (2.0, 0.0, 0.0),
        "neck01": (-8.0, -10.0, 0.0),
        "head": (-14.0 - 5.0 * meteor_look + 1.5 * math.sin(phi), -16.0 - 4.0 * meteor_look, 2.0 + 2.0 * meteor_look),
        "upperleg01.R": (46.0, 0.0, 14.0),
        "lowerleg01.R": (-78.0, 0.0, 0.0),
        "upperleg01.L": (42.0, 0.0, -16.0),
        "lowerleg01.L": (-74.0, 0.0, 0.0),
    }
    curl_hand_fingers(b_rots, "R", 0.88)
    curl_hand_fingers(b_rots, "L", 0.35)
    b_rmats: Dict[str, np.ndarray] = {}

    b_target_L = np.array([-0.46, 0.16, 0.29])
    b_pole_L = np.array([-0.62, 0.04, 0.52])
    err_bL = boy.solve_arm_ik("L", b_target_L, b_pole_L, b_rots, b_rmats, b_root_pos, b_root_yaw)

    B_pose_b0, _ = boy.compute_bone_world(b_rots, b_rmats, b_root_pos, b_root_yaw)
    S_bR = B_pose_b0[boy.bone_idx["upperarm01.R"]][:3, 3]
    u_app = _norm(P_g_palm - S_bR)
    b_target_R = P_g_palm - 0.068 * u_app + np.array([0.0, -0.014, -0.008])
    b_pole_R = np.array([-0.14, -0.18, 0.54])
    err_bR = boy.solve_arm_ik("R", b_target_R, b_pole_R, b_rots, b_rmats, b_root_pos, b_root_yaw)

    # Analytically aim Boy's wrist.R + curled palm around Girl's fingers at P_g_palm
    B_pose_b1, _ = boy.compute_bone_world(b_rots, b_rmats, b_root_pos, b_root_yaw)
    iwr = boy.bone_idx["wrist.R"]
    if3 = boy.bone_idx["finger3-1.R"]
    R_parent_wr = B_pose_b1[boy.parents[iwr]][:3, :3] @ boy.B_local_rest[iwr][:3, :3]
    v_hand_cur = B_pose_b1[if3][:3, 3] - B_pose_b1[iwr][:3, 3]
    v_hand_des = P_g_palm - B_pose_b1[iwr][:3, 3]
    R_cup = _rot_axis_angle(_norm(v_hand_des), math.radians(-25.0))
    b_rmats["wrist.R"] = R_parent_wr.T @ (R_cup @ _rot_between(v_hand_cur, v_hand_des) @ R_parent_wr)
    clasp_pos = P_g_palm

    boy_res = boy.pose_all(
        b_rots, b_rmats, b_root_pos, b_root_yaw, phi=phi, wind_swell=wind_swell, ground_feet=False
    )

    ik_diag = dict(
        fpose=fpose,
        err_girl_R_cm=round(err_gR, 3),
        err_girl_L_cm=round(err_gL, 3),
        err_boy_R_cm=round(err_bR, 3),
        err_boy_L_cm=round(err_bL, 3),
        err_leg_R_cm=round(err_leg_R, 3),
        err_leg_L_cm=round(err_leg_L, 3),
        girl_foot_z_cm=round(girl_res[3]["foot_z_cm"], 3),
        clasp_pos=clasp_pos.tolist(),
    )
    return girl_res, boy_res, ik_diag


def run_preview():
    girl, boy = build_cast()
    W_cell, H_cell = 420, 620
    canvas = Image.new("RGB", (W_cell * 4, H_cell * 2), (24, 18, 56))
    dr = ImageDraw.Draw(canvas)

    def draw_shaded(im_pass: Image.Image, mode: str) -> Image.Image:
        arr = np.asarray(im_pass, dtype=np.float32) / 255.0
        a = arr[..., 3:4]
        bg = np.array([28 / 255.0, 22 / 255.0, 72 / 255.0], dtype=np.float32)
        if mode == "girl":
            core = np.array([1.0, 0.96, 0.94]) * (0.72 + 0.28 * arr[..., 1:2])
            col = np.clip(core + arr[..., 2:3] * 0.22, 0, 1)
        else:
            col = np.array([0.11, 0.09, 0.34]) + arr[..., 0:1] * np.array([0.18, 0.72, 1.0]) + arr[..., 1:2] * np.array([0.9, 0.2, 0.9])
            col = np.clip(col, 0, 1)
        return Image.fromarray((np.clip(col * a + bg * (1 - a), 0, 1) * 255).astype(np.uint8))

    # Row 0: Girl turnaround with posed straight contrapposto legs
    for ci, yaw in enumerate([-30.0, 60.0, 150.0, -120.0]):
        g_rots_t: Dict[str, Tuple[float, float, float]] = {}
        g_rm_t: Dict[str, np.ndarray] = {}
        R_y = _euler_xyz_deg(0.0, 0.0, yaw)
        girl.solve_leg_ik("R", R_y @ np.array([-0.068, 0.010, 0.072]), R_y @ np.array([-0.072, -0.55, 0.44]), yaw - 4.0, g_rots_t, g_rm_t, (0, 0, 0), yaw)
        girl.solve_leg_ik("L", R_y @ np.array([0.076, -0.032, 0.072]), R_y @ np.array([0.080, -0.58, 0.44]), yaw + 6.0, g_rots_t, g_rm_t, (0, 0, 0), yaw)
        girl.solve_arm_ik("R", R_y @ np.array([-0.20, -0.02, 0.72]), R_y @ np.array([-0.28, 0.10, 0.95]), g_rots_t, g_rm_t, (0, 0, 0), yaw)
        girl.solve_arm_ik("L", R_y @ np.array([0.20, -0.02, 0.72]), R_y @ np.array([0.28, 0.10, 0.95]), g_rots_t, g_rm_t, (0, 0, 0), yaw)
        V, T, N, _ = girl.pose_all(g_rots_t, g_rm_t, (0.0, 0.0, 0.0), yaw, phi=1.2, wind_swell=0.8, ground_feet=True)
        cam = make_camera(cam_pos=(0.0, -2.5, 0.85), target=(0.0, 0.0, 0.82), lens_mm=42.0, width=W_cell, height=H_cell)
        canvas.paste(draw_shaded(render_character_pass(V, T, N, cam, "girl", np.array([0.5, -0.5, 1.2])), "girl"), (ci * W_cell, 0))
        dr.text((ci * W_cell + 10, 10), f"Girl yaw={yaw:.0f}", fill=(255, 255, 160))

    # Row 1: Boy 3/4 back + Full Couple + 1:1 Clasp + 1:1 Girl Legs/Skirt
    girl_res, boy_res, ik_diag = pose_couple_frame(girl, boy, 55, 240)
    print("Preview f=55 diagnostics:", json.dumps(ik_diag))
    for k, v in ik_diag.items():
        if k.startswith("err_") and v > 2.0:
            print(f"WARNING IK error > 2cm: {k}={v} cm")

    cam_hero = make_camera(width=1080, height=1920)
    Vg, Tg, Ng, dg = girl_res
    Vb, Tb, Nb, db = boy_res
    ag = np.asarray(render_character_pass(Vg, Tg, Ng, cam_hero, "girl", dg["chest_pos"], ssaa=2), dtype=np.float32) / 255.0
    ab = np.asarray(render_character_pass(Vb, Tb, Nb, cam_hero, "boy", dg["chest_pos"], ssaa=2), dtype=np.float32) / 255.0
    bg_h = np.full((1920, 1080, 3), [36 / 255.0, 24 / 255.0, 74 / 255.0], dtype=np.float32)
    col_b = np.array([0.11, 0.09, 0.32]) + ab[..., 0:1] * np.array([0.2, 0.78, 1.0]) + ab[..., 1:2] * np.array([0.9, 0.25, 0.95])
    col_g = np.array([1.0, 0.95, 0.94]) * (0.76 + 0.24 * ag[..., 1:2]) + ag[..., 2:3] * 0.24
    comp = bg_h * (1 - ab[..., 3:4]) + np.clip(col_b, 0, 1) * ab[..., 3:4]
    comp = comp * (1 - ag[..., 3:4]) + np.clip(col_g, 0, 1) * ag[..., 3:4]
    im_comp = Image.fromarray((np.clip(comp, 0, 1) * 255).astype(np.uint8))

    # Col 0: Boy 3/4 seated closeup
    uv_b, _ = project_points(cam_hero, np.array([db["head_pos"] - [0, 0, 0.12]]))
    bx, by = int(uv_b[0, 0]), int(uv_b[0, 1])
    crop_boy = im_comp.crop((max(0, bx - 170), max(0, by - 210), min(1080, bx + 170), min(1920, by + 230))).resize((W_cell, H_cell), Image.Resampling.LANCZOS)
    canvas.paste(crop_boy, (0, H_cell))
    dr.text((10, H_cell + 10), "Boy 3/4 back + jacket + curls", fill=(120, 230, 255))

    # Col 1: Full couple composition with dashed cyan ridge reference curve
    im_couple_marked = im_comp.copy()
    dr_m = ImageDraw.Draw(im_couple_marked)
    for k_seg in range(0, 72, 2):
        u0 = k_seg / 72.0
        u1 = (k_seg + 1) / 72.0
        v0 = 0.858 - 0.070 / (1.0 + math.exp((u0 - 0.44) / 0.08)) + 0.004 * math.sin(u0 * 7.5 + 0.6)
        v1 = 0.858 - 0.070 / (1.0 + math.exp((u1 - 0.44) / 0.08)) + 0.004 * math.sin(u1 * 7.5 + 0.6)
        dr_m.line([(u0 * 1080, v0 * 1920), (u1 * 1080, v1 * 1920)], fill=(80, 235, 255), width=3)
    canvas.paste(im_couple_marked.crop((140, 880, 920, 1840)).resize((W_cell, H_cell), Image.Resampling.LANCZOS), (W_cell, H_cell))
    dr.text((W_cell + 10, H_cell + 10), "Couple f=55 (cyan=grass ridge)", fill=(255, 220, 180))

    # Col 2: 1:1 Hand clasp crop
    uv_c, _ = project_points(cam_hero, np.array([ik_diag["clasp_pos"]]))
    cx, cy = int(uv_c[0, 0]), int(uv_c[0, 1])
    crop_clasp = im_comp.crop((max(0, cx - 140), max(0, cy - 200), min(1080, cx + 140), min(1920, cy + 200))).resize((W_cell, H_cell), Image.Resampling.NEAREST)
    canvas.paste(crop_clasp, (2 * W_cell, H_cell))
    dr.text((2 * W_cell + 10, H_cell + 10), f"1:1 Clasp gR={ik_diag['err_girl_R_cm']} bR={ik_diag['err_boy_R_cm']}cm", fill=(160, 255, 160))

    # Col 3: 1:1 Girl legs + skirt crop
    uv_l, _ = project_points(cam_hero, np.array([[0.27, 0.18, 0.36]]))
    lx, ly = int(uv_l[0, 0]), int(uv_l[0, 1])
    crop_legs = im_comp.crop((max(0, lx - 160), max(0, ly - 240), min(1080, lx + 160), min(1920, ly + 240))).resize((W_cell, H_cell), Image.Resampling.LANCZOS)
    canvas.paste(crop_legs, (3 * W_cell, H_cell))
    dr.text((3 * W_cell + 10, H_cell + 10), f"1:1 Legs+Skirt z={ik_diag['girl_foot_z_cm']}cm", fill=(255, 200, 220))

    out_path = os.path.join(PROJ_ROOT, "assets", "cast_preview_v2.png")
    canvas.save(out_path)
    print("Saved cast preview v2:", out_path)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        run_preview()
