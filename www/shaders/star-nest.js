/* Star Nest by Pablo Roman Andrioli. Source supplied by the user.
   https://www.shadertoy.com/view/XlfGRj

   MIT License
   Copyright (c) Pablo Roman Andrioli

   Permission is hereby granted, free of charge, to any person obtaining a copy
   of this software and associated documentation files (the "Software"), to deal
   in the Software without restriction, including without limitation the rights
   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   copies of the Software, and to permit persons to whom the Software is
   furnished to do so, subject to the following conditions:

   The above copyright notice and this permission notice shall be included in all
   copies or substantial portions of the Software.

   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
   SOFTWARE.

   Adapted to fixed camera angles, scene colours and the shared seeded clock. */
(function(window) {
  var shaders=window.HackBankExtraButtonShaders=window.HackBankExtraButtonShaders || {};
  shaders['shader-star-nest']=`
    vec3 scene() {
      vec2 p=uv-.5;p.y*=resolution.y/resolution.x;
      vec3 direction=vec3(p*.8,1.);
      float drift=time*.01+.25;
      mat2 rot1=mat2(cos(.5),sin(.5),-sin(.5),cos(.5));
      mat2 rot2=mat2(cos(.8),sin(.8),-sin(.8),cos(.8));
      direction.xz*=rot1;direction.xy*=rot2;
      vec3 origin=vec3(1.,.5,.5)+vec3(drift*2.,drift,-2.);
      origin.xz*=rot1;origin.xy*=rot2;
      float s=.1, fade=1.;vec3 v=vec3(0.);
      for(int r=0;r<20;r++) {
        vec3 point=origin+s*direction*.5;
        point=abs(vec3(.85)-mod(point,vec3(1.7)));
        float previous=0., change=0.;
        for(int i=0;i<17;i++) {
          point=abs(point)/max(dot(point,point),.000001)-.53;
          float size=length(point);change+=abs(size-previous);previous=size;
        }
        float darkMatter=max(0.,.3-change*change*.001);
        change*=change*change;
        if(r>6)fade*=1.-darkMatter;
        v+=fade;
        v+=vec3(s,s*s,s*s*s*s)*change*.0015*fade;
        fade*=.73;s+=.1;
      }
      v=mix(vec3(length(v)),v,.85)*.01;
      return color0*v.r+color1*v.g+color2*v.b;
    }
  `;
})(window);
