"use client";
import { useRef, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Spline from '@splinetool/react-spline';
import { Application } from '@splinetool/runtime';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { useGSAP } from '@gsap/react';

gsap.registerPlugin(ScrollTrigger);

export default function SplineGSAPHero() {
  const containerRef = useRef<HTMLDivElement>(null);
  const splineAppRef = useRef<Application | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const router = useRouter();

  const onLoad = (app: Application) => {
    splineAppRef.current = app;
    setIsLoaded(true);
  };

  useGSAP(() => {
    if (!isLoaded || !splineAppRef.current) return;

    const tl = gsap.timeline({
      scrollTrigger: {
        trigger: containerRef.current,
        start: "top top",
        end: "+=2000",
        scrub: 1,
        pin: true,
      }
    });

    // Fade out text while scrolling down
    tl.to(".hero-content", {
      opacity: 0,
      y: -50,
      duration: 0.5,
    }, 0);

    // If there's an object to rotate in Spline (e.g. 'Cube', 'Monolith')
    // tl.to({}, {
    //   duration: 1,
    //   onUpdate: function() {
    //     const obj = splineAppRef.current?.findObjectByName('Monolith');
    //     if(obj) obj.rotation.y = tl.progress() * Math.PI * 2;
    //   }
    // }, 0);

  }, { scope: containerRef, dependencies: [isLoaded] });

  const handleEnterStudio = () => {
    setIsTransitioning(true);
    // Animate everything out
    gsap.to(containerRef.current, {
      opacity: 0,
      scale: 1.05,
      duration: 1.2,
      ease: "power3.inOut",
      onComplete: () => {
        router.push("/app");
      }
    });
  };

  return (
    <div ref={containerRef} className="h-screen w-full relative bg-[#050505] overflow-hidden">
      {/* Loading State */}
      {!isLoaded && (
        <div className="absolute inset-0 flex items-center justify-center z-50 bg-[#050505]">
          <div className="flex flex-col items-center gap-4">
            <div className="w-12 h-12 border-2 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin" />
            <div className="text-indigo-500/50 text-sm font-mono tracking-widest uppercase">Inicializando TEKIRA Engine</div>
          </div>
        </div>
      )}

      {/* Spline Background */}
      <div className="absolute inset-0 z-0 pointer-events-none opacity-60">
        <Spline 
          scene="https://prod.spline.design/6Wq1Q7YGyM-iab9i/scene.splinecode" 
          onLoad={onLoad} 
        />
      </div>

      {/* UI Overlay */}
      <div className="absolute inset-0 z-10 flex flex-col justify-between p-8 pointer-events-none">
        <header className="flex justify-between items-center w-full max-w-7xl mx-auto">
          <div className="text-white/80 font-bold tracking-widest text-sm uppercase">Esperanto Studio</div>
          <div className="text-white/40 font-mono text-xs">v2.0.0-rc</div>
        </header>

        <div className="hero-content flex flex-col items-center text-center max-w-4xl mx-auto space-y-6">
          <div className="px-4 py-1.5 rounded-full border border-indigo-500/30 bg-indigo-500/10 backdrop-blur-md text-indigo-300 text-xs font-semibold tracking-wider uppercase mb-4">
            Powered by TEKIRA Core
          </div>
          <h1 className="text-5xl md:text-8xl font-bold tracking-tighter text-white bg-clip-text text-transparent bg-gradient-to-b from-white to-white/40">
            El lenguaje,<br/>restaurado.
          </h1>
          <p className="text-lg md:text-xl text-slate-400 font-light max-w-2xl mx-auto">
            Auditoría, corrección y preservación Unicode de nivel profesional para literatura en Esperanto. Una experiencia diseñada para la precisión.
          </p>
          
          <div className="pt-8 pointer-events-auto">
            <button 
              onClick={handleEnterStudio}
              disabled={isTransitioning || !isLoaded}
              className="relative group overflow-hidden rounded-full bg-white text-black px-8 py-4 font-semibold text-sm uppercase tracking-widest transition-all hover:scale-105 active:scale-95 disabled:opacity-50 disabled:hover:scale-100"
            >
              <span className="relative z-10 flex items-center gap-3">
                {isTransitioning ? "Iniciando Secuencia..." : "Enter Studio"}
                {!isTransitioning && (
                  <svg className="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" /></svg>
                )}
              </span>
              <div className="absolute inset-0 bg-indigo-100 transform scale-x-0 group-hover:scale-x-100 transition-transform origin-left" />
            </button>
          </div>
        </div>

        <footer className="flex justify-between items-end w-full max-w-7xl mx-auto pb-4">
          <div className="text-white/30 text-xs">Desliza para explorar arquitectura ↓</div>
          <div className="text-white/30 text-xs font-mono">SYS.STATUS: ONLINE</div>
        </footer>
      </div>
      
      {/* Scroll indicator overlay effect */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-[#050505] to-transparent z-10 pointer-events-none" />
    </div>
  );
}
