/* =============================================================================
   Lily Pond — WebGL2 renderer: living water, lit sprites, dappled sunlight.
   ============================================================================= */
'use strict';

const SUN = (() => { const v = [-0.48, 0.58, 0.66], l = Math.hypot(v[0], v[1], v[2]); return v.map(c => c / l); })();

const VS_FULL = `#version 300 es
void main(){ vec2 p = vec2(float((gl_VertexID << 1) & 2), float(gl_VertexID & 2)); gl_Position = vec4(p * 2.0 - 1.0, 0.0, 1.0); }`;

/* ---- ripple simulation: a damped wave equation on a height field ---- */
const FS_SIM = `#version 300 es
precision highp float;
uniform sampler2D uPrev, uShore;
uniform vec2 uPx;
uniform vec4 uDrops[12];
uniform int uCount;
out vec4 o;
void main(){
  vec2 uv = gl_FragCoord.xy * uPx;
  vec2 c = texture(uPrev, uv).rg;
  float l = texture(uPrev, uv - vec2(uPx.x, 0.0)).r, r = texture(uPrev, uv + vec2(uPx.x, 0.0)).r;
  float d = texture(uPrev, uv - vec2(0.0, uPx.y)).r, u = texture(uPrev, uv + vec2(0.0, uPx.y)).r;
  float h = ((l + r + d + u) * 0.5 - c.g) * 0.986;
  for (int i = 0; i < 12; i++) {
    if (i >= uCount) break;
    vec2 q = (uv - uDrops[i].xy) / (uPx * uDrops[i].z);
    h += uDrops[i].w * exp(-dot(q, q));
  }
  h *= smoothstep(-0.05, 0.25, texture(uShore, uv).r);     // the bank swallows waves
  o = vec4(clamp(h, -4.0, 4.0), c.r, 0.0, 1.0);
}`;

/* ---- the pond: bottom, water column, surface, bank ---- */
const FS_WATER = `#version 300 es
precision highp float;
uniform vec2 uRes;
uniform vec3 uCam;
uniform vec4 uRect;
uniform float uTime, uSimOn;
uniform vec3 uSun;
uniform sampler2D uNoise, uWave, uSim, uUnder, uShore, uGrass;
out vec4 o;
void main(){
  vec2 w = uCam.xy + (gl_FragCoord.xy - 0.5 * uRes) / uCam.z;
  vec2 ruv = (w - uRect.xy) / uRect.zw;
  float sd = texture(uShore, ruv).r;
  float t = uTime;
  // surface slope: slow swells and finer wavelets, plus the interactive ripples
  vec2 g = (texture(uWave, w * 0.045 + vec2(0.006, 0.004) * t).rg - 0.5);
  g += (texture(uWave, w * 0.11 + vec2(-0.009, 0.011) * t + 0.3).ba - 0.5) * 0.55;
  g += (texture(uWave, w * 0.27 + vec2(0.016, -0.019) * t + 0.7).rg - 0.5) * 0.22;
  g *= 0.20 * (0.35 + 0.65 * smoothstep(0.0, 0.7, sd));
  if (uSimOn > 0.5) {
    vec2 px = 1.0 / vec2(textureSize(uSim, 0));
    float hl = texture(uSim, ruv - vec2(px.x, 0.0)).r, hr = texture(uSim, ruv + vec2(px.x, 0.0)).r;
    float hd = texture(uSim, ruv - vec2(0.0, px.y)).r, hu = texture(uSim, ruv + vec2(0.0, px.y)).r;
    g += vec2(hr - hl, hu - hd) * 2.2;
  }
  vec3 N = normalize(vec3(-g, 1.0));
  float depth = smoothstep(0.0, 2.6, sd);
  // pond floor, seen through the moving surface
  vec2 rw = w + N.xy * (0.12 + 0.55 * depth);
  float n1 = texture(uNoise, rw * 0.11).r, n2 = texture(uNoise, rw * 0.43 + 0.2).g;
  vec4 cell = texture(uNoise, rw * 0.8);
  vec3 sand = mix(vec3(0.50, 0.45, 0.29), vec3(0.33, 0.33, 0.20), n1);
  vec3 silt = mix(vec3(0.13, 0.19, 0.12), vec3(0.06, 0.11, 0.08), n2);
  vec3 bed = mix(sand, silt, smoothstep(0.15, 1.7, sd + (n1 - 0.5) * 1.1));
  float pebble = smoothstep(0.42, 0.18, cell.b) * (1.0 - smoothstep(0.3, 1.5, sd + (n2 - 0.5)));
  bed = mix(bed, bed * (0.55 + 1.3 * texture(uNoise, rw * 0.8 + 0.5).r) + 0.03, pebble * 0.8);
  bed *= 0.78 + 0.45 * n2;
  // caustics dance on the shallows
  vec2 cu = rw * 0.2 + N.xy * 0.25;
  float c1 = texture(uNoise, cu + vec2(0.012, 0.008) * t).a;
  float c2 = texture(uNoise, cu * 1.31 - vec2(0.010, 0.013) * t + 0.5).a;
  float ca = c1 * c2 * 1.8 + 0.22 * (c1 + c2);
  bed *= 1.0 + ca * (1.05 - depth) * 0.75;
  vec3 deep = vec3(0.016, 0.105, 0.100);
  vec3 col = mix(bed, deep, 1.0 - exp(-depth * 2.5));
  col += vec3(0.02, 0.05, 0.04) * ca * depth * 0.6;               // faint light shafts in deep water
  // shadows of the pads and the koi, refracted
  vec2 suv = (gl_FragCoord.xy + N.xy * uCam.z * (0.10 + 0.30 * depth)) / uRes;
  vec4 under = texture(uUnder, suv);
  col = col * (1.0 - under.a) + under.rgb * vec3(0.72, 0.92, 0.86);
  // the sky and the trees around the pond, mirrored in the surface
  vec2 rv = w * 0.06 + N.xy * 2.2 + vec2(0.003 * t, 0.0);
  float canopy = smoothstep(0.40, 0.62, texture(uNoise, rv).r * 0.62 + texture(uNoise, rv * 2.6).g * 0.38);
  vec3 sky = mix(vec3(0.66, 0.82, 0.93), vec3(0.03, 0.11, 0.05), canopy);
  float fres = clamp(0.085 + 5.0 * (1.0 - N.z), 0.0, 0.5);
  col = mix(col, sky, fres);
  vec3 H = normalize(vec3(uSun.xy * 0.22, 1.0));
  col += vec3(1.0, 0.97, 0.88) * pow(max(dot(N, H), 0.0), 1500.0) * 0.42 * (1.0 - canopy * 0.8);
  col *= 0.72 + 0.28 * smoothstep(0.0, 0.35, sd);                 // bank shadow on the water's edge
  col += vec3(0.20, 0.22, 0.18) * (1.0 - smoothstep(0.0, 0.05, abs(sd - 0.03))) * (0.4 + 0.6 * n2);
  // the bank
  if (sd < 0.05) {
    vec2 gu = w * 0.40;
    vec3 gr = mix(texture(uGrass, gu).rgb, texture(uGrass, gu * 0.37 + 0.31).rgb, 0.4);
    gr *= 0.72 + 0.7 * texture(uNoise, w * 0.045).g;
    vec3 soil = mix(vec3(0.21, 0.16, 0.10), vec3(0.10, 0.085, 0.06), n2) * (0.8 + 0.5 * cell.b);
    float wet = smoothstep(-0.50 - 0.2 * n1, -0.02, sd);
    vec3 bank = mix(gr, soil, wet * 0.92);
    bank *= 1.0 - 0.4 * smoothstep(-0.16, 0.0, sd);
    col = mix(bank, col, smoothstep(-0.012, 0.03, sd));
  }
  o = vec4(col, 1.0);
}`;

/* ---- sprites: Blender renders, re-lit per pixel by the game's sun ---- */
const VS_SPRITE = `#version 300 es
layout(location=0) in vec2 aPos;
layout(location=1) in vec2 aUV;
layout(location=2) in vec2 aRot;
layout(location=3) in vec4 aTint;
layout(location=4) in vec4 aParam;
uniform vec2 uRes; uniform vec3 uCam;
out vec2 vUV; out vec2 vRot; out vec4 vTint; out vec4 vParam;
void main(){
  vUV = aUV; vRot = aRot; vTint = aTint; vParam = aParam;
  gl_Position = vec4((aPos - uCam.xy) * uCam.z / (0.5 * uRes), 0.0, 1.0);
}`;
const FS_SPRITE = `#version 300 es
precision highp float;
uniform sampler2D uTex, uTex2, uNorm;
uniform vec3 uSun;
uniform vec2 uTexSize;
in vec2 vUV; in vec2 vRot; in vec4 vTint; in vec4 vParam;
out vec4 o;
void main(){
  float mode = vParam.y;
  if (mode > 2.5) {                         // soft ring (highlights)
    float d = length(vUV - 0.5) * 2.0;
    float a = smoothstep(vParam.z - vParam.w, vParam.z, d) * (1.0 - smoothstep(vParam.z, vParam.z + vParam.w * 0.6, d));
    o = vec4(vTint.rgb * a * vTint.a, a * vTint.a * 0.35);
    return;
  }
  vec2 uv = vUV / uTexSize;
  if (mode > 0.5 && mode < 1.5) {           // shadow: blurred silhouette
    float a = textureLod(uTex, uv, vParam.z).a;
    o = vec4(vTint.rgb * a * vTint.a, a * vTint.a);
    return;
  }
  vec4 a = texture(uTex, uv);
  if (vParam.x > 0.001) a = mix(a, texture(uTex2, uv), vParam.x);
  if (a.a < 0.004) discard;
  vec3 alb = a.rgb / a.a;
  if (mode > 1.5) { o = vec4(alb * vTint.rgb, 1.0) * a.a * vTint.a; return; }   // unlit
  vec3 n = texture(uNorm, uv).xyz * 2.0 - 1.0;
  n.xy = vec2(n.x * vRot.x - n.y * vRot.y, n.x * vRot.y + n.y * vRot.x);
  n = normalize(n);
  float ndl = max(dot(n, uSun), 0.0);
  vec3 H = normalize(uSun + vec3(0.0, 0.0, 1.0));
  float spec = pow(max(dot(n, H), 0.0), 60.0) * vParam.w + pow(max(dot(n, H), 0.0), 400.0) * vParam.w * 1.5;
  vec3 col = alb * vTint.rgb * (0.50 + 0.92 * ndl) * (0.86 + 0.14 * n.z) + vec3(1.0, 0.98, 0.92) * spec;
  o = vec4(col, 1.0) * a.a * vTint.a;
}`;

/* ---- last pass: sunlight falling through leaves, and a soft vignette ---- */
const FS_LIGHT = `#version 300 es
precision highp float;
uniform vec2 uRes; uniform vec3 uCam; uniform float uTime;
uniform sampler2D uNoise;
out vec4 o;
void main(){
  vec2 w = uCam.xy + (gl_FragCoord.xy - 0.5 * uRes) / uCam.z;
  float t = uTime;
  vec2 sway = vec2(sin(t * 0.31), cos(t * 0.23)) * 0.012;
  float d1 = texture(uNoise, w * 0.031 + sway + vec2(0.0015 * t, 0.0)).r;
  float d2 = texture(uNoise, w * 0.083 - sway * 1.7 + 0.4).g;
  float leaf = smoothstep(0.36, 0.60, d1 * 0.62 + d2 * 0.38);
  vec3 c = mix(vec3(0.66, 0.74, 0.84), vec3(1.14, 1.09, 0.98), leaf);
  vec2 q = gl_FragCoord.xy / uRes - 0.5;
  c *= 1.0 - dot(q, q) * 0.62;
  float over = max(max(c.r, c.g), c.b) - 1.0;
  o = vec4(min(c, vec3(1.0)), max(over, 0.0));
}`;

class Renderer {
  constructor(canvas, images, atlas) {
    const gl = canvas.getContext('webgl2', { antialias: false, alpha: false, premultipliedAlpha: false, powerPreference: 'high-performance' });
    if (!gl) throw new Error('WebGL2 is not available');
    this.gl = gl; this.canvas = canvas; this.atlas = atlas;
    this.floatOK = !!(gl.getExtension('EXT_color_buffer_float') || gl.getExtension('EXT_color_buffer_half_float'));
    this.progWater = this.program(VS_FULL, FS_WATER);
    this.progSprite = this.program(VS_SPRITE, FS_SPRITE);
    this.progLight = this.program(VS_FULL, FS_LIGHT);
    this.progSim = this.floatOK ? this.program(VS_FULL, FS_SIM) : null;
    this.tex = {
      frogRed: this.imageTexture(images.frog_red, true), frogBlue: this.imageTexture(images.frog_blue, true),
      frogN: this.imageTexture(images.frog_n, false),
      pad: this.imageTexture(images.pad, true), padN: this.imageTexture(images.pad_n, false),
      props: this.imageTexture(images.props, true), propsN: this.imageTexture(images.props_n, false),
      grass: this.imageTexture(images.grass, false, true),
    };
    this.sets = {
      frog: { a: this.tex.frogRed, b: this.tex.frogBlue, n: this.tex.frogN, size: atlas.frog.size },
      pad: { a: this.tex.pad, b: this.tex.pad, n: this.tex.padN, size: atlas.pad.size },
      props: { a: this.tex.props, b: this.tex.props, n: this.tex.propsN, size: atlas.props.size },
    };
    this.makeNoise();
    this.vao = gl.createVertexArray();
    this.vbo = gl.createBuffer();
    gl.bindVertexArray(this.vao);
    gl.bindBuffer(gl.ARRAY_BUFFER, this.vbo);
    const stride = 14 * 4;
    [[0, 2, 0], [1, 2, 8], [2, 2, 16], [3, 4, 24], [4, 4, 40]].forEach(([loc, n, off]) => {
      gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, n, gl.FLOAT, false, stride, off);
    });
    gl.bindVertexArray(null);
    this.emptyVao = gl.createVertexArray();
    this.under = new Batch(); this.main = new Batch();
    this.cam = [0, 0, 100];
    this.rect = [0, 0, 1, 1];
    this.drops = [];
    this.simAcc = 0;
    this.shoreTex = null; this.sim = null; this.underFbo = null;
    this.quality = 1;
  }

  program(vs, fs) {
    const gl = this.gl, p = gl.createProgram();
    for (const [type, src] of [[gl.VERTEX_SHADER, vs], [gl.FRAGMENT_SHADER, fs]]) {
      const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s) + '\n' + src.split('\n').slice(0, 6).join('\n'));
      gl.attachShader(p, s);
    }
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p));
    const u = {}, n = gl.getProgramParameter(p, gl.ACTIVE_UNIFORMS);
    for (let i = 0; i < n; i++) { const info = gl.getActiveUniform(p, i); u[info.name.replace('[0]', '')] = gl.getUniformLocation(p, info.name); }
    return { p, u };
  }

  imageTexture(img, premultiply, repeat) {
    const gl = this.gl, t = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, t);
    gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, premultiply);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
    gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
    gl.generateMipmap(gl.TEXTURE_2D);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    const wrap = repeat ? gl.REPEAT : gl.CLAMP_TO_EDGE;
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, wrap); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, wrap);
    const ext = gl.getExtension('EXT_texture_filter_anisotropic');
    if (ext) gl.texParameterf(gl.TEXTURE_2D, ext.TEXTURE_MAX_ANISOTROPY_EXT, 4);
    return t;
  }

  /* Two tiling textures drive every procedural effect:
     noise: R,G = fractal noise, B = distance to nearest cell point, A = cell borders
     wave:  RG and BA = slopes of two fractal height fields                          */
  makeNoise() {
    const gl = this.gl, S = 256, rnd = PondCore().mulberry32(20231119);
    const fbm = (base, octaves) => {
      const out = new Float32Array(S * S); let amp = 1, tot = 0;
      for (let o = 0; o < octaves; o++) {
        const n = base << o, lat = new Float32Array(n * n);
        for (let i = 0; i < lat.length; i++) lat[i] = rnd();
        for (let y = 0; y < S; y++) for (let x = 0; x < S; x++) {
          const fx = x / S * n, fy = y / S * n, x0 = Math.floor(fx), y0 = Math.floor(fy);
          let tx = fx - x0, ty = fy - y0; tx = tx * tx * tx * (tx * (tx * 6 - 15) + 10); ty = ty * ty * ty * (ty * (ty * 6 - 15) + 10);
          const x1 = (x0 + 1) % n, y1 = (y0 + 1) % n;
          const a = lat[y0 * n + x0], b = lat[y0 * n + x1], c = lat[y1 * n + x0], d = lat[y1 * n + x1];
          out[y * S + x] += amp * (a + (b - a) * tx + (c - a) * ty + (a - b - c + d) * tx * ty);
        }
        tot += amp; amp *= 0.5;
      }
      let lo = 1e9, hi = -1e9;
      for (let i = 0; i < out.length; i++) { out[i] /= tot; lo = Math.min(lo, out[i]); hi = Math.max(hi, out[i]); }
      for (let i = 0; i < out.length; i++) out[i] = (out[i] - lo) / (hi - lo);
      return out;
    };
    const f1 = fbm(4, 5), f2 = fbm(4, 5), h1 = fbm(6, 4), h2 = fbm(8, 4);
    const G = 12, pts = new Float32Array(G * G * 2);
    for (let i = 0; i < G * G; i++) { pts[i * 2] = rnd(); pts[i * 2 + 1] = rnd(); }
    const noise = new Uint8Array(S * S * 4), wave = new Uint8Array(S * S * 4);
    for (let y = 0; y < S; y++) for (let x = 0; x < S; x++) {
      const i = y * S + x, gx = x / S * G, gy = y / S * G, cx = Math.floor(gx), cy = Math.floor(gy);
      let d1 = 9, d2 = 9;
      for (let oy = -1; oy <= 1; oy++) for (let ox = -1; ox <= 1; ox++) {
        const k = ((cy + oy + G) % G) * G + ((cx + ox + G) % G);
        const d = Math.hypot(cx + ox + pts[k * 2] - gx, cy + oy + pts[k * 2 + 1] - gy);
        if (d < d1) { d2 = d1; d1 = d; } else if (d < d2) d2 = d;
      }
      const e = Math.min(1, Math.max(0, (d2 - d1) / 0.22));
      noise[i * 4] = f1[i] * 255; noise[i * 4 + 1] = f2[i] * 255;
      noise[i * 4 + 2] = Math.min(255, d1 * 255); noise[i * 4 + 3] = (1 - e * e * (3 - 2 * e)) * 255;
      const xl = y * S + (x + S - 1) % S, xr = y * S + (x + 1) % S, yd = ((y + S - 1) % S) * S + x, yu = ((y + 1) % S) * S + x;
      const enc = v => Math.max(0, Math.min(255, 127.5 + v * 2600));
      wave[i * 4] = enc(h1[xr] - h1[xl]); wave[i * 4 + 1] = enc(h1[yu] - h1[yd]);
      wave[i * 4 + 2] = enc(h2[xr] - h2[xl]); wave[i * 4 + 3] = enc(h2[yu] - h2[yd]);
    }
    const mk = (data) => {
      const t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, S, S, 0, gl.RGBA, gl.UNSIGNED_BYTE, data);
      gl.generateMipmap(gl.TEXTURE_2D);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      return t;
    };
    this.tex.noise = mk(noise); this.tex.wave = mk(wave);
    this.noiseField = f1; this.noiseSize = S;
  }

  /* World rectangle covered by the shore map and the ripple simulation. */
  setWorld(rect, shore, sw, sh) {
    const gl = this.gl;
    this.rect = rect;
    if (this.shoreTex) gl.deleteTexture(this.shoreTex);
    this.shoreTex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, this.shoreTex);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.R16F, sw, sh, 0, gl.RED, gl.FLOAT, shore);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    if (this.floatOK) {
      const W = 400, H = Math.max(64, Math.round(W * rect[3] / rect[2]));
      if (this.sim) for (const s of this.sim.t) { gl.deleteTexture(s.tex); gl.deleteFramebuffer(s.fbo); }
      this.sim = { w: W, h: H, t: [this.target(W, H, true), this.target(W, H, true)], i: 0 };
    }
    this.drops.length = 0;
  }

  target(w, h, float) {
    const gl = this.gl, tex = gl.createTexture(), fbo = gl.createFramebuffer();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    if (float) gl.texImage2D(gl.TEXTURE_2D, 0, gl.RG16F, w, h, 0, gl.RG, gl.HALF_FLOAT, null);
    else gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, w, h, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
    gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    return { tex, fbo, w, h };
  }

  resize() {
    const gl = this.gl, c = this.canvas;
    const dpr = Math.min(window.devicePixelRatio || 1, 2) * this.quality;
    const w = Math.max(2, Math.round(c.clientWidth * dpr)), h = Math.max(2, Math.round(c.clientHeight * dpr));
    if (c.width !== w || c.height !== h || !this.underFbo) {
      c.width = w; c.height = h;
      if (this.underFbo) { gl.deleteTexture(this.underFbo.tex); gl.deleteFramebuffer(this.underFbo.fbo); }
      this.underFbo = this.target(Math.ceil(w / 2), Math.ceil(h / 2), false);
    }
    this.pxRatio = w / c.clientWidth;
  }

  /* A ripple: world position, radius in world units, strength. */
  drop(x, y, radius, strength) {
    if (!this.sim || this.drops.length >= 48) return;
    const texel = this.rect[2] / this.sim.w;
    this.drops.push([(x - this.rect[0]) / this.rect[2], (y - this.rect[1]) / this.rect[3], Math.max(1.3, radius / texel), strength]);
  }

  bind(unit, tex, loc) { const gl = this.gl; gl.activeTexture(gl.TEXTURE0 + unit); gl.bindTexture(gl.TEXTURE_2D, tex); gl.uniform1i(loc, unit); }

  stepSim(dt) {
    const gl = this.gl, sim = this.sim;
    if (!sim) return;
    this.simAcc = Math.min(this.simAcc + dt, 0.05);
    gl.disable(gl.BLEND);
    gl.bindVertexArray(this.emptyVao);
    gl.useProgram(this.progSim.p);
    while (this.simAcc >= 1 / 60) {
      this.simAcc -= 1 / 60;
      const src = sim.t[sim.i], dst = sim.t[1 - sim.i];
      gl.bindFramebuffer(gl.FRAMEBUFFER, dst.fbo);
      gl.viewport(0, 0, sim.w, sim.h);
      const u = this.progSim.u;
      this.bind(0, src.tex, u.uPrev); this.bind(1, this.shoreTex, u.uShore);
      gl.uniform2f(u.uPx, 1 / sim.w, 1 / sim.h);
      const batch = this.drops.splice(0, 12), flat = new Float32Array(48);
      batch.forEach((d, i) => flat.set(d, i * 4));
      gl.uniform4fv(u.uDrops, flat); gl.uniform1i(u.uCount, batch.length);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
      sim.i = 1 - sim.i;
    }
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
  }

  drawBatch(batch) {
    const gl = this.gl;
    if (!batch.n) return;
    gl.useProgram(this.progSprite.p);
    const u = this.progSprite.u;
    gl.uniform2f(u.uRes, this.vw, this.vh); gl.uniform3fv(u.uCam, this.camPx); gl.uniform3fv(u.uSun, SUN);
    gl.bindVertexArray(this.vao);
    gl.bindBuffer(gl.ARRAY_BUFFER, this.vbo);
    gl.bufferData(gl.ARRAY_BUFFER, batch.data.subarray(0, batch.n * 14), gl.DYNAMIC_DRAW);
    gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
    for (const d of batch.draws) {
      const set = this.sets[d.set];
      this.bind(0, set.a, u.uTex); this.bind(1, set.b, u.uTex2); this.bind(2, set.n, u.uNorm);
      gl.uniform2f(u.uTexSize, set.size[0], set.size[1]);
      gl.drawArrays(gl.TRIANGLES, d.start, d.count);
    }
    gl.bindVertexArray(null);
  }

  render(time, dt) {
    const gl = this.gl;
    this.stepSim(dt);
    const W = this.canvas.width, H = this.canvas.height;
    this.camPx = [this.cam[0], this.cam[1], this.cam[2] * this.pxRatio];
    // 1. what lies under the surface
    gl.bindFramebuffer(gl.FRAMEBUFFER, this.underFbo.fbo);
    gl.viewport(0, 0, this.underFbo.w, this.underFbo.h);
    gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
    this.vw = W; this.vh = H;
    this.drawBatch(this.under);
    // 2. the water and the bank
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.viewport(0, 0, W, H);
    gl.disable(gl.BLEND);
    gl.useProgram(this.progWater.p);
    let u = this.progWater.u;
    gl.uniform2f(u.uRes, W, H); gl.uniform3fv(u.uCam, this.camPx); gl.uniform4fv(u.uRect, this.rect);
    gl.uniform1f(u.uTime, time); gl.uniform1f(u.uSimOn, this.sim ? 1 : 0); gl.uniform3fv(u.uSun, SUN);
    this.bind(0, this.tex.noise, u.uNoise); this.bind(1, this.tex.wave, u.uWave);
    this.bind(2, this.sim ? this.sim.t[this.sim.i].tex : this.tex.noise, u.uSim);
    this.bind(3, this.underFbo.tex, u.uUnder); this.bind(4, this.shoreTex, u.uShore); this.bind(5, this.tex.grass, u.uGrass);
    gl.bindVertexArray(this.emptyVao);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    // 3. everything that floats, sits or flies
    this.drawBatch(this.main);
    // 4. sunlight
    gl.useProgram(this.progLight.p);
    u = this.progLight.u;
    gl.uniform2f(u.uRes, W, H); gl.uniform3fv(u.uCam, this.camPx); gl.uniform1f(u.uTime, time);
    this.bind(0, this.tex.noise, u.uNoise);
    gl.enable(gl.BLEND); gl.blendFunc(gl.DST_COLOR, gl.SRC_ALPHA);
    gl.bindVertexArray(this.emptyVao);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    gl.disable(gl.BLEND);
  }
}

/* A growable list of textured quads; consecutive quads from the same atlas
   are drawn in one call. */
class Batch {
  constructor() { this.data = new Float32Array(14 * 6 * 512); this.n = 0; this.draws = []; }
  clear() { this.n = 0; this.draws.length = 0; }
  use(set) {
    const last = this.draws[this.draws.length - 1];
    if (!last || last.set !== set) this.draws.push({ set, start: this.n, count: 0 });
  }
  vert(x, y, u, v, c, s, tint, par) {
    if ((this.n + 1) * 14 > this.data.length) { const d = new Float32Array(this.data.length * 2); d.set(this.data); this.data = d; }
    const o = this.n * 14, a = this.data;
    a[o] = x; a[o + 1] = y; a[o + 2] = u; a[o + 3] = v; a[o + 4] = c; a[o + 5] = s;
    a[o + 6] = tint[0]; a[o + 7] = tint[1]; a[o + 8] = tint[2]; a[o + 9] = tint[3];
    a[o + 10] = par[0]; a[o + 11] = par[1]; a[o + 12] = par[2]; a[o + 13] = par[3];
    this.n++; this.draws[this.draws.length - 1].count++;
  }
  /* Four corners (top-left, top-right, bottom-right, bottom-left) with the
     pixel rectangle [x, y, w, h] of the atlas. */
  quad4(set, p, rect, rot, tint, par) {
    this.use(set);
    const c = Math.cos(rot), s = Math.sin(rot);
    const u0 = rect[0] + 0.5, v0 = rect[1] + 0.5, u1 = rect[0] + rect[2] - 0.5, v1 = rect[1] + rect[3] - 0.5;
    this.vert(p[0], p[1], u0, v0, c, s, tint, par); this.vert(p[2], p[3], u1, v0, c, s, tint, par); this.vert(p[4], p[5], u1, v1, c, s, tint, par);
    this.vert(p[0], p[1], u0, v0, c, s, tint, par); this.vert(p[4], p[5], u1, v1, c, s, tint, par); this.vert(p[6], p[7], u0, v1, c, s, tint, par);
  }
  /* Rotated sprite centred on (x, y). */
  sprite(set, x, y, hw, hh, rot, rect, tint, par) {
    const c = Math.cos(rot), s = Math.sin(rot);
    const ax = c * hw, ay = s * hw, bx = -s * hh, by = c * hh;
    this.quad4(set, [x - ax + bx, y - ay + by, x + ax + bx, y + ay + by, x + ax - bx, y + ay - by, x - ax - bx, y - ay - by], rect, rot, tint, par);
  }
}
