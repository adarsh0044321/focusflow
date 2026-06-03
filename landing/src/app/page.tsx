"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence, useMotionValue, useSpring } from "framer-motion";
import { 
  Play, Pause, Award, TrendingUp, Zap, Monitor, Clock, Target, 
  Shield, ArrowRight, Activity, ChevronLeft, ChevronRight,
  ClipboardCheck, Check, Sparkles, BookOpen, Flame, UserCheck, Code
} from "lucide-react";

// --- Types for interactive widgets ---
type ChartTab = "hours" | "score" | "distractions";

// --- Particle Background Component for premium floating dots effect ---
function ParticleBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

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

    class Particle {
      x: number;
      y: number;
      size: number;
      speedX: number;
      speedY: number;
      color: string;

      constructor() {
        this.x = Math.random() * width;
        this.y = Math.random() * height;
        this.size = Math.random() * 1.2 + 0.4;
        this.speedX = (Math.random() - 0.5) * 0.15;
        this.speedY = (Math.random() - 0.5) * 0.15;
        this.color = Math.random() > 0.5 ? "rgba(0, 119, 255, 0.25)" : "rgba(123, 47, 247, 0.15)";
      }

      update() {
        this.x += this.speedX;
        this.y += this.speedY;

        if (this.x > width) this.x = 0;
        else if (this.x < 0) this.x = width;

        if (this.y > height) this.y = 0;
        else if (this.y < 0) this.y = height;
      }

      draw() {
        if (!ctx) return;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fillStyle = this.color;
        ctx.fill();
      }
    }

    const particlesArray: Particle[] = [];
    const numberOfParticles = 50;
    for (let i = 0; i < numberOfParticles; i++) {
      particlesArray.push(new Particle());
    }

    const animate = () => {
      ctx.clearRect(0, 0, width, height);
      for (let i = 0; i < particlesArray.length; i++) {
        particlesArray[i].update();
        particlesArray[i].draw();
      }
      animationFrameId = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      window.removeEventListener("resize", handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full pointer-events-none z-0 opacity-60"
    />
  );
}

export default function Home() {
  // Mouse position tracking for ambient follower glow
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  const glowX = useSpring(mouseX, { stiffness: 80, damping: 20 });
  const glowY = useSpring(mouseY, { stiffness: 80, damping: 20 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      mouseX.set(e.clientX);
      mouseY.set(e.clientY);
    };
    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, [mouseX, mouseY]);

  // Timer State in Hero Showcase
  const [timerSeconds, setTimerSeconds] = useState(1500); // 25 mins
  const [timerRunning, setTimerRunning] = useState(true);

  // Analytics tab selection
  const [activeTab, setActiveTab] = useState<ChartTab>("hours");

  // Screenshot Carousel State
  const [carouselIndex, setCarouselIndex] = useState(0);

  // Copied clipboard indicator state
  const [isCopied, setIsCopied] = useState(false);

  // Interactive Heatmap hover state
  const [hoveredDay, setHoveredDay] = useState<{ row: number; col: number; val: number } | null>(null);

  // Run Hero Timer Countdown
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

  // Mock Screenshot Carousel Data
  const carouselSlides = [
    {
      title: "Stealth HUD Control Panel",
      desc: "Compact, glassmorphic controls withTraffic-light actions, global hotkeys, and mode selectors that completely evade screenshot capture using ctypes.",
      tag: "Stealth Technology",
      colors: "from-blue-600/20 to-indigo-600/20",
      content: (
        <div className="w-full h-full flex flex-col justify-between p-6 bg-zinc-950/90 text-left border border-white/10 rounded-2xl relative overflow-hidden font-mono">
          <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/10 rounded-full blur-2xl"></div>
          <div className="flex items-center justify-between border-b border-white/5 pb-3">
            <div className="flex items-center space-x-2">
              <span className="w-3 h-3 rounded-full bg-red-500"></span>
              <span className="w-3 h-3 rounded-full bg-yellow-500"></span>
              <span className="w-3 h-3 rounded-full bg-green-500"></span>
              <span className="text-[10px] text-zinc-500 ml-2">● FocusFlow Controls</span>
            </div>
            <span className="text-[10px] text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded-full bg-emerald-500/5">Stealth Enabled</span>
          </div>
          <div className="my-4 space-y-3">
            <div className="flex justify-between items-center text-xs">
              <span className="text-zinc-400">Capture Mode:</span>
              <span className="text-blue-400 font-bold">Region Selection (800x600)</span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-zinc-400">AI Engine Mode:</span>
              <span className="text-purple-400 font-bold">Hybrid (Offline Ready)</span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-zinc-400">Target Display:</span>
              <span className="text-white">Display 1 (1920x1080)</span>
            </div>
          </div>
          <div className="bg-zinc-900/50 p-3 rounded-xl border border-white/5 space-y-1">
            <span className="text-[9px] text-zinc-500 block">MANUAL QUESTION DRAWER</span>
            <div className="flex items-center space-x-2">
              <div className="flex-1 bg-zinc-950 h-7 rounded border border-white/10 px-2 flex items-center text-[10px] text-zinc-400">what is the limit of x*sin(1/x)...</div>
              <button className="bg-emerald-400 hover:bg-emerald-500 text-black font-bold text-[10px] px-3 h-7 rounded transition cursor-pointer">Send</button>
            </div>
          </div>
        </div>
      )
    },
    {
      title: "Detailed AI Answer Panel",
      desc: "Step-by-step math, science, and coding solutions with final answer extraction, formatted cleanly with scroll bounding and custom Socratic Tutor explanations.",
      tag: "AI Solving Engine",
      colors: "from-purple-600/20 to-pink-600/20",
      content: (
        <div className="w-full h-full flex flex-col justify-between p-6 bg-zinc-950/90 text-left border border-white/10 rounded-2xl relative overflow-hidden font-mono">
          <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/10 rounded-full blur-2xl"></div>
          <div className="flex items-center justify-between border-b border-white/5 pb-3">
            <div className="flex items-space-x-1 flex-row">
              <span className="text-[10px] text-zinc-500">● AI Solution Panel</span>
            </div>
            <span className="text-[10px] text-yellow-400 border border-yellow-500/20 px-2 py-0.5 rounded-full bg-yellow-500/5">Socratic Mode</span>
          </div>
          <div className="my-3 flex-1 overflow-y-auto pr-1 space-y-2">
            <div className="text-[10px] text-emerald-400">Q: Compute the derivative of f(x) = x^2 * ln(x)</div>
            <div className="text-[9px] text-zinc-300 space-y-1 bg-zinc-900/40 p-3 rounded-lg border border-white/5 leading-relaxed">
              <p className="text-zinc-500">// Using the product rule: (u*v)&apos; = u&apos;v + uv&apos;</p>
              <p>1. Let u = x^2  =&gt;  u&apos; = 2x</p>
              <p>2. Let v = ln(x) =&gt;  v&apos; = 1/x</p>
              <p>3. f&apos;(x) = 2x * ln(x) + x^2 * (1/x)</p>
              <p>4. f&apos;(x) = 2x*ln(x) + x</p>
              <p className="text-emerald-400 font-bold mt-1">Answer: f&apos;(x) = x(2ln(x) + 1)</p>
            </div>
          </div>
          <div className="flex items-center space-x-2 pt-2 border-t border-white/5 text-[10px]">
            <button className="bg-zinc-900 border border-white/10 hover:bg-zinc-800 text-zinc-300 px-3 py-1.5 rounded flex items-center gap-1 cursor-pointer">⟳ Re-run</button>
            <button className="bg-zinc-900 border border-white/10 hover:bg-zinc-800 text-zinc-300 px-3 py-1.5 rounded flex items-center gap-1 cursor-pointer">📋 Copy</button>
          </div>
        </div>
      )
    },
    {
      title: "Chronological History Viewer",
      desc: "A fully searchable learning journal compiling past captures. Allows students to search by text keywords and trigger image preview overlay dialogs.",
      tag: "Learning Journal",
      colors: "from-blue-600/20 to-purple-600/20",
      content: (
        <div className="w-full h-full flex flex-col justify-between p-6 bg-zinc-950/90 text-left border border-white/10 rounded-2xl relative overflow-hidden font-mono">
          <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/10 rounded-full blur-2xl"></div>
          <div className="flex items-center justify-between border-b border-white/5 pb-2">
            <span className="text-[10px] text-zinc-500">🔍 Search Learning Journal</span>
            <span className="text-[10px] text-blue-400">34 Entries Saved</span>
          </div>
          <div className="my-2 bg-zinc-900/60 p-2 rounded-lg border border-white/15 flex items-center justify-between">
            <span className="text-[9px] text-zinc-400">Filter: &quot;derivative&quot;</span>
            <span className="text-[8px] text-zinc-600">Enter keyword</span>
          </div>
          <div className="flex-1 overflow-y-auto space-y-1.5 my-1">
            <div className="p-1.5 rounded bg-blue-500/10 border border-blue-500/20 flex justify-between items-center text-[9px]">
              <span className="text-zinc-300">10:44:38 [OFFLINE] Q: Derivative...</span>
              <span className="text-emerald-400 font-bold">Good Quality</span>
            </div>
            <div className="p-1.5 rounded bg-zinc-900 border border-white/5 flex justify-between items-center text-[9px]">
              <span className="text-zinc-400">09:12:15 [ONLINE] Q: Let A = ...</span>
              <span className="text-zinc-500">Weak Quality</span>
            </div>
            <div className="p-1.5 rounded bg-zinc-900 border border-white/5 flex justify-between items-center text-[9px]">
              <span className="text-zinc-400">08:05:04 [OFFLINE] Q: Code debug...</span>
              <span className="text-zinc-500">Manual</span>
            </div>
          </div>
          <button className="w-full mt-2 py-1.5 text-center bg-zinc-900 hover:bg-zinc-800 text-[10px] rounded border border-white/10 text-white font-bold cursor-pointer">🖼️ View Screenshot Popup</button>
        </div>
      )
    }
  ];

  const nextCarousel = () => {
    setCarouselIndex((prev) => (prev + 1) % carouselSlides.length);
  };

  const prevCarousel = () => {
    setCarouselIndex((prev) => (prev - 1 + carouselSlides.length) % carouselSlides.length);
  };

  // Mock clipboard copy helper
  const handleCopyClipboard = () => {
    navigator.clipboard.writeText("powershell -Command \"[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms'); [System.Windows.Forms.MessageBox]::Show('FocusFlow Stealth Active')\"");
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  return (
    <div className="min-h-screen bg-black text-white relative bg-grid-overlay overflow-hidden">
      
      {/* Background Aurora / Ambient Lights */}
      <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-blue-500/15 rounded-full blur-[160px] pointer-events-none"></div>
      <div className="absolute bottom-[20%] right-[-10%] w-[50%] h-[50%] bg-purple-500/10 rounded-full blur-[160px] pointer-events-none"></div>
      <div className="absolute top-[40%] left-[30%] w-[40%] h-[40%] bg-indigo-500/10 rounded-full blur-[180px] pointer-events-none"></div>

      {/* Mouse Follower Ambient Glow */}
      <motion.div
        style={{
          x: glowX,
          y: glowY,
          translateX: "-50%",
          translateY: "-50%",
        }}
        className="fixed top-0 left-0 w-[450px] h-[450px] bg-gradient-to-tr from-blue-500/8 via-purple-500/4 to-transparent rounded-full blur-[100px] pointer-events-none z-0"
      />

      {/* Canvas Floating Particles */}
      <ParticleBackground />

      {/* --- Header / Navbar --- */}
      <header className="fixed top-0 left-0 w-full z-50 bg-black/60 backdrop-blur-xl border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-purple-600 flex items-center justify-center border border-white/10 shadow-lg shadow-blue-500/20">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-zinc-200 to-zinc-400 bg-clip-text text-transparent">
              FocusFlow
            </span>
          </div>

          <nav className="hidden md:flex items-center space-x-8 text-sm text-zinc-400 font-medium">
            <a href="#features" className="hover:text-white transition">Features</a>
            <a href="#analytics" className="hover:text-white transition">Analytics</a>
            <a href="#timeline" className="hover:text-white transition">Process</a>
            <a href="#achievements" className="hover:text-white transition">Gamification</a>
            <a href="#carousel" className="hover:text-white transition">HUD Showcase</a>
          </nav>

          <div className="flex items-center space-x-4">
            <a 
              href="https://github.com/adarsh0044321/focusflow" 
              className="text-zinc-400 hover:text-white transition hidden sm:inline-block"
              target="_blank"
              rel="noreferrer"
              aria-label="GitHub Repository"
            >
              <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24" aria-hidden="true">
                <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.464-1.11-1.464-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.579.688.481C19.137 20.164 22 16.418 22 12c0-5.523-4.477-10-10-10z" />
              </svg>
            </a>
            <a 
              href="#download"
              className="px-4 py-2 text-xs font-semibold text-white bg-zinc-900 border border-white/10 hover:border-blue-500/30 rounded-full hover:bg-zinc-800 transition duration-300 shadow-md shadow-black/50"
            >
              Get FocusFlow
            </a>
          </div>
        </div>
      </header>

      {/* --- Hero Section --- */}
      <section className="pt-32 pb-20 px-6 max-w-7xl mx-auto flex flex-col lg:flex-row items-center justify-between gap-12 relative">
        <div className="flex-1 text-center lg:text-left space-y-6 max-w-xl z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-xs text-blue-400 font-medium">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Introducing FocusFlow v1.1.0 (Stealth HUD)</span>
          </div>
          <h1 className="text-5xl sm:text-6xl font-extrabold tracking-tight leading-[1.1] text-white">
            Master <span className="bg-gradient-to-r from-blue-500 via-indigo-400 to-purple-500 bg-clip-text text-transparent">Deep Work.</span>
          </h1>
          <p className="text-zinc-400 text-lg leading-relaxed sm:text-xl">
            FocusFlow transforms distractions into momentum. Capture equations, write clean syntax, and query rotating AI completion pools from a borderless HUD completely hidden from screenshots.
          </p>
          <div className="flex flex-col sm:flex-row items-center gap-4 justify-center lg:justify-start">
            <a 
              href="#download"
              className="w-full sm:w-auto px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-semibold rounded-xl shadow-lg shadow-blue-500/25 transition duration-300 text-center flex items-center justify-center gap-2"
            >
              <Monitor className="w-5 h-5" />
              Download for Windows
            </a>
            <a 
              href="#features"
              className="w-full sm:w-auto px-8 py-4 bg-zinc-900 hover:bg-zinc-800 border border-white/10 rounded-xl font-semibold transition text-center text-zinc-300"
            >
              View Features
            </a>
          </div>
        </div>

        {/* Hero Interactive 3D Mock Showcase */}
        <div className="flex-1 w-full max-w-md lg:max-w-none relative min-h-[480px] z-10 flex items-center justify-center">
          
          {/* Main Floating HUD Timer Card */}
          <motion.div 
            initial={{ y: 20, rotateY: 5 }}
            animate={{ y: -20, rotateY: -5 }}
            transition={{ repeat: Infinity, duration: 6, repeatType: "reverse", ease: "easeInOut" }}
            className="absolute z-20 w-[310px] p-6 glass-panel rounded-2xl border border-white/10 shadow-2xl shadow-blue-500/5 relative overflow-hidden glowing-border"
          >
            <div className="absolute top-0 right-0 w-24 h-24 bg-blue-500/10 rounded-full blur-xl"></div>
            <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-2">
              <span className="text-[10px] text-zinc-500 uppercase tracking-widest font-mono">Pomodoro Focus Timer</span>
              <span className="text-[10px] text-blue-400 font-mono">Active</span>
            </div>
            
            <div className="flex flex-col items-center justify-center py-6">
              <div className="text-5xl font-mono font-extrabold tracking-tighter text-white select-none">
                {formatTimer(timerSeconds)}
              </div>
              <span className="text-[10px] text-zinc-500 font-mono mt-1">Focusing on Organic Chemistry</span>
            </div>

            <div className="flex justify-center space-x-3 pt-3">
              <button 
                onClick={() => setTimerRunning(!timerRunning)}
                className="w-10 h-10 rounded-full bg-white text-black flex items-center justify-center hover:bg-zinc-200 transition cursor-pointer"
              >
                {timerRunning ? <Pause className="w-4 h-4 fill-black" /> : <Play className="w-4 h-4 fill-black ml-0.5" />}
              </button>
              <button 
                onClick={() => setTimerSeconds(1500)}
                className="px-4 py-2 rounded-full bg-zinc-900 border border-white/10 text-xs hover:bg-zinc-800 font-mono text-zinc-300 cursor-pointer"
              >
                Reset
              </button>
            </div>
          </motion.div>

          {/* Secondary Floating Focus Score Card */}
          <motion.div 
            initial={{ x: -20, y: -40, rotate: -5 }}
            animate={{ x: 20, y: -20, rotate: 2 }}
            transition={{ repeat: Infinity, duration: 5, repeatType: "reverse", ease: "easeInOut" }}
            className="absolute top-[10%] left-0 z-30 w-44 p-4 bg-zinc-950/80 backdrop-blur-md rounded-xl border border-white/10 shadow-xl shadow-black/80 flex items-center space-x-3"
          >
            <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
              <Activity className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <div className="text-[9px] text-zinc-500 font-mono uppercase">Focus Score</div>
              <div className="text-lg font-bold font-mono text-emerald-400">92%</div>
            </div>
          </motion.div>

          {/* Tertiary Floating Productivity Stats Card */}
          <motion.div 
            initial={{ x: 30, y: 110, rotate: 8 }}
            animate={{ x: -10, y: 130, rotate: 2 }}
            transition={{ repeat: Infinity, duration: 7, repeatType: "reverse", ease: "easeInOut" }}
            className="absolute bottom-[10%] right-0 z-10 w-52 p-4 bg-zinc-950/80 backdrop-blur-md rounded-xl border border-white/10 shadow-xl shadow-black/80 space-y-2"
          >
            <div className="flex items-center justify-between text-[9px] font-mono text-zinc-500">
              <span>DAILY PROGRESS</span>
              <span className="text-purple-400">+4.2 hrs</span>
            </div>
            <div className="text-base font-bold font-mono">5.5h / 8.0h</div>
            <div className="w-full bg-zinc-900 rounded-full h-1.5 overflow-hidden">
              <div className="bg-gradient-to-r from-blue-500 to-purple-500 h-full rounded-full w-[70%]"></div>
            </div>
          </motion.div>
          
        </div>
      </section>

      {/* --- Feature Stats Section --- */}
      <section className="bg-zinc-950/80 border-y border-white/5 py-12 px-6">
        <div className="max-w-7xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
          <div className="space-y-2">
            <h3 className="text-3xl sm:text-4xl font-extrabold font-mono bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">10,000+</h3>
            <p className="text-zinc-500 text-xs sm:text-sm font-medium">Hours Focused</p>
          </div>
          <div className="space-y-2">
            <h3 className="text-3xl sm:text-4xl font-extrabold font-mono bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">5,000+</h3>
            <p className="text-zinc-500 text-xs sm:text-sm font-medium">Sessions Completed</p>
          </div>
          <div className="space-y-2">
            <h3 className="text-3xl sm:text-4xl font-extrabold font-mono bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">95%</h3>
            <p className="text-zinc-500 text-xs sm:text-sm font-medium">Productivity Improvement</p>
          </div>
          <div className="space-y-2">
            <h3 className="text-3xl sm:text-4xl font-extrabold font-mono bg-gradient-to-r from-pink-400 to-blue-400 bg-clip-text text-transparent">1,000+</h3>
            <p className="text-zinc-500 text-xs sm:text-sm font-medium">Active Users</p>
          </div>
        </div>
      </section>

      {/* --- Features Grid Section --- */}
      <section id="features" className="py-24 px-6 max-w-7xl mx-auto space-y-16">
        <div className="text-center space-y-4 max-w-2xl mx-auto">
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">Intelligent Focus Workspace</h2>
          <p className="text-zinc-400 text-sm sm:text-base">
            FocusFlow brings robust local OCR, rotated API pools, and gamified statistics directly onto your Windows desktop via transparent borderless overlays.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          
          {/* Card 1 */}
          <div className="p-6 glass-panel-interactive rounded-2xl flex flex-col justify-between h-56 group">
            <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/25 flex items-center justify-center text-blue-400 group-hover:bg-blue-500/20 group-hover:border-blue-500/40 transition">
              <Clock className="w-5 h-5" />
            </div>
            <div className="space-y-2 mt-4">
              <h4 className="font-bold text-white text-base">Deep Focus Sessions</h4>
              <p className="text-zinc-400 text-xs leading-relaxed">
                Trigger pomodoro or stopwatch timelines that lock you into deep work cycles and logs.
              </p>
            </div>
          </div>

          {/* Card 2 */}
          <div className="p-6 glass-panel-interactive rounded-2xl flex flex-col justify-between h-56 group">
            <div className="w-10 h-10 rounded-lg bg-purple-500/10 border border-purple-500/25 flex items-center justify-center text-purple-400 group-hover:bg-purple-500/20 group-hover:border-purple-500/40 transition">
              <TrendingUp className="w-5 h-5" />
            </div>
            <div className="space-y-2 mt-4">
              <h4 className="font-bold text-white text-base">Productivity Analytics</h4>
              <p className="text-zinc-400 text-xs leading-relaxed">
                Track focused minutes, study history, and charts across visual metric panels.
              </p>
            </div>
          </div>

          {/* Card 3 */}
          <div className="p-6 glass-panel-interactive rounded-2xl flex flex-col justify-between h-56 group">
            <div className="w-10 h-10 rounded-lg bg-pink-500/10 border border-pink-500/25 flex items-center justify-center text-pink-400 group-hover:bg-pink-500/20 group-hover:border-pink-500/40 transition">
              <Sparkles className="w-5 h-5" />
            </div>
            <div className="space-y-2 mt-4">
              <h4 className="font-bold text-white text-base">AI Study Insights</h4>
              <p className="text-zinc-400 text-xs leading-relaxed">
                Rotated online API and local GGUF models process screens, math, or syntax questions step-by-step.
              </p>
            </div>
          </div>

          {/* Card 4 */}
          <div className="p-6 glass-panel-interactive rounded-2xl flex flex-col justify-between h-56 group">
            <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/25 flex items-center justify-center text-emerald-400 group-hover:bg-emerald-500/20 group-hover:border-emerald-500/40 transition">
              <Target className="w-5 h-5" />
            </div>
            <div className="space-y-2 mt-4">
              <h4 className="font-bold text-white text-base">Focus Score System</h4>
              <p className="text-zinc-400 text-xs leading-relaxed">
                Algorithmically graded scores reflecting your depth, consistency, and session logs.
              </p>
            </div>
          </div>

          {/* Card 5 */}
          <div className="p-6 glass-panel-interactive rounded-2xl flex flex-col justify-between h-56 group">
            <div className="w-10 h-10 rounded-lg bg-indigo-500/10 border border-indigo-500/25 flex items-center justify-center text-indigo-400 group-hover:bg-indigo-500/20 group-hover:border-indigo-500/40 transition">
              <BookOpen className="w-5 h-5" />
            </div>
            <div className="space-y-2 mt-4">
              <h4 className="font-bold text-white text-base">Session History Journal</h4>
              <p className="text-zinc-400 text-xs leading-relaxed">
                A searchable log repository displaying raw OCR outputs, timings, and screen captures.
              </p>
            </div>
          </div>

          {/* Card 6 */}
          <div className="p-6 glass-panel-interactive rounded-2xl flex flex-col justify-between h-56 group">
            <div className="w-10 h-10 rounded-lg bg-yellow-500/10 border border-yellow-500/25 flex items-center justify-center text-yellow-400 group-hover:bg-yellow-500/20 group-hover:border-yellow-500/40 transition">
              <Award className="w-5 h-5" />
            </div>
            <div className="space-y-2 mt-4">
              <h4 className="font-bold text-white text-base">Achievement Badging</h4>
              <p className="text-zinc-400 text-xs leading-relaxed">
                Unlock glow badges like Deep Focus Master or 100 Hour Club to keep your consistency.
              </p>
            </div>
          </div>

          {/* Card 7 */}
          <div className="p-6 glass-panel-interactive rounded-2xl flex flex-col justify-between h-56 group">
            <div className="w-10 h-10 rounded-lg bg-cyan-500/10 border border-cyan-500/25 flex items-center justify-center text-cyan-400 group-hover:bg-cyan-500/20 group-hover:border-cyan-500/40 transition">
              <Activity className="w-5 h-5" />
            </div>
            <div className="space-y-2 mt-4">
              <h4 className="font-bold text-white text-base">Goal Management</h4>
              <p className="text-zinc-400 text-xs leading-relaxed">
                Configure target focus hours and align study tasks per week dynamically.
              </p>
            </div>
          </div>

          {/* Card 8 */}
          <div className="p-6 glass-panel-interactive rounded-2xl flex flex-col justify-between h-56 group">
            <div className="w-10 h-10 rounded-lg bg-red-500/10 border border-red-500/25 flex items-center justify-center text-red-400 group-hover:bg-red-500/20 group-hover:border-red-500/40 transition">
              <Shield className="w-5 h-5" />
            </div>
            <div className="space-y-2 mt-4">
              <h4 className="font-bold text-white text-base">Distraction Reduction</h4>
              <p className="text-zinc-400 text-xs leading-relaxed">
                Excludes protected Windows HUD widgets from screen-sharers like Discord, Teams, or Zoom.
              </p>
            </div>
          </div>

        </div>
      </section>

      {/* --- Interactive Productivity Visualization Dashboard --- */}
      <section id="analytics" className="py-24 px-6 bg-zinc-950/40 border-y border-white/5 relative">
        <div className="absolute top-[20%] left-[-10%] w-[300px] h-[300px] bg-blue-500/5 rounded-full blur-[120px] pointer-events-none"></div>
        <div className="absolute bottom-[20%] right-[-10%] w-[300px] h-[300px] bg-purple-500/5 rounded-full blur-[120px] pointer-events-none"></div>
        
        <div className="max-w-7xl mx-auto space-y-16">
          <div className="text-center lg:text-left flex flex-col lg:flex-row items-center justify-between gap-6">
            <div className="space-y-4 max-w-xl">
              <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">Interactive Analytics Console</h2>
              <p className="text-zinc-400 text-sm sm:text-base">
                Inspect simulated dashboard statistics mapping heatmaps, weekly study hours, and achievements. FocusFlow logs stats locally.
              </p>
            </div>

            {/* Toggle Tabs */}
            <div className="bg-zinc-900/90 border border-white/5 p-1 rounded-full flex items-center font-mono text-xs">
              {(["hours", "score", "distractions"] as ChartTab[]).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-4 py-2 rounded-full font-bold transition capitalize cursor-pointer ${
                    activeTab === tab 
                      ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md shadow-blue-500/10" 
                      : "text-zinc-400 hover:text-white"
                  }`}
                >
                  {tab === "hours" ? "Study Hours" : tab === "score" ? "Focus Score" : "Distractions"}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            
            {/* Chart Area */}
            <div className="lg:col-span-2 p-6 glass-panel rounded-2xl border border-white/10 space-y-6 flex flex-col justify-between min-h-[360px]">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-blue-500 animate-pulse"></span>
                  <span className="text-xs font-mono font-bold tracking-wider uppercase text-zinc-400">Weekly Performance Index</span>
                </div>
                <span className="text-xs font-mono text-zinc-500">June 2026</span>
              </div>

              {/* Dynamic SVG chart drawing */}
              <div className="flex-1 w-full min-h-[180px] relative flex items-end">
                <svg className="w-full h-[160px] overflow-visible" viewBox="0 0 600 160" preserveAspectRatio="none">
                  {/* Grid Lines */}
                  <line x1="0" y1="40" x2="600" y2="40" stroke="rgba(255,255,255,0.05)" strokeDasharray="4 4" />
                  <line x1="0" y1="80" x2="600" y2="80" stroke="rgba(255,255,255,0.05)" strokeDasharray="4 4" />
                  <line x1="0" y1="120" x2="600" y2="120" stroke="rgba(255,255,255,0.05)" strokeDasharray="4 4" />
                  
                  {/* SVG Path drawing based on active tab */}
                  <AnimatePresence mode="wait">
                    {activeTab === "hours" && (
                      <motion.path
                        key="hours-path"
                        initial={{ pathLength: 0 }}
                        animate={{ pathLength: 1 }}
                        transition={{ duration: 1 }}
                        d="M0,140 Q100,60 200,90 T400,30 T600,60"
                        fill="none"
                        stroke="url(#gradient-blue)"
                        strokeWidth="3.5"
                      />
                    )}
                    {activeTab === "score" && (
                      <motion.path
                        key="score-path"
                        initial={{ pathLength: 0 }}
                        animate={{ pathLength: 1 }}
                        transition={{ duration: 1 }}
                        d="M0,100 Q100,70 200,50 T400,20 T600,10"
                        fill="none"
                        stroke="url(#gradient-green)"
                        strokeWidth="3.5"
                      />
                    )}
                    {activeTab === "distractions" && (
                      <motion.path
                        key="distractions-path"
                        initial={{ pathLength: 0 }}
                        animate={{ pathLength: 1 }}
                        transition={{ duration: 1 }}
                        d="M0,40 Q100,90 200,120 T400,130 T600,140"
                        fill="none"
                        stroke="url(#gradient-red)"
                        strokeWidth="3.5"
                      />
                    )}
                  </AnimatePresence>

                  {/* Gradient Definitions */}
                  <defs>
                    <linearGradient id="gradient-blue" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="#0077ff" />
                      <stop offset="100%" stopColor="#7b2ff7" />
                    </linearGradient>
                    <linearGradient id="gradient-green" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="#10b981" />
                      <stop offset="100%" stopColor="#34d399" />
                    </linearGradient>
                    <linearGradient id="gradient-red" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="#ff4a4a" />
                      <stop offset="100%" stopColor="#ff6b6b" />
                    </linearGradient>
                  </defs>
                </svg>
              </div>

              {/* Chart labels */}
              <div className="flex justify-between items-center text-[10px] font-mono text-zinc-500 pt-2 border-t border-white/5">
                <span>MON</span>
                <span>TUE</span>
                <span>WED</span>
                <span>THU</span>
                <span>FRI</span>
                <span>SAT</span>
                <span>SUN</span>
              </div>
            </div>

            {/* Heatmap & Streak Section */}
            <div className="p-6 glass-panel rounded-2xl border border-white/10 flex flex-col justify-between min-h-[360px] relative">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold tracking-wider uppercase text-zinc-400">Consistency Heatmap</span>
                  <div className="flex items-center space-x-1">
                    <Flame className="w-3.5 h-3.5 text-orange-500 fill-orange-500" />
                    <span className="text-xs font-bold text-orange-500 font-mono">14d Streak</span>
                  </div>
                </div>

                {/* Heatmap Grid (7x15) */}
                <div className="grid grid-cols-15 gap-1.5 py-4 relative">
                  {Array.from({ length: 7 }).map((_, row) => (
                    <React.Fragment key={row}>
                      {Array.from({ length: 15 }).map((_, col) => {
                        // Generate a mock shade of study depth
                        const val = Math.floor(Math.sin((row + col) * 0.5) * 5) + 3;
                        const opacity = val <= 0 ? 0.05 : val >= 6 ? 0.9 : val * 0.15;
                        const bgStyle = {
                          backgroundColor: val <= 0 ? "rgba(255,255,255,0.05)" : `rgba(0,119,255,${opacity})`
                        };
                        return (
                          <div 
                            key={col} 
                            style={bgStyle}
                            onMouseEnter={() => setHoveredDay({ row, col, val: val <= 0 ? 0 : val })}
                            onMouseLeave={() => setHoveredDay(null)}
                            className="aspect-square w-full rounded-[2px] transition hover:scale-125 cursor-pointer relative"
                          ></div>
                        );
                      })}
                    </React.Fragment>
                  ))}
                  
                  {/* Heatmap Hover Tooltip */}
                  {hoveredDay && (
                    <div className="absolute bottom-[-35px] left-1/2 transform -translate-x-1/2 bg-zinc-950 border border-white/10 px-2 py-1 rounded text-[9px] font-mono z-50 text-white whitespace-nowrap shadow-lg">
                      Day {hoveredDay.col + 1}, Week {hoveredDay.row + 1}: {hoveredDay.val.toFixed(1)} hrs focused
                    </div>
                  )}
                </div>
              </div>

              <div className="pt-4 border-t border-white/5 space-y-2">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-zinc-500 font-mono">Weekly Total:</span>
                  <span className="text-white font-bold font-mono">38.4 hours</span>
                </div>
                <div className="flex justify-between items-center text-xs">
                  <span className="text-zinc-500 font-mono">Avg Daily Depth:</span>
                  <span className="text-blue-400 font-bold font-mono">94.8%</span>
                </div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* --- Timeline - How It Works --- */}
      <section id="timeline" className="py-24 px-6 max-w-7xl mx-auto space-y-16">
        <div className="text-center space-y-4 max-w-2xl mx-auto">
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">The Focus Flow Cycle</h2>
          <p className="text-zinc-400 text-sm sm:text-base">
            An elegant timeline tracking study sessions, cleaning raw OCR artifacts, running local GGUF router logic, and presenting stealth hud answers.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 relative">
          {/* Connecting Line */}
          <div className="absolute top-1/2 left-[12%] right-[12%] h-[1px] bg-gradient-to-r from-blue-600/30 via-purple-600/30 to-blue-600/30 z-0 hidden md:block"></div>
          
          {/* Step 1 */}
          <div className="p-6 glass-panel rounded-2xl border border-white/10 space-y-4 relative z-10 hover:border-blue-500/20 transition group">
            <div className="w-10 h-10 rounded-full bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-sm font-bold font-mono text-blue-400 group-hover:scale-110 transition duration-300">
              01
            </div>
            <h4 className="font-bold text-white text-base">Start Focus HUD</h4>
            <p className="text-zinc-400 text-xs leading-relaxed">
              Launch the stealth HUD overlay using `Ctrl+Shift+K` or click drag selection region.
            </p>
          </div>

          {/* Step 2 */}
          <div className="p-6 glass-panel rounded-2xl border border-white/10 space-y-4 relative z-10 hover:border-purple-500/20 transition group">
            <div className="w-10 h-10 rounded-full bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-sm font-bold font-mono text-purple-400 group-hover:scale-110 transition duration-300">
              02
            </div>
            <h4 className="font-bold text-white text-base">OCR & Cleaning</h4>
            <p className="text-zinc-400 text-xs leading-relaxed">
              Local Tesseract parses the image, cleans UI garbage, and corrects character glitches instantly.
            </p>
          </div>

          {/* Step 3 */}
          <div className="p-6 glass-panel rounded-2xl border border-white/10 space-y-4 relative z-10 hover:border-pink-500/20 transition group">
            <div className="w-10 h-10 rounded-full bg-pink-500/10 border border-pink-500/20 flex items-center justify-center text-sm font-bold font-mono text-pink-400 group-hover:scale-110 transition duration-300">
              03
            </div>
            <h4 className="font-bold text-white text-base">AI Engine Route</h4>
            <p className="text-zinc-400 text-xs leading-relaxed">
              Routes context to local `llama.cpp` weights or online key-rotated OpenAI models based on selected mode.
            </p>
          </div>

          {/* Step 4 */}
          <div className="p-6 glass-panel rounded-2xl border border-white/10 space-y-4 relative z-10 hover:border-emerald-500/20 transition group">
            <div className="w-10 h-10 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-sm font-bold font-mono text-emerald-400 group-hover:scale-110 transition duration-300">
              04
            </div>
            <h4 className="font-bold text-white text-base">Log & Improve</h4>
            <p className="text-zinc-400 text-xs leading-relaxed">
              Saves query entries, times, and screenshots to history JSON while grading daily focus scores.
            </p>
          </div>

        </div>
      </section>

      {/* --- Gamified Achievement System Showcase --- */}
      <section id="achievements" className="py-24 px-6 bg-zinc-950/40 border-y border-white/5 relative">
        <div className="max-w-7xl mx-auto space-y-16">
          <div className="text-center space-y-4 max-w-2xl mx-auto">
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">Earn Exclusive Achievement Badges</h2>
            <p className="text-zinc-400 text-sm sm:text-base">
              Build your study consistency and unlock glowing badges saved to your FocusFlow profile log.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-6">
            
            {/* Badge 1 */}
            <div className="p-6 glass-panel rounded-2xl border border-white/10 flex flex-col items-center justify-center text-center space-y-4 hover:scale-105 transition duration-300 relative group overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-b from-orange-500/5 to-transparent opacity-0 group-hover:opacity-100 transition"></div>
              <div className="w-14 h-14 rounded-full bg-orange-500/15 border border-orange-500/30 flex items-center justify-center text-orange-400 group-hover:scale-110 transition shadow-lg shadow-orange-500/5">
                <Flame className="w-7 h-7" />
              </div>
              <div>
                <h5 className="font-bold text-white text-sm">7 Day Streak</h5>
                <p className="text-zinc-500 text-[10px] mt-1">Study 1+ hour daily for a week</p>
              </div>
            </div>

            {/* Badge 2 */}
            <div className="p-6 glass-panel rounded-2xl border border-white/10 flex flex-col items-center justify-center text-center space-y-4 hover:scale-105 transition duration-300 relative group overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-b from-purple-500/5 to-transparent opacity-0 group-hover:opacity-100 transition"></div>
              <div className="w-14 h-14 rounded-full bg-purple-500/15 border border-purple-500/30 flex items-center justify-center text-purple-400 group-hover:scale-110 transition shadow-lg shadow-purple-500/5">
                <Award className="w-7 h-7" />
              </div>
              <div>
                <h5 className="font-bold text-white text-sm">Deep Focus Master</h5>
                <p className="text-zinc-500 text-[10px] mt-1">Maintain &gt;90% depth for 10 sessions</p>
              </div>
            </div>

            {/* Badge 3 */}
            <div className="p-6 glass-panel rounded-2xl border border-white/10 flex flex-col items-center justify-center text-center space-y-4 hover:scale-105 transition duration-300 relative group overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-b from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition"></div>
              <div className="w-14 h-14 rounded-full bg-blue-500/15 border border-blue-500/30 flex items-center justify-center text-blue-400 group-hover:scale-110 transition shadow-lg shadow-blue-500/5">
                <Clock className="w-7 h-7" />
              </div>
              <div>
                <h5 className="font-bold text-white text-sm">100 Hour Club</h5>
                <p className="text-zinc-500 text-[10px] mt-1">Log 100 total hours of deep work</p>
              </div>
            </div>

            {/* Badge 4 */}
            <div className="p-6 glass-panel rounded-2xl border border-white/10 flex flex-col items-center justify-center text-center space-y-4 hover:scale-105 transition duration-300 relative group overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-b from-emerald-500/5 to-transparent opacity-0 group-hover:opacity-100 transition"></div>
              <div className="w-14 h-14 rounded-full bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400 group-hover:scale-110 transition shadow-lg shadow-emerald-500/5">
                <UserCheck className="w-7 h-7" />
              </div>
              <div>
                <h5 className="font-bold text-white text-sm">Active Champion</h5>
                <p className="text-zinc-500 text-[10px] mt-1">Complete 3 study goals in 1 week</p>
              </div>
            </div>

            {/* Badge 5 */}
            <div className="p-6 glass-panel rounded-2xl border border-white/10 flex flex-col items-center justify-center text-center space-y-4 hover:scale-105 transition duration-300 relative group overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-b from-pink-500/5 to-transparent opacity-0 group-hover:opacity-100 transition"></div>
              <div className="w-14 h-14 rounded-full bg-pink-500/15 border border-pink-500/30 flex items-center justify-center text-pink-400 group-hover:scale-110 transition shadow-lg shadow-pink-500/5">
                <Target className="w-7 h-7" />
              </div>
              <div>
                <h5 className="font-bold text-white text-sm">JEE/NEET Ninja</h5>
                <p className="text-zinc-500 text-[10px] mt-1">Verify 50 complex formulas with OCR</p>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* --- Cinematic Screenshot / HUD Carousel Section --- */}
      <section id="carousel" className="py-24 px-6 max-w-7xl mx-auto space-y-16">
        <div className="text-center space-y-4 max-w-2xl mx-auto">
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">Sleek Premium HUD Design</h2>
          <p className="text-zinc-400 text-sm sm:text-base">
            FocusFlow overlays are designed to sit borderless and transparent directly on your display. Flip through screens.
          </p>
        </div>

        {/* Carousel Frame */}
        <div className="flex flex-col lg:flex-row items-center justify-between gap-12 bg-zinc-950/60 p-8 rounded-3xl border border-white/5 relative">
          
          {/* Detail Side */}
          <div className="flex-1 space-y-6 text-left max-w-md">
            <span className="px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 text-xs font-mono text-purple-400">
              {carouselSlides[carouselIndex].tag}
            </span>
            <h3 className="text-2xl sm:text-3xl font-extrabold text-white">
              {carouselSlides[carouselIndex].title}
            </h3>
            <p className="text-zinc-400 text-sm leading-relaxed">
              {carouselSlides[carouselIndex].desc}
            </p>

            <div className="flex items-center space-x-3 pt-4">
              <button 
                onClick={prevCarousel}
                className="w-10 h-10 rounded-full bg-zinc-900 hover:bg-zinc-800 text-white flex items-center justify-center border border-white/10 transition cursor-pointer"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <button 
                onClick={nextCarousel}
                className="w-10 h-10 rounded-full bg-zinc-900 hover:bg-zinc-800 text-white flex items-center justify-center border border-white/10 transition cursor-pointer"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Interactive Screen Sandbox Side */}
          <div className="flex-1 w-full max-w-md h-[280px] bg-zinc-950/40 rounded-2xl relative shadow-2xl flex items-center justify-center p-4">
            <AnimatePresence mode="wait">
              <motion.div
                key={carouselIndex}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.3 }}
                className="w-full h-full"
              >
                {carouselSlides[carouselIndex].content}
              </motion.div>
            </AnimatePresence>
          </div>

        </div>
      </section>

      {/* --- Testimonials --- */}
      <section className="py-24 px-6 bg-zinc-950/40 border-t border-white/5 relative">
        <div className="max-w-7xl mx-auto space-y-16">
          <div className="text-center space-y-4 max-w-2xl mx-auto">
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">Approved by High-Performer Students</h2>
            <p className="text-zinc-400 text-sm sm:text-base">
              See how JEE/NEET competitive exam students and software engineers use FocusFlow daily to drive results.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            
            {/* Card 1 */}
            <div className="p-6 glass-panel rounded-2xl border border-white/10 space-y-4 hover:border-blue-500/20 transition duration-300">
              <p className="text-zinc-300 text-sm italic leading-relaxed">
                &quot;FocusFlow completely streamlined my JEE physics preparation. When solving tricky question banks, I capture equations and review details offline without browser tabs distraction.&quot;
              </p>
              <div className="flex items-center space-x-3 pt-2">
                <div className="w-9 h-9 rounded-full bg-blue-600 flex items-center justify-center font-bold font-mono text-xs">
                  AR
                </div>
                <div>
                  <h6 className="font-bold text-white text-xs">Aditya Raj</h6>
                  <span className="text-[10px] text-zinc-500 font-medium">JEE Advanced Aspirant</span>
                </div>
              </div>
            </div>

            {/* Card 2 */}
            <div className="p-6 glass-panel rounded-2xl border border-white/10 space-y-4 hover:border-purple-500/20 transition duration-300">
              <p className="text-zinc-300 text-sm italic leading-relaxed">
                &quot;The stealth HUD exclusion is an engineering marvel. I screen share my coding work, but the answer panels and focus timers stay completely invisible to viewers. Insanely premium.&quot;
              </p>
              <div className="flex items-center space-x-3 pt-2">
                <div className="w-9 h-9 rounded-full bg-purple-600 flex items-center justify-center font-bold font-mono text-xs">
                  SK
                </div>
                <div>
                  <h6 className="font-bold text-white text-xs">Sanjay K.</h6>
                  <span className="text-[10px] text-zinc-500 font-medium">Full Stack Software Developer</span>
                </div>
              </div>
            </div>

            {/* Card 3 */}
            <div className="p-6 glass-panel rounded-2xl border border-white/10 space-y-4 hover:border-pink-500/20 transition duration-300">
              <p className="text-zinc-300 text-sm italic leading-relaxed">
                &quot;The gamified badge score tracking is what keeps me study-consistent. Reaching the 100 Hour Club gave my NEET organic chemistry MCQ runs real focus.&quot;
              </p>
              <div className="flex items-center space-x-3 pt-2">
                <div className="w-9 h-9 rounded-full bg-pink-600 flex items-center justify-center font-bold font-mono text-xs">
                  PD
                </div>
                <div>
                  <h6 className="font-bold text-white text-xs">Priya D.</h6>
                  <span className="text-[10px] text-zinc-500 font-medium">NEET 2026 Rank Aspirant</span>
                </div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* --- Download CTA Panel Section --- */}
      <section id="download" className="py-24 px-6 max-w-7xl mx-auto relative">
        <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-blue-600/10 via-purple-600/5 to-transparent rounded-3xl blur-2xl pointer-events-none"></div>
        
        <div className="p-12 bg-zinc-950/80 border border-white/10 rounded-3xl text-center space-y-8 relative overflow-hidden glowing-border">
          <div className="absolute top-0 right-0 w-44 h-44 bg-purple-500/10 rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 left-0 w-44 h-44 bg-blue-500/10 rounded-full blur-3xl"></div>
          
          <div className="space-y-4 max-w-xl mx-auto">
            <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight">Ready to Enter Deep Focus?</h2>
            <p className="text-zinc-400 text-sm sm:text-base leading-relaxed">
              Unlock your true potential today. Experience the most advanced educational productivity assistant built for Windows.
            </p>
          </div>

          <div className="flex flex-col items-center justify-center space-y-4">
            <a
              href="https://github.com/adarsh0044321/focusflow/releases/download/v1.1.0/FocusFlow-v1.1.0-LITE.zip"
              className="px-8 py-4 text-sm font-bold bg-white text-black hover:bg-zinc-200 transition duration-300 rounded-xl flex items-center gap-2 shadow-lg shadow-white/5"
            >
              <Monitor className="w-4 h-4" />
              Download FocusFlow v1.1.0 (Lite Release)
            </a>
            <div className="text-[10px] text-zinc-500 font-mono flex items-center gap-1.5 justify-center">
              <span>● Compatible with Windows 10 &amp; 11</span>
              <span>·</span>
              <span>Tesseract OCR Bundled</span>
            </div>
          </div>

          {/* Quick Copy Script helper for developers */}
          <div className="max-w-md mx-auto pt-6 border-t border-white/5 space-y-2">
            <span className="text-[10px] text-zinc-500 font-mono block">QUICK INSTALL FOR DEVELOPERS (POWERSHELL)</span>
            <div className="bg-zinc-900/60 p-2 border border-white/10 rounded-lg flex items-center justify-between text-[9px] font-mono">
              <span className="text-zinc-400 select-all overflow-x-hidden text-ellipsis mr-2">git clone https://github.com/adarsh0044321/focusflow.git</span>
              <button 
                onClick={handleCopyClipboard}
                className="bg-zinc-800 hover:bg-zinc-700 text-white font-bold px-3 py-1 rounded transition text-[9px] min-w-[70px] cursor-pointer"
              >
                {isCopied ? "Copied!" : "Copy"}
              </button>
            </div>
          </div>

        </div>
      </section>

      {/* --- Footer --- */}
      <footer className="border-t border-white/5 bg-zinc-950/80 py-16 px-6 font-mono text-xs">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-start gap-12">
          
          <div className="space-y-4 max-w-sm">
            <div className="flex items-center space-x-2">
              <div className="w-6 h-6 rounded-md bg-gradient-to-tr from-blue-600 to-purple-600 flex items-center justify-center border border-white/10 shadow-lg">
                <Zap className="w-3.5 h-3.5 text-white" />
              </div>
              <span className="font-bold text-sm tracking-tight text-white">FocusFlow</span>
            </div>
            <p className="text-zinc-500 leading-relaxed">
              Intelligent focus and study companion built for Windows 10/11. Zero-window display exclusion ensures maximum stealth while you learn.
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-8">
            <div className="space-y-3">
              <h6 className="text-[10px] text-zinc-400 font-bold uppercase tracking-wider">Features</h6>
              <ul className="space-y-2 text-zinc-500">
                <li><a href="#features" className="hover:text-white transition">Timer Logs</a></li>
                <li><a href="#analytics" className="hover:text-white transition">Productivity</a></li>
                <li><a href="#achievements" className="hover:text-white transition">Badges</a></li>
              </ul>
            </div>

            <div className="space-y-3">
              <h6 className="text-[10px] text-zinc-400 font-bold uppercase tracking-wider">Resources</h6>
              <ul className="space-y-2 text-zinc-500">
                <li><a href="https://github.com/adarsh0044321/focusflow/blob/main/README.md" className="hover:text-white transition" target="_blank" rel="noreferrer">Documentation</a></li>
                <li><a href="https://github.com/adarsh0044321/focusflow" className="hover:text-white transition" target="_blank" rel="noreferrer">GitHub</a></li>
                <li><a href="https://github.com/adarsh0044321/focusflow/releases" className="hover:text-white transition" target="_blank" rel="noreferrer">Releases</a></li>
              </ul>
            </div>

            <div className="space-y-3">
              <h6 className="text-[10px] text-zinc-400 font-bold uppercase tracking-wider">Legal</h6>
              <ul className="space-y-2 text-zinc-500">
                <li><a href="https://github.com/adarsh0044321/focusflow/blob/main/LICENSE" className="hover:text-white transition" target="_blank" rel="noreferrer">MIT License</a></li>
                <li><a href="#" className="hover:text-white transition">Privacy Policy</a></li>
                <li><a href="#" className="hover:text-white transition">Contact</a></li>
              </ul>
            </div>
          </div>

        </div>

        <div className="max-w-7xl mx-auto pt-8 mt-8 border-t border-white/5 flex flex-col sm:flex-row justify-between items-center text-zinc-600 gap-4">
          <span>&copy; {new Date().getFullYear()} FocusFlow. All rights reserved.</span>
          <span>Designed with Linear &amp; Raycast inspiration.</span>
        </div>
      </footer>

    </div>
  );
}
