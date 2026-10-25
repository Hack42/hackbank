/* The Universe Within - Martijn Steinrucken aka BigWings - 2018.
   Twitter: @The_ArtOfCode
   Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported.
   https://creativecommons.org/licenses/by-nc-sa/3.0/
   Source: https://www.shadertoy.com/view/lscczl
   Video: https://youtu.be/GAhu4ngQa48
   Tutorial: https://youtu.be/3CycKKJiwis
   Adapted from the user-supplied source for silent ambient buttons:
   audio FFT replaced with a gentle constant glow; scene palette, fixed parallax,
   button-shaped vignette, no intro/outro blackout, WebGL 1 array indexing. */
(function(window) {
  var shaders=window.HackBankExtraButtonShaders=window.HackBankExtraButtonShaders || {};
  shaders['shader-universe']=`
    float netS(float a,float b,float x) {
      float t=clamp((x-a)/(b-a),0.,1.);
      return t*t*(3.-2.*t);
    }
    float netN21(vec2 p) {
      vec3 a=fract(vec3(p.xyx)*vec3(213.897,653.453,253.098));
      a+=dot(a,a.yzx+79.76);
      return fract((a.x+a.y)*a.z);
    }
    vec2 netPosition(vec2 id,vec2 offset,float t) {
      float n=netN21(id+offset), a=t+n;
      return offset+vec2(sin(a*fract(n*10.)),cos(a*fract(n*100.)))*.4;
    }
    float netLine(vec2 a,vec2 b,vec2 p) {
      vec2 pa=p-a, ba=b-a;
      float h=clamp(dot(pa,ba)/max(dot(ba,ba),.000001),0.,1.);
      float d=length(pa-ba*h), span=length(a-b);
      float fade=netS(1.5,.5,span)+netS(.05,.02,abs(span-.75));
      return netS(.04,.01,d)*fade;
    }
    float netLayer(vec2 st,float n,float t) {
      vec2 id=floor(st)+n;st=fract(st)-.5;
      vec2 points[9];
      for(int i=0;i<9;i++) {
        vec2 offset=vec2(mod(float(i),3.)-1.,floor(float(i)/3.)-1.);
        points[i]=netPosition(id,offset,t);
      }
      float lines=0., sparkle=0.;
      for(int i=0;i<9;i++) {
        lines+=netLine(points[4],points[i],st);
        float d=length(st-points[i]);
        float star=.005/max(d*d,.000001)*netS(1.,.7,d);
        float pulse=sin((fract(points[i].x)+fract(points[i].y)+t)*5.)*.4+.6;
        sparkle+=star*pow(pulse,20.);
      }
      lines+=netLine(points[1],points[3],st)+netLine(points[1],points[5],st);
      lines+=netLine(points[7],points[5],st)+netLine(points[7],points[3],st);
      float phase=(sin(t+n)+sin(t*.1))*.25+.5;
      phase+=pow(sin(t*.1)*.5+.5,50.)*5.;
      return lines+sparkle*phase;
    }
    vec3 scene() {
      vec2 p=(uv-.5)*vec2(resolution.x/resolution.y,1.);
      float t=time*.1, s=sin(t), c=cos(t);
      mat2 rotation=mat2(c,-s,s,c);
      vec2 st=p*rotation;
      float network=0.;
      for(int layer=0;layer<4;layer++) {
        float i=float(layer)*.25, z=fract(t+i);
        float size=mix(15.,1.,z), fade=netS(0.,.6,z)*netS(1.,.8,z);
        network+=fade*netLayer(st*size,i,time);
      }
      vec3 wave=vec3(s,cos(t*.4),-sin(t*.24))*.4+.6;
      vec3 base=(color0*wave.r+color1*wave.g+color2*wave.b)/1.5;
      vec3 col=base*(network+max(0.,-p.y)*.15);
      vec2 vignette=uv-.5;
      return col*max(.15,1.-dot(vignette,vignette));
    }
  `;
})(window);
