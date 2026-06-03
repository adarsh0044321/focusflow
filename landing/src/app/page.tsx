"use client";

import React, { useState, useEffect, useRef } from "react";
import { 
  motion, 
  AnimatePresence, 
  useScroll, 
  useTransform, 
  useMotionValue, 
  useSpring,
  useMotionTemplate
} from "framer-motion";
import { 
  Zap, Monitor, Clock, Target, Shield, 
  Sparkles, BookOpen, Flame, Code, Check
} from "lucide-react";

// --- Orbiting Particles Canvas Component (Mental focus signals) ---
function CalmOrbitBackground({ scrollProgress }: { scrollProgress: number }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mouseRef = useRef({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      mouseRef.current.x = e.clientX;
      mouseRef.current.y = e.clientY;
    };
    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener("resize", handleResize);

    class Dot {
      angle: number;
      radius: number;
      speed: number;
      size: number;
      color: string;

      constructor(index: number) {
        this.angle = Math.random() * Math.PI * 2;
        this.radius = 60 + Math.random() * 160;
        this.speed = 0.003 + Math.random() * 0.006;
        this.size = Math.random() * 1.6 + 0.4;
        this.color = index % 2 === 0 ? "rgba(59, 130, 246, 0.3)" : "rgba(168, 85, 247, 0.25)";
      }

      update(calmFactor: number) {
        this.angle += this.speed * (0.1 + calmFactor * 0.9);
      }

      draw(targetX: number, targetY: number, calmFactor: number) {
        if (!ctx) return;
        
        const opacity = calmFactor * 0.7;
        if (opacity <= 0.01) return;

        const x = targetX + Math.cos(this.angle) * this.radius;
        const y = targetY + Math.sin(this.angle) * this.radius;

        ctx.beginPath();
        ctx.arc(x, y, this.size, 0, Math.PI * 2);
        ctx.fillStyle = this.color.replace(/[\d\.]+\)$/, `${opacity})`);
        ctx.fill();

        // Calm light connection lines representing focused neural linkages
        if (calmFactor > 0.5) {
          ctx.beginPath();
          ctx.moveTo(targetX, targetY);
          ctx.lineTo(x, y);
          ctx.strokeStyle = `rgba(0, 119, 255, ${(calmFactor - 0.5) * 0.15})`;
          ctx.lineWidth = 0.35;
          ctx.stroke();
        }
      }
    }

    const dots: Dot[] = Array.from({ length: 45 }).map((_, i) => new Dot(i));

    const animate = () => {
      ctx.clearRect(0, 0, width, height);
      
      // Cleansing phase maps scroll 0.2 to 0.5 into calmFactor 0 to 1
      let calmFactor = 0;
      if (scrollProgress > 0.2) {
        calmFactor = Math.min((scrollProgress - 0.2) / 0.3, 1);
      }

      const tx = mouseRef.current.x;
      const ty = mouseRef.current.y;

      dots.forEach((dot) => {
        dot.update(calmFactor);
        dot.draw(tx, ty, calmFactor);
      });

      // Ambient messy yellow/orange pencil scratches during the chaos phase
      if (scrollProgress < 0.25) {
        const chaosFactor = 1 - (scrollProgress / 0.25);
        ctx.fillStyle = `rgba(245, 158, 11, ${chaosFactor * 0.08})`;
        for (let i = 0; i < 15; i++) {
          const rx = Math.random() * width;
          const ry = Math.random() * height;
          ctx.fillRect(rx, ry, Math.random() * 3, Math.random() * 1.5);
        }
      }

      animationFrameId = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      window.removeEventListener("resize", handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, [scrollProgress]);

  return <canvas ref={canvasRef} className="absolute inset-0 w-full h-full pointer-events-none z-0" />;
}

// --- Distractions Configuration ---
const distractions = [
  {
    text: "Mock Test #4: 92/300. (Percentile: 84% - FAILED Cutoff)",
    organizedText: "Mock Test #9: 268/300 (IIT B CS Safe)",
    type: "sticky-red",
    x: 12, y: 16, rotate: -6,
    targetX: 10, targetY: 18
  },
  {
    text: "Telegram: 'Bro check this JEE memes leak' (140 pings)",
    organizedText: "Telegram: Notifications Blocked (Stealth Mode)",
    type: "sticky-orange",
    x: 72, y: 12, rotate: 4,
    targetX: 10, targetY: 30
  },
  {
    text: "Organic Chemistry: CANNOT REMEMBER CANNIZZARO!",
    organizedText: "Cannizzaro Mechanism: Cached in Memory Journal",
    type: "sticky-yellow",
    x: 82, y: 42, rotate: -9,
    targetX: 10, targetY: 42
  },
  {
    text: "Goal: 8h revision. Actual: 2.2h. FAILED.",
    organizedText: "Daily Revision: 8.5 Hours Completed",
    type: "sticky-red",
    x: 8, y: 56, rotate: 5,
    targetX: 10, targetY: 54
  },
  {
    text: "JEE Mains Session 1: 42 Days Left (PANIC)",
    organizedText: "Syllabus Checklist: 100% Core Ready",
    type: "sticky-yellow",
    x: 48, y: 82, rotate: 3,
    targetX: 10, targetY: 66
  },
  {
    text: "Integrate: sec³(x) dx (Too lengthy, skipped)",
    organizedText: "Calculus Module: Integration Mastery Active",
    type: "sticky-yellow",
    x: 22, y: 78, rotate: -5,
    targetX: 80, targetY: 22
  },
  {
    text: "Reddit: 'Is 96 percentile enough for NIT CS?'",
    organizedText: "System Guard: Reddit Redirect Blocked",
    type: "social",
    x: 65, y: 78, rotate: 6,
    targetX: 80, targetY: 34
  },
  {
    text: "15 Open Tabs: 'IIT B Cutoffs', 'college predictors'...",
    organizedText: "Workspace Tabs: 1 Active (FocusFlow HUD)",
    type: "tabs",
    x: 44, y: 10, rotate: -3,
    targetX: 80, targetY: 46
  },
  {
    text: "Sleep warning: 4.2 hours average this week",
    organizedText: "Recovery Stats: 7.5 Hours Sleep (Calibrated)",
    type: "warning",
    x: 82, y: 26, rotate: 8,
    targetX: 80, targetY: 58
  }
];

// --- Isolated Distraction Note Component (Resolves Hook Rule issues) ---
interface DistractionCardProps {
  distraction: typeof distractions[0];
  scrollYProgress: any;
}

function DistractionCard({ distraction, scrollYProgress }: DistractionCardProps) {
  const left = useTransform(scrollYProgress, [0.18, 0.35], [`${distraction.x}%`, `${distraction.targetX}%`]);
  const top = useTransform(scrollYProgress, [0.18, 0.35], [`${distraction.y}%`, `${distraction.targetY}%`]);
  const rotate = useTransform(scrollYProgress, [0.18, 0.35], [distraction.rotate, 0]);
  const scale = useTransform(scrollYProgress, [0.18, 0.35], [1, 0.9]);
  
  const bg = useTransform(
    scrollYProgress,
    [0.18, 0.35],
    [
      distraction.type === "sticky-red" ? "rgba(254, 226, 226, 0.95)" :
      distraction.type === "sticky-orange" ? "rgba(255, 237, 213, 0.95)" :
      distraction.type === "sticky-yellow" ? "rgba(254, 243, 199, 0.95)" :
      "rgba(24, 24, 27, 0.85)",
      "rgba(15, 15, 20, 0.75)"
    ]
  );

  const textCol = useTransform(
    scrollYProgress,
    [0.18, 0.35],
    [
      distraction.type === "sticky-red" ? "#991b1b" :
      distraction.type === "sticky-orange" ? "#9a3412" :
      distraction.type === "sticky-yellow" ? "#92400e" :
      "#a1a1aa",
      "#10b981"
    ]
  );

  const borderCol = useTransform(
    scrollYProgress,
    [0.18, 0.35],
    [
      distraction.type === "sticky-red" ? "rgba(252, 165, 165, 0.5)" :
      distraction.type === "sticky-orange" ? "rgba(253, 186, 116, 0.5)" :
      distraction.type === "sticky-yellow" ? "rgba(252, 211, 77, 0.5)" :
      "rgba(255, 255, 255, 0.05)",
      "rgba(16, 185, 129, 0.25)"
    ]
  );

  const [isOrganized, setIsOrganized] = useState(false);
  useEffect(() => {
    return scrollYProgress.onChange((v: number) => {
      setIsOrganized(v > 0.28);
    });
  }, [scrollYProgress]);

  const isSticky = distraction.type.startsWith("sticky");

  return (
    <motion.div
      style={{
        left,
        top,
        rotate,
        scale,
        backgroundColor: bg,
        color: textCol,
        borderColor: borderCol,
      }}
      className={`absolute p-4 rounded-xl border shadow-xl z-20 flex items-center gap-2.5 w-[280px] backdrop-blur-md transition-all duration-300 ${
        !isOrganized && isSticky ? "font-handwriting font-bold text-sm shadow-amber-950/20 animate-shake" : "font-mono text-[10px]"
      }`}
    >
      <span className={`w-2 h-2 rounded-full ${isOrganized ? "bg-emerald-500 animate-pulse" : distraction.type === "sticky-red" ? "bg-red-600 animate-pulse" : "bg-amber-500"}`} />
      <span className="flex-1 whitespace-normal leading-relaxed">
        {isOrganized ? distraction.organizedText : distraction.text}
      </span>
    </motion.div>
  );
}

// --- Isolated Heatmap Row Component (Resolves Hook Rule issues) ---
interface HeatmapRowProps {
  row: number;
  scrollYProgress: any;
}

function HeatmapRow({ row, scrollYProgress }: HeatmapRowProps) {
  const rowStart = 0.74 + row * 0.015;
  const opacity = useTransform(scrollYProgress, [rowStart, rowStart + 0.06], [0, 1]);
  const scale = useTransform(scrollYProgress, [rowStart, rowStart + 0.06], [0.85, 1]);

  return (
    <motion.div
      style={{ opacity, scale }}
      className="flex gap-1.5"
    >
      {Array.from({ length: 15 }).map((_, col) => {
        const val = Math.floor(Math.sin((row + col) * 0.45) * 5) + 3;
        const opacityVal = val <= 0 ? 0.04 : val >= 6 ? 0.95 : val * 0.18;
        const bgStyle = {
          backgroundColor: val <= 0 ? "rgba(255,255,255,0.03)" : `rgba(59, 130, 246, ${opacityVal})`
        };
        return (
          <div
            key={col}
            style={bgStyle}
            className="aspect-square w-full rounded-[2px] transition duration-200 hover:scale-125 cursor-pointer relative group"
          >
            <div className="absolute bottom-6 left-1/2 transform -translate-x-1/2 hidden group-hover:block bg-zinc-950 border border-white/10 px-2 py-1 rounded text-[8px] font-mono whitespace-nowrap text-white z-50">
              Study Block: {val <= 0 ? 0 : val} hrs
            </div>
          </div>
        );
      })}
    </motion.div>
  );
}

// --- Main Page Component ---
export default function Home() {
  const containerRef = useRef<HTMLDivElement>(null);
  
  // Track scroll progress across the container
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"]
  });

  // Track mouse coordinates
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  const glowX = useSpring(mouseX, { stiffness: 90, damping: 22 });
  const glowY = useSpring(mouseY, { stiffness: 90, damping: 22 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      mouseX.set(e.clientX);
      mouseY.set(e.clientY);
    };
    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, [mouseX, mouseY]);

  // Sync scrollVal state for React rendering conditional blocks
  const [scrollVal, setScrollVal] = useState(0);
  useEffect(() => {
    return scrollYProgress.onChange((v) => setScrollVal(v));
  }, [scrollYProgress]);

  // Mock score count-up calculation
  const [scoreVal, setScoreVal] = useState(92);
  const scoreCountTransform = useTransform(scrollYProgress, [0.24, 0.45], [92, 268]);
  useEffect(() => {
    return scoreCountTransform.onChange((v) => {
      setScoreVal(Math.floor(v));
    });
  }, [scoreCountTransform]);

  // Streak counter mapping
  const [streakVal, setStreakVal] = useState(1);
  const streakCountTransform = useTransform(scrollYProgress, [0.76, 0.90], [1, 30]);
  useEffect(() => {
    return streakCountTransform.onChange((v) => {
      setStreakVal(Math.max(Math.floor(v), 1));
    });
  }, [streakCountTransform]);

  // Socratic Solver steps calculation
  const [solverStep, setSolverStep] = useState(0);
  useEffect(() => {
    if (scrollVal >= 0.52 && scrollVal < 0.78) {
      const step = Math.min(Math.floor((scrollVal - 0.52) / 0.04), 5);
      setSolverStep(step);
    } else {
      setSolverStep(0);
    }
  }, [scrollVal]);

  // Pomodoro Focus Timer State
  const [timerSeconds, setTimerSeconds] = useState(1500); // 25 mins
  const [timerRunning, setTimerRunning] = useState(false);

  useEffect(() => {
    let interval: any;
    if (timerRunning && timerSeconds > 0) {
      interval = setInterval(() => {
        setTimerSeconds((prev) => (prev > 0 ? prev - 1 : 1500));
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [timerRunning, timerSeconds]);

  const formatTimer = (secs: number) => {
    const mins = Math.floor(secs / 60);
    const s = secs % 60;
    return `${mins.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  // Copied math formula alert state
  const [isCopied, setIsCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText("R_eq = (1 + \u22155) \u2215 2");
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  // Timer stabilizing jitter simulation
  const [timerJitter, setTimerJitter] = useState({ x: 0, y: 0 });
  useEffect(() => {
    if (scrollVal >= 0.18 && scrollVal < 0.45) {
      const interval = setInterval(() => {
        const factor = 1 - (scrollVal - 0.18) / 0.27;
        const maxOffset = Math.max(factor * 12, 0); // Max 12px jitter fading to 0
        setTimerJitter({
          x: (Math.random() - 0.5) * maxOffset,
          y: (Math.random() - 0.5) * maxOffset
        });
      }, 55);
      return () => clearInterval(interval);
    } else {
      setTimerJitter({ x: 0, y: 0 });
    }
  }, [scrollVal]);

  // --- Scroll Transformations for Phase elements ---
  
  // Phase 1 (Chaos Intro Title)
  const heroTextOpacity = useTransform(scrollYProgress, [0, 0.16], [1, 0]);
  const heroTextScale = useTransform(scrollYProgress, [0, 0.16], [1, 0.94]);

  // Background Grid transition
  const gridChaosOpacity = useTransform(scrollYProgress, [0, 0.22, 0.28], [1, 0.5, 0]);
  const gridCalmOpacity = useTransform(scrollYProgress, [0.22, 0.35], [0, 1]);

  // Phase 2 (Focus Timer)
  const timerOpacity = useTransform(scrollYProgress, [0.18, 0.24, 0.44, 0.49], [0, 1, 1, 0]);
  const timerScale = useTransform(scrollYProgress, [0.20, 0.44], [0.85, 1.05]);
  const timerBlurValue = useTransform(scrollYProgress, [0.18, 0.40], [14, 0]);
  const timerBlur = useMotionTemplate`blur(${timerBlurValue}px)`;

  // Cleansing visual transformations (Mock Score improves, Notes organize)
  const cleansingOpacity = useTransform(scrollYProgress, [0.24, 0.30, 0.45, 0.49], [0, 1, 1, 0]);
  const cleansingScale = useTransform(scrollYProgress, [0.25, 0.45], [0.9, 1.0]);

  // Phase 3 (Self-Assembling App Interface)
  const appWorkspaceOpacity = useTransform(scrollYProgress, [0.46, 0.52, 0.74, 0.78], [0, 1, 1, 0]);
  const appWorkspaceScale = useTransform(scrollYProgress, [0.48, 0.74], [0.93, 1.02]);
  
  const appTopBarY = useTransform(scrollYProgress, [0.46, 0.53], [-120, 0]);
  const appTopBarOpacity = useTransform(scrollYProgress, [0.46, 0.53], [0, 1]);
  
  const appLeftPanelX = useTransform(scrollYProgress, [0.48, 0.56], [-220, 0]);
  const appLeftPanelOpacity = useTransform(scrollYProgress, [0.48, 0.56], [0, 1]);
  
  const appRightPanelX = useTransform(scrollYProgress, [0.50, 0.60], [220, 0]);
  const appRightPanelOpacity = useTransform(scrollYProgress, [0.50, 0.60], [0, 1]);
  
  const appBottomBarY = useTransform(scrollYProgress, [0.52, 0.63], [120, 0]);
  const appBottomBarOpacity = useTransform(scrollYProgress, [0.52, 0.63], [0, 1]);

  // Phase 4 (Mastery Analytics Showcase)
  const masteryDashboardOpacity = useTransform(scrollYProgress, [0.74, 0.81, 0.94, 0.98], [0, 1, 1, 0]);
  const masteryDashboardScale = useTransform(scrollYProgress, [0.74, 0.84], [0.95, 1.05]);
  
  const strokeOffset = useTransform(scrollYProgress, [0.76, 0.88], [550, 0]);
  
  const flameColor = useTransform(scrollYProgress, [0.76, 0.90], ["rgba(150, 150, 150, 0.15)", "rgba(249, 115, 22, 1)"]);
  const flameScale = useTransform(scrollYProgress, [0.76, 0.90], [0.88, 1.25]);

  // Phase 5 (Final Editorial CTA)
  const finalCtaOpacity = useTransform(scrollYProgress, [0.91, 0.96], [0, 1]);
  const finalCtaScale = useTransform(scrollYProgress, [0.91, 0.96], [0.96, 1]);

  // Dynamic Cursor glow styling ( desk lamp transitions to command center )
  const glowColor = useTransform(scrollYProgress, [0, 0.22, 0.46], ["rgba(245, 158, 11, 0.16)", "rgba(0, 119, 255, 0.15)", "rgba(123, 47, 247, 0.08)"]);
  const glowSize = useTransform(scrollYProgress, [0, 0.22, 0.46], ["340px", "490px", "640px"]);
  const glowBlur = useTransform(scrollYProgress, [0, 0.22, 0.46], ["80px", "115px", "145px"]);

  // Resolve Hook Rule by declaring the Motion Template at the top level
  const glowFilter = useMotionTemplate`blur(${glowBlur})`;

  return (
    <div ref={containerRef} className="relative h-[650vh] w-full bg-black text-white font-sans selection:bg-blue-500/20 selection:text-blue-200">
      
      {/* Sticky Viewport Container */}
      <div className="sticky top-0 h-screen w-full overflow-hidden flex flex-col items-center justify-center">
        
        {/* Dynamic Background Grids */}
        <motion.div style={{ opacity: gridChaosOpacity }} className="absolute inset-0 bg-grid-chaos pointer-events-none z-0" />
        <motion.div style={{ opacity: gridCalmOpacity }} className="absolute inset-0 bg-grid-overlay pointer-events-none z-0" />
 
        {/* Ambient static lighting */}
        <div className="absolute top-[-10%] left-[-15%] w-[60%] h-[60%] bg-blue-500/10 rounded-full blur-[180px] pointer-events-none z-0" />
        <div className="absolute bottom-[-10%] right-[-15%] w-[60%] h-[60%] bg-purple-500/5 rounded-full blur-[180px] pointer-events-none z-0" />
 
        {/* 2 AM Desk Lamp / HUD follow glow */}
        <motion.div
          style={{
            x: glowX,
            y: glowY,
            translateX: "-50%",
            translateY: "-50%",
            width: glowSize,
            height: glowSize,
            backgroundColor: glowColor,
            filter: glowFilter,
          }}
          className={`fixed top-0 left-0 rounded-full pointer-events-none z-0 ${
            scrollVal < 0.22 ? "animate-flicker" : ""
          }`}
        />
 
        {/* Orbiting particles background */}
        <CalmOrbitBackground scrollProgress={scrollVal} />
 
        {/* --- HEADER --- */}
        <header className="absolute top-0 left-0 w-full z-50 p-8 flex items-center justify-between border-b border-white/5 bg-black/20 backdrop-blur-md">
          <div className="flex items-center space-x-2">
            <img src="/logo.png" alt="FocusFlow Logo" className="w-6 h-6 rounded-md border border-white/10 shadow-lg object-cover" />
            <span className="font-bold text-sm tracking-tight text-white font-mono">FocusFlow</span>
          </div>
          
          <div className="flex items-center space-x-6 text-[10px] font-mono tracking-widest text-zinc-500">
            <span>SCROLL PROGRESS: {Math.floor(scrollVal * 100)}%</span>
            <span className="hidden sm:inline-block border border-zinc-800 px-2 py-0.5 rounded text-amber-400 animate-pulse bg-amber-500/5 uppercase">
              {scrollVal < 0.24 ? "2:00 AM Chaos overlay" : scrollVal < 0.74 ? "Holographic Workspace Active" : "Command Center Engaged"}
            </span>
          </div>
        </header>

        {/* ======================================================== */}
        {/* PHASE 1: CHAOS Desk & STICKY NOTES (0.0 - 0.22)          */}
        {/* ======================================================== */}
        <AnimatePresence>
          {scrollVal < 0.24 && (
            <motion.div 
              style={{ opacity: heroTextOpacity, scale: heroTextScale }}
              className="absolute flex flex-col items-center justify-center text-center px-6 max-w-4xl z-10 select-none"
            >
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/25 text-[10px] text-amber-400 font-medium font-mono mb-6 animate-pulse">
                <Clock className="w-3.5 h-3.5" />
                <span>STUDENT DESK · 2:00 AM · JEE ADVANCED REVISION</span>
              </div>
              <h1 className="text-5xl sm:text-7xl font-black tracking-tighter leading-none text-white uppercase font-sans">
                Lost In The <span className="text-stroke">Formula</span> Noise.
              </h1>
              <p className="text-zinc-500 font-mono text-xs sm:text-sm mt-6 max-w-lg leading-relaxed">
                Failing mock test scores, forgotten mechanisms, Telegram pings, and missed study goals. Scroll down to filter the distractions and trigger deep focus.
              </p>
              
              <div className="mt-12 flex flex-col items-center gap-2 text-zinc-700 font-mono text-[9px] uppercase tracking-widest">
                <span className="animate-pulse">Scroll to organize workspace</span>
                <div className="w-[1px] h-8 bg-zinc-800 mt-2 relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-full h-1/2 bg-zinc-400 animate-[bounce_1.5s_infinite]" />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Scattered Sticky Notes that organize on scroll */}
        {distractions.map((d, i) => (
          <DistractionCard 
            key={i} 
            distraction={d} 
            scrollYProgress={scrollYProgress} 
          />
        ))}

        {/* ======================================================== */}
        {/* PHASE 2: CLEANSING & TIMER STABILIZATION (0.18 - 0.49)   */}
        {/* ======================================================== */}
        <AnimatePresence>
          {scrollVal >= 0.18 && scrollVal < 0.49 && (
            <motion.div
              style={{
                opacity: timerOpacity,
                scale: timerScale,
                filter: timerBlur,
                x: timerJitter.x,
                y: timerJitter.y,
              }}
              className="absolute text-center select-none font-mono z-10 flex flex-col items-center justify-center"
            >
              <span className="text-[9px] text-zinc-500 uppercase tracking-widest block mb-4 border border-zinc-850 px-3 py-1 rounded bg-zinc-900/10">
                {scrollVal < 0.32 ? "Absorbing chaos elements" : scrollVal < 0.40 ? "Stabilizing workspace frequency" : "Deep Coherence Established"}
              </span>
              <h2 className="text-7xl sm:text-9xl font-extrabold tracking-tighter text-white">
                25:00
              </h2>
              <span className="text-[10px] text-blue-400/80 mt-4 block font-sans tracking-wide">
                {scrollVal < 0.30 ? "Warm lamp fading · Shaking notes aligning" : scrollVal < 0.42 ? "Holographic grid building..." : "Ambient noise muted · Focus companion loaded"}
              </span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Emerging Organized Score Card and Status */}
        <AnimatePresence>
          {scrollVal >= 0.24 && scrollVal < 0.49 && (
            <motion.div
              style={{
                opacity: cleansingOpacity,
                scale: cleansingScale,
              }}
              className="absolute bottom-[10%] flex flex-col sm:flex-row gap-4 max-w-xl z-20"
            >
              <div className="p-4 glass-panel border-emerald-500/20 rounded-xl text-left flex items-start gap-3 w-64">
                <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400 mt-0.5">
                  <Target className="w-4 h-4" />
                </div>
                <div>
                  <span className="text-[9px] text-zinc-500 block uppercase font-mono mb-0.5">MOCK EXAM RESULT</span>
                  <div className="text-lg font-bold font-mono text-emerald-400">
                    {scoreVal} / 300
                  </div>
                  <div className="text-[8px] text-emerald-500/80 font-mono mt-0.5">
                    {scoreVal < 150 ? "JEE Prep Index: Poor" : scoreVal < 240 ? "JEE Prep Index: Climbing" : "IIT Bombay CS Safe State"}
                  </div>
                </div>
              </div>
              
              <div className="p-4 glass-panel border-blue-500/20 rounded-xl text-left flex items-start gap-3 w-64">
                <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-400 mt-0.5">
                  <BookOpen className="w-4 h-4" />
                </div>
                <div>
                  <span className="text-[9px] text-zinc-500 block uppercase font-mono mb-0.5">WORKSPACE STATUS</span>
                  <div className="text-lg font-bold font-mono text-blue-400">System Sorted</div>
                  <div className="text-[8px] text-zinc-400 font-mono mt-0.5">Handwritten stickies parsed to database log.</div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ======================================================== */}
        {/* PHASE 3: DYNAMIC HUD WORKSPACE ASSEMBLY (0.46 - 0.78)     */}
        {/* ======================================================== */}
        <AnimatePresence>
          {scrollVal >= 0.46 && scrollVal < 0.78 && (
            <motion.div
              style={{
                opacity: appWorkspaceOpacity,
                scale: appWorkspaceScale,
              }}
              className="absolute w-full max-w-5xl h-[480px] p-2 flex flex-col justify-between z-10"
            >
              {/* Assembling Top Bar */}
              <motion.div
                style={{ y: appTopBarY, opacity: appTopBarOpacity }}
                className="w-full h-11 border border-white/10 bg-zinc-950/80 backdrop-blur-md rounded-xl p-3 flex items-center justify-between font-mono text-[10px]"
              >
                <div className="flex items-center space-x-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-red-500/70"></span>
                  <span className="w-2.5 h-2.5 rounded-full bg-yellow-500/70"></span>
                  <span className="w-2.5 h-2.5 rounded-full bg-green-500/70"></span>
                  <span className="text-zinc-500 ml-4">FocusFlow Stealth Overlay HUD - Command Workspace</span>
                </div>
                <span className="text-emerald-400 flex items-center gap-1.5 font-bold">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
                  Stealth Mode Connected
                </span>
              </motion.div>

              {/* Main App Body */}
              <div className="flex-1 flex gap-4 my-4 h-[350px]">
                
                {/* Left Panel: Mode Controls */}
                <motion.div
                  style={{ x: appLeftPanelX, opacity: appLeftPanelOpacity }}
                  className="w-1/3 border border-white/10 bg-zinc-950/80 backdrop-blur-md rounded-2xl p-5 flex flex-col justify-between"
                >
                  <div className="space-y-4">
                    <span className="text-[9px] font-mono tracking-widest text-zinc-500 block uppercase">HUD Mode Switcher</span>
                    
                    <div className="space-y-2">
                      <div className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-xl flex items-center justify-between text-xs font-mono">
                        <span className="text-blue-400 font-bold">Stealth HUD</span>
                        <Zap className="w-3.5 h-3.5 text-blue-400" />
                      </div>
                      <div className="p-3 bg-zinc-900/30 border border-white/5 hover:border-white/15 rounded-xl flex items-center justify-between text-xs text-zinc-400 font-mono transition">
                        <span>Hybrid Solve</span>
                        <Monitor className="w-3.5 h-3.5 text-zinc-500" />
                      </div>
                      <div className="p-3 bg-zinc-900/30 border border-white/5 hover:border-white/15 rounded-xl flex items-center justify-between text-xs text-zinc-400 font-mono transition">
                        <span>Offline Engine</span>
                        <Shield className="w-3.5 h-3.5 text-zinc-500" />
                      </div>
                    </div>
                  </div>

                  {/* Sliders */}
                  <div className="space-y-3 pt-4 border-t border-white/5 font-mono">
                    <div>
                      <div className="flex justify-between text-[9px] text-zinc-500 mb-1">
                        <span>TRANSPARENCY</span>
                        <span>80%</span>
                      </div>
                      <div className="w-full h-1 bg-zinc-800 rounded-full overflow-hidden">
                        <div className="bg-gradient-to-r from-blue-500 to-purple-500 h-full w-[80%] rounded-full"></div>
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between text-[9px] text-zinc-500 mb-1">
                        <span>COGNITIVE SHIELD</span>
                        <span>MAX</span>
                      </div>
                      <div className="w-full h-1 bg-zinc-800 rounded-full overflow-hidden">
                        <div className="bg-gradient-to-r from-purple-500 to-pink-500 h-full w-[100%] rounded-full"></div>
                      </div>
                    </div>
                  </div>
                </motion.div>

                {/* Right Panel: AI Socratic Solver Screen */}
                <motion.div
                  style={{ x: appRightPanelX, opacity: appRightPanelOpacity }}
                  className="flex-1 border border-white/10 bg-zinc-950/80 backdrop-blur-md rounded-2xl p-6 flex flex-col justify-between relative overflow-hidden font-mono"
                >
                  <div className="absolute top-0 right-0 w-36 h-36 bg-purple-500/5 rounded-full blur-3xl"></div>
                  
                  <div className="flex items-center justify-between pb-3 border-b border-white/5">
                    <span className="text-[9px] text-zinc-500 uppercase tracking-widest">Socratic AI Engine Solver</span>
                    <span className="text-[9px] text-purple-400 border border-purple-500/20 px-2 py-0.5 rounded bg-purple-500/5">JEE Physics Engine</span>
                  </div>

                  {/* Infinite Resistors Ladder Question */}
                  <div className="flex-1 my-4 space-y-3 text-xs overflow-y-auto leading-relaxed">
                    
                    {solverStep >= 1 && (
                      <div className="text-zinc-400">
                        <span className="text-blue-400 font-bold">OCR Read Success: </span>
                        Find the equivalent resistance of an infinite ladder grid of 1 &Omega; resistors.
                      </div>
                    )}

                    {solverStep >= 2 && (
                      <div className="text-zinc-550 text-[10px]">
                        // Step 1: Slice coordinate grid. R_eq = R + (R * R_eq) &divide; (R + R_eq)
                      </div>
                    )}

                    {solverStep >= 3 && (
                      <div className="text-zinc-300 space-y-1">
                        <div>Since all resistors are 1 &Omega;:</div>
                        <div>R_eq = 1 + R_eq &divide; (1 + R_eq)</div>
                      </div>
                    )}

                    {solverStep >= 4 && (
                      <div className="text-zinc-300">
                        Multiply terms: R_eq&sup2; - R_eq - 1 = 0
                      </div>
                    )}

                    {solverStep >= 5 && (
                      <div className="text-emerald-400 font-bold p-2 bg-emerald-500/5 border border-emerald-500/15 rounded-lg inline-block">
                        Equivalent Resistance R_eq = (1 + &radic;5) &divide; 2 &asymp; 1.618 &Omega; (Golden Ratio)
                      </div>
                    )}

                  </div>

                  {/* Solver Footer */}
                  <div className="flex items-center space-x-3 pt-3 border-t border-white/5 text-[10px]">
                    <button 
                      onClick={handleCopy} 
                      className="bg-zinc-900 border border-white/10 hover:border-blue-500/20 text-zinc-300 px-4 py-2 rounded-lg flex items-center gap-1.5 transition cursor-pointer"
                    >
                      {isCopied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Code className="w-3.5 h-3.5 text-blue-400" />}
                      {isCopied ? "Copied Equation" : "Copy Equation"}
                    </button>
                    <span className="text-zinc-650">Overlay captures screen region automatically</span>
                  </div>
                </motion.div>

              </div>

              {/* Status Footer */}
              <motion.div
                style={{ y: appBottomBarY, opacity: appBottomBarOpacity }}
                className="w-full h-11 border border-white/10 bg-zinc-950/80 backdrop-blur-md rounded-xl p-3 flex items-center justify-between font-mono text-[9px] text-zinc-500"
              >
                <div className="flex items-center space-x-4">
                  <span>MODEL: Phi-3 GGUF (4-bit Local Quantized)</span>
                  <span>·</span>
                  <span>OCR: Custom Math Parser Active (10ms)</span>
                </div>
                <span>MONITOR 1 (MAIN DISPLAY PORT)</span>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ======================================================== */}
        {/* PHASE 4: METRICS & STUDY COMMAND CENTER (0.74 - 0.94)    */}
        {/* ======================================================== */}
        <AnimatePresence>
          {scrollVal >= 0.74 && scrollVal < 0.96 && (
            <motion.div
              style={{
                opacity: masteryDashboardOpacity,
                scale: masteryDashboardScale,
              }}
              className="absolute w-full max-w-5xl grid grid-cols-1 md:grid-cols-2 gap-8 z-10"
            >
              
              {/* Left Column: Consistency Heatmap & Streak Counter */}
              <div className="glass-panel border border-white/10 rounded-2xl p-6 flex flex-col justify-between min-h-[340px]">
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] font-mono tracking-widest text-zinc-500 uppercase">30-Day Revision Consistency</span>
                    
                    {/* Glowing Streak Flame */}
                    <motion.div 
                      style={{ color: flameColor, scale: flameScale }}
                      className="flex items-center space-x-1.5 font-mono font-bold text-xs"
                    >
                      <Flame className="w-4 h-4 fill-current" />
                      <span>{streakVal} DAY STUDY STREAK</span>
                    </motion.div>
                  </div>

                  {/* Heatmap Grid populating dynamically row-by-row */}
                  <div className="grid gap-1.5 py-4">
                    {Array.from({ length: 7 }).map((_, row) => (
                      <HeatmapRow 
                        key={row} 
                        row={row} 
                        scrollYProgress={scrollYProgress} 
                      />
                    ))}
                  </div>
                </div>

                <div className="pt-4 border-t border-white/5 flex justify-between font-mono text-[10px] text-zinc-500">
                  <span>Weekly Dedicated Study: 46.8 hours</span>
                  <span className="text-blue-400">Target Focus Frequency Locked</span>
                </div>
              </div>

              {/* Right Column: Score Trend Self-Drawing SVG */}
              <div className="glass-panel border border-white/10 rounded-2xl p-6 flex flex-col justify-between min-h-[340px] relative overflow-hidden">
                <div className="absolute top-0 right-0 w-36 h-36 bg-blue-500/5 rounded-full blur-3xl"></div>
                
                <div>
                  <span className="text-[10px] font-mono tracking-widest text-zinc-500 uppercase block mb-1">JEE Mock Score Trend</span>
                  <span className="text-2xl font-bold font-mono text-white">Score Growth: 92 &rarr; 268 / 300</span>
                </div>

                {/* Self-drawing SVG container */}
                <div className="flex-1 w-full min-h-[160px] flex items-end py-4">
                  <svg className="w-full h-[140px] overflow-visible" viewBox="0 0 600 140" preserveAspectRatio="none">
                    <line x1="0" y1="35" x2="600" y2="35" stroke="rgba(255,255,255,0.03)" strokeDasharray="4 4" />
                    <line x1="0" y1="70" x2="600" y2="70" stroke="rgba(255,255,255,0.03)" strokeDasharray="4 4" />
                    <line x1="0" y1="105" x2="600" y2="105" stroke="rgba(255,255,255,0.03)" strokeDasharray="4 4" />
                    
                    <defs>
                      <linearGradient id="mastery-gradient" x1="0" y1="0" x2="1" y2="0">
                        <stop offset="0%" stopColor="#3b82f6" />
                        <stop offset="50%" stopColor="#a855f7" />
                        <stop offset="100%" stopColor="#ec4899" />
                      </linearGradient>
                    </defs>

                    <motion.path
                      d="M 10 125 Q 150 110 280 60 T 590 15"
                      fill="none"
                      stroke="url(#mastery-gradient)"
                      strokeWidth="3.5"
                      strokeLinecap="round"
                      strokeDasharray="600"
                      style={{ strokeDashoffset: strokeOffset }}
                    />
                  </svg>
                </div>

                <div className="pt-4 border-t border-white/5 flex justify-between font-mono text-[9px] text-zinc-500 uppercase">
                  <span>Initial: 92 (Failed)</span>
                  <span>Midpoint: 180</span>
                  <span>Current: 268 (IIT B CS Safe)</span>
                </div>
              </div>

            </motion.div>
          )}
        </AnimatePresence>

        {/* ======================================================== */}
        {/* PHASE 5: THE IIT MOMENTUM CTA & MINIMAL DOWNLOAD (0.90 - 1.0) */}
        {/* ======================================================== */}
        <AnimatePresence>
          {scrollVal >= 0.90 && (
            <motion.div
              style={{
                opacity: finalCtaOpacity,
                scale: finalCtaScale,
              }}
              className="absolute flex flex-col items-center justify-center text-center px-6 max-w-4xl z-10"
            >
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/25 text-[10px] text-blue-400 font-medium font-mono mb-6">
                <Sparkles className="w-3.5 h-3.5" />
                <span>COMMAND CENTER LOCK ENGAGED</span>
              </div>
              
              <h2 className="text-5xl sm:text-7xl font-extrabold tracking-tighter leading-none text-white uppercase select-none font-sans">
                Master Your <br />
                <span className="bg-gradient-to-r from-blue-500 via-indigo-400 to-purple-500 bg-clip-text text-transparent">JEE Momentum.</span>
              </h2>
              
              <p className="text-zinc-500 font-mono text-xs sm:text-sm mt-6 max-w-lg leading-relaxed select-none">
                No notification loops. No Telegram alerts. Simply an ultra-stealth study companion built to guide competitive exam aspirants through the dark.
              </p>

              {/* Minimal download button layouts */}
              <div className="mt-10 flex flex-col sm:flex-row items-center gap-4 justify-center w-full max-w-md">
                <a 
                  href="https://github.com/adarsh0044321/focusflow/releases/download/v1.1.0/FocusFlow-v1.1.0-LITE.zip"
                  className="w-full sm:w-auto px-8 py-4 bg-white text-black font-mono font-bold text-xs hover:bg-zinc-200 transition duration-300 rounded-xl shadow-lg shadow-white/5 flex items-center justify-center gap-2 cursor-pointer animate-pulse"
                >
                  <Monitor className="w-4 h-4" />
                  Download FocusFlow v1.1.0
                </a>
                <a 
                  href="https://github.com/adarsh0044321/focusflow" 
                  className="w-full sm:w-auto px-8 py-4 bg-zinc-950 border border-white/10 hover:border-white/20 text-zinc-300 font-mono text-xs transition rounded-xl flex items-center justify-center gap-2 cursor-pointer"
                  target="_blank"
                  rel="noreferrer"
                >
                  <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24" aria-hidden="true">
                    <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.464-1.11-1.464-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.579.688.481C19.137 20.164 22 16.418 22 12c0-5.523-4.477-10-10-10z" />
                  </svg>
                  Inspect Source Code
                </a>
              </div>

              <div className="text-[10px] text-zinc-650 font-mono mt-6 flex items-center justify-center gap-4 select-none">
                <span>Compatible with Windows 10 / 11</span>
                <span>·</span>
                <span>Open Source under MIT</span>
              </div>

              {/* Minimalist Footer inside CTA */}
              <div className="mt-20 border-t border-white/5 pt-8 w-full max-w-md text-[9px] font-mono text-zinc-750 flex justify-between select-none">
                <span>&copy; {new Date().getFullYear()} FocusFlow.</span>
                <span>Created for deep study focus.</span>
              </div>

            </motion.div>
          )}
        </AnimatePresence>

      </div>

    </div>
  );
}
