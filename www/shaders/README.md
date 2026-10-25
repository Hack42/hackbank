# Button shader sources

These five adaptations use GLSL supplied by the user for the linked examples.
Each JavaScript file registers a local fragment-shader body; no remote shader
code, images, audio, libraries or buffer passes are fetched at runtime.

| Preset | Source | Credit and licence supplied with the code |
| --- | --- | --- |
| Wonderful | [mtyGWy](https://www.shadertoy.com/view/mtyGWy), [tutorial](https://youtu.be/f4s1h2YETNY) | Tutorial credit preserved; no licence statement in the supplied source. |
| Heartfelt | [ltffzl](https://www.shadertoy.com/view/ltffzl) | Martijn Steinrucken / BigWings, 2017. CC BY-NC-SA 3.0 Unported. |
| Star Nest | [XlfGRj](https://www.shadertoy.com/view/XlfGRj) | Pablo Roman Andrioli. MIT. |
| 2D Clouds | [4tdSWr](https://www.shadertoy.com/view/4tdSWr) | No author or licence statement in the supplied source. |
| Universe Within | [lscczl](https://www.shadertoy.com/view/lscczl) | Martijn Steinrucken / BigWings, 2018. CC BY-NC-SA 3.0 Unported. |

The shader-specific notices are retained in their respective files; the MIT
notice is included in full. See the [CC BY-NC-SA 3.0 terms](https://creativecommons.org/licenses/by-nc-sa/3.0/)
for the two BigWings shaders. These notices describe the supplied shader code;
they do not assert a new licence for the rest of the application.

All scenes use the shared renderer's username-seeded clock, three scene colours,
speed and intensity controls. Numerical guards prevent zero-distance divisions;
descending smoothstep transitions use an explicit interpolation for WebGL 1.
The original Wonderful ring iterations, Star Nest's 20 × 17 volume/fractal
iterations and 2D Clouds' noise layers are retained.

Wonderful uses a 2× closer view so its pattern is legible on a small button.
Heartfelt uses a procedural bokeh backdrop in place of its missing image input,
with closer framing and continuous rain covering the whole button. Its heart
accent changes the fog instead of masking the rain to the centre. Lightning
is subdued and full-button intro/outro fades are removed.
Universe Within keeps its four network
layers and sparkles, replaces audio FFT input with a quiet glow, fits the
vignette to the button and removes long intro/outro blackouts. Both are silent
and use fixed ambient camera/parallax settings instead of mouse input.
