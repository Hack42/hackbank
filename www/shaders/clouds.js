/* 2D Clouds - adapted from the user-supplied shader.
   Source: https://www.shadertoy.com/view/4tdSWr
   The supplied source did not include author or licence comments.
   Original noise layers retained; sky/cloud colours use the scene palette. */
(function(window) {
  var shaders=window.HackBankExtraButtonShaders=window.HackBankExtraButtonShaders || {};
  shaders['shader-clouds']=`
    const mat2 cloudMatrix=mat2(1.6,1.2,-1.2,1.6);
    vec2 cloudHash(vec2 p) {
      p=vec2(dot(p,vec2(127.1,311.7)),dot(p,vec2(269.5,183.3)));
      return -1.+2.*fract(sin(p)*43758.5453123);
    }
    float cloudNoise(vec2 p) {
      const float K1=.366025404, K2=.211324865;
      vec2 i=floor(p+(p.x+p.y)*K1);
      vec2 a=p-i+(i.x+i.y)*K2;
      vec2 o=a.x>a.y ? vec2(1.,0.) : vec2(0.,1.);
      vec2 b=a-o+K2, c=a-1.+2.*K2;
      vec3 h=max(.5-vec3(dot(a,a),dot(b,b),dot(c,c)),0.);
      vec3 n=h*h*h*h*vec3(dot(a,cloudHash(i)),dot(b,cloudHash(i+o)),dot(c,cloudHash(i+1.)));
      return dot(n,vec3(70.));
    }
    float cloudFbm(vec2 p) {
      float sum=0., amplitude=.1;
      for(int i=0;i<7;i++) {
        sum+=cloudNoise(p)*amplitude;p=cloudMatrix*p;amplitude*=.4;
      }
      return sum;
    }
    vec3 scene() {
      vec2 p=uv, q=p*vec2(resolution.x/resolution.y,1.);
      float drift=time*.03, warp=cloudFbm(q*1.1*.5);
      float ridges=0., weight=.8;
      q*=1.1;q-=warp-drift;
      for(int i=0;i<8;i++) {
        ridges+=abs(weight*cloudNoise(q));q=cloudMatrix*q+drift;weight*=.7;
      }
      float shape=0.;q=p*vec2(resolution.x/resolution.y,1.)*1.1;q-=warp-drift;weight=.7;
      for(int i=0;i<8;i++) {
        shape+=weight*cloudNoise(q);q=cloudMatrix*q+drift;weight*=.6;
      }
      shape*=ridges+shape;
      float colour=0.;drift=time*.03*2.;
      q=p*vec2(resolution.x/resolution.y,1.)*1.1*2.;q-=warp-drift;weight=.4;
      for(int i=0;i<7;i++) {
        colour+=weight*cloudNoise(q);q=cloudMatrix*q+drift;weight*=.6;
      }
      float detail=0.;drift=time*.03*3.;
      q=p*vec2(resolution.x/resolution.y,1.)*1.1*3.;q-=warp-drift;weight=.4;
      for(int i=0;i<7;i++) {
        detail+=abs(weight*cloudNoise(q));q=cloudMatrix*q+drift;weight*=.6;
      }
      colour+=detail;
      vec3 sky=mix(color1,color0,p.y);
      vec3 clouds=color2*vec3(1.1,1.1,1.)*clamp(.5+.3*colour,0.,1.);
      shape=.2+8.*shape*ridges;
      return mix(sky,clamp(.5*sky+clouds,0.,1.),clamp(shape+colour,0.,1.));
    }
  `;
})(window);
