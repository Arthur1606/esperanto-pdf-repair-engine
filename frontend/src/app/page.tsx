"use client";

import { useRef, useState } from "react";
import Spline from "@splinetool/react-spline";
import { Application } from "@splinetool/runtime";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import TextRepairDashboard from "./text_repair_dashboard";

gsap.registerPlugin(useGSAP);

export default function EntryExperience() {
  const containerRef = useRef<HTMLDivElement>(null);
  const textRef = useRef<HTMLHeadingElement>(null);
  const splineAppRef = useRef<Application | null>(null);
  
  const [isIntroDone, setIsIntroDone] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);

  const onLoad = (app: Application) => {
    splineAppRef.current = app;
    // Damos un pequeño respiro antes de iniciar la historia
    setTimeout(() => {
      setIsLoaded(true);
    }, 500);
  };

  useGSAP(() => {
    if (!isLoaded) return;

    // Timeline Maestro: Intenso pero breve (0-5 segundos)
    const tl = gsap.timeline({
      onComplete: () => {
        setIsIntroDone(true);
      }
    });

    // Acto I: El lenguaje se construye
    tl.fromTo(textRef.current, 
      { filter: "blur(30px)", opacity: 0, scale: 1.1, letterSpacing: "1em" },
      { filter: "blur(0px)", opacity: 1, scale: 1, letterSpacing: "-0.05em", duration: 1.5, ease: "expo.out" }
    );

    // Acto II: TEKIRA emerge (Aparición de la malla 3D)
    tl.fromTo(".spline-wrapper", 
      { scale: 0.8, filter: "blur(20px)", opacity: 0 },
      { scale: 1, filter: "blur(0px)", opacity: 1, duration: 1.5, ease: "power3.out" },
      "-=1.0" // Superposición para mayor dinamismo
    );

    // Acto III: El espacio respira y revela el Studio
    // Transición fluida a la herramienta de utilidad
    tl.to([textRef.current, ".spline-wrapper"], {
      opacity: 0,
      scale: 1.1,
      filter: "blur(10px)",
      duration: 1,
      ease: "power2.inOut",
      delay: 1 // Pausa dramática breve antes de entrar
    });

  }, { scope: containerRef, dependencies: [isLoaded] });

  // Acto IV: Transición a la Utilidad (Sin bloqueos)
  // Cuando la narrativa termina, entregamos inmediatamente la herramienta al usuario.
  if (isIntroDone) {
    return (
      <div className="animate-in fade-in duration-1000">
        <TextRepairDashboard />
      </div>
    );
  }

  return (
    <div ref={containerRef} className="h-screen w-full bg-slate-950 overflow-hidden relative flex items-center justify-center">
      {/* Background Spline (Artefacto TEKIRA) */}
      <div className="spline-wrapper absolute inset-0 flex items-center justify-center pointer-events-none z-0 opacity-0">
        {/* Escena abstracta de prueba en Spline para el prototipo */}
        <Spline 
          scene="https://prod.spline.design/6Wq1Q7YGyM-iab9i/scene.splinecode" 
          onLoad={onLoad} 
        />
      </div>

      {/* Foreground Typography */}
      <h1 
        ref={textRef} 
        className="text-white text-4xl md:text-6xl font-medium z-10 opacity-0 mix-blend-difference"
      >
        ESPERANTO LANGUAGE STUDIO
      </h1>
      
      {/* Estado de carga oculto */}
      {!isLoaded && (
        <div className="absolute inset-0 bg-slate-950 z-50 flex items-center justify-center transition-opacity duration-500">
          <div className="w-2 h-2 rounded-full bg-slate-700 animate-ping"></div>
        </div>
      )}
    </div>
  );
}
