/* Adapted from the user-supplied Wonderful tutorial shader.
   Shader: https://www.shadertoy.com/view/mtyGWy
   Tutorial: https://youtu.be/f4s1h2YETNY
   Palette reference: https://iquilezles.org/articles/palettes/
   The supplied source did not include a licence statement. */
(function(window) {
  var shaders=window.HackBankExtraButtonShaders=window.HackBankExtraButtonShaders || {};
  shaders['shader-wonderful']=`
    vec3 wonderfulPalette(float t) {
      vec3 wave=.5+.5*cos(6.28318*(vec3(t)+vec3(.263,.416,.557)));
      return (color0*wave.r+color1*wave.g+color2*wave.b)/max(.001,wave.r+wave.g+wave.b);
    }
    vec3 scene() {
      vec2 p=(uv*2.-1.)*vec2(resolution.x/resolution.y,1.)*.5;
      vec2 original=p;
      vec3 result=vec3(0.);
      for(int i=0;i<4;i++) {
        p=fract(p*1.5)-.5;
        float d=length(p)*exp(-length(original));
        vec3 col=wonderfulPalette(length(original)+float(i)*.4+time*.4);
        d=abs(sin(d*8.+time)/8.);
        d=pow(.01/max(d,.0001),1.2);
        result+=col*d;
      }
      return result;
    }
  `;
})(window);
