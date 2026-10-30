/* Heartfelt - Martijn Steinrucken aka BigWings - 2017.
   Twitter: @The_ArtOfCode
   Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported.
   https://creativecommons.org/licenses/by-nc-sa/3.0/
   Source: https://www.shadertoy.com/view/ltffzl
   Video: https://www.youtube.com/watch?v=uiF5Tlw22PI
   Adapted from the user-supplied source for silent ambient buttons:
   procedural palette backdrop replaces iChannel0; no audio or mouse input;
   subdued lightning, closer framing and continuous rain across the button.
   The heart accents the fog rather than limiting where rain appears.
   N13 noise is credited to Dave Hoskins in the supplied source. */
(function(window) {
  var shaders=window.HackBankExtraButtonShaders=window.HackBankExtraButtonShaders || {};
  shaders['shader-heartfelt']=`
    float rainS(float a,float b,float x) {
      if(abs(b-a)<.000001) return 0.;
      float t=clamp((x-a)/(b-a),0.,1.);
      return t*t*(3.-2.*t);
    }
    vec3 rainN13(float p) {
      vec3 p3=fract(vec3(p)*vec3(.1031,.11369,.13787));
      p3+=dot(p3,p3.yzx+19.19);
      return fract(vec3((p3.x+p3.y)*p3.z,(p3.x+p3.z)*p3.y,(p3.y+p3.z)*p3.x));
    }
    float rainN(float t) { return fract(sin(t*12345.564)*7658.76); }
    float rainSaw(float b,float t) { return rainS(0.,b,t)*rainS(1.,b,t); }
    vec2 rainLayer(vec2 p,float t) {
      vec2 original=p, a=vec2(6.,1.), grid=a*2.;
      p.y+=t*.75;
      vec2 id=floor(p*grid);
      p.y+=rainN(id.x);
      id=floor(p*grid);
      vec3 n=rainN13(id.x*35.2+id.y*2376.1);
      vec2 st=fract(p*grid)-vec2(.5,0.);
      float x=n.x-.5, y=original.y*20.;
      x+=sin(y+sin(y))*(.5-abs(x))*(n.z-.5);
      x*=.7;
      y=(rainSaw(.85,fract(t+n.z))-.5)*.9+.5;
      float d=length((st-vec2(x,y))*a.yx);
      float mainDrop=rainS(.4,0.,d);
      float r=sqrt(max(0.,rainS(1.,y,st.y)));
      float cd=abs(st.x-x);
      float trail=rainS(.23*r,.15*r*r,cd);
      float front=rainS(-.02,.02,st.y-y);
      trail*=front*r*r;
      y=fract(original.y*10.)+(st.y-.5);
      float droplets=rainS(.3,0.,length(st-vec2(x,y)));
      return vec2(mainDrop+droplets*r*front,trail);
    }
    float rainStatic(vec2 p,float t) {
      p*=40.;
      vec2 id=floor(p);p=fract(p)-.5;
      vec3 n=rainN13(id.x*107.45+id.y*3543.654);
      float d=length(p-(n.xy-.5)*.7);
      return rainS(.3,0.,d)*fract(n.z*10.)*rainSaw(.025,fract(t+n.z));
    }
    vec2 rainDrops(vec2 p,float t,float l0,float l1,float l2) {
      float s=rainStatic(p,t)*l0;
      vec2 a=rainLayer(p,t)*l1, b=rainLayer(p*1.85,t)*l2;
      return vec2(rainS(.3,1.,s+a.x+b.x),max(a.y*l0,b.y*l1));
    }
    vec3 rainBackdrop(vec2 p,float blur) {
      vec2 q=(p-.5)*vec2(resolution.x/resolution.y,1.);
      vec3 col=mix(color0,color1,clamp(p.y,0.,1.))*.35;
      for(int i=0;i<6;i++) {
        float n=float(i);
        vec2 center=vec2(sin(n*2.3+time*.015)*resolution.x/resolution.y*.4,cos(n*1.7+time*.012)*.4);
        vec2 delta=q-center;
        float radius=.025+blur*.018;
        col+=palette(n*.2)*exp(-dot(delta,delta)/radius)*.7;
      }
      return col;
    }
    vec3 scene() {
      vec2 p=(uv-.5)*vec2(resolution.x/resolution.y,1.), imageUV=uv;
      float T=mod(time,102.), story=rainS(0.,70.,T);
      float t=time*.2;
      float zoom=.5;p*=zoom;
      float minBlur=4.+rainS(.5,1.,story)*3.;
      float maxBlur=6.+rainS(.5,1.,story)*1.5;
      vec2 heartUV=p-vec2(0.,-.1);heartUV.x*=.5;
      float shrink=rainS(110.,70.,T);
      heartUV.y-=sqrt(abs(heartUV.x))*.5*shrink;
      float heart=rainS(.4*shrink,.2*shrink,length(heartUV))*shrink;
      maxBlur-=heart;p*=1.5;t*=.25;
      imageUV=(imageUV-.5)*(.9+zoom*.1)+.5;
      float rainAmount=.65+.35*heart;
      float l0=rainS(-.5,1.,rainAmount)*2., l1=rainS(.25,.75,rainAmount), l2=rainS(0.,.5,rainAmount);
      vec2 drops=rainDrops(p,t,l0,l1,l2), e=vec2(.001,0.);
      vec2 normal=vec2(rainDrops(p+e,t,l0,l1,l2).x,rainDrops(p+e.yx,t,l0,l1,l2).x)-drops.x;
      float focus=mix(maxBlur-drops.y,minBlur,rainS(.1,.2,drops.x));
      vec3 col=rainBackdrop(imageUV+normal,focus);
      float shift=sin((T+3.)*.1)*.5+.5+story;
      col*=mix(vec3(1.),vec3(.8,.9,1.3),shift);
      float flash=sin((T+3.)*.5*sin((T+3.)*5.));
      flash*=pow(max(0.,sin((T+3.)*.5+sin((T+3.)*.5))),10.);
      col*=1.+flash*.08*(1.-story*.9);
      vec2 vignette=imageUV-.5;col*=max(.15,1.-dot(vignette,vignette));
      return mix(pow(max(col,vec3(0.)),vec3(1.2)),col,heart);
    }
  `;
})(window);
