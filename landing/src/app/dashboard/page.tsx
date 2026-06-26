"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Zap, Monitor, Clock, Target, Shield, Sparkles, BookOpen, Flame,
  Play, Pause, SkipForward, ChevronRight, Settings, BarChart2,
  HelpCircle, CheckSquare, Plus, Trash2, Volume2, Music, Check,
  AlertTriangle, LogOut, FileText, Folder, Eye, Moon, Compass, Code, Terminal
} from "lucide-react";

// --- Types & Schema Definitions ---
interface Session {
  id: string;
  timestamp: string;
  goal: string;
  subject: string;
  duration_mins: number;
  target_duration_mins: number;
  mode: string;
  status: string;
  focus_score: number;
  is_interrupted: boolean;
}

interface Goal {
  id: string;
  text: string;
  completed: boolean;
  date: string;
}

interface AppSettings {
  hotkey_solve: string;
  capture_mode: string;
  mode: string;
  opacity: number;
  online_model: string;
  very_strict_allowed_apps?: string[];
  strict_allowed_apps?: string[];
  moderate_allowed_apps?: string[];
  moderate_allowed_websites?: string[];
  llm_model_path?: string;
}

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<string>("desktop");
  const [hoverTimer, setHoverTimer] = useState<boolean>(false);
  const [isWebviewReady, setIsWebviewReady] = useState<boolean>(false);
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" | "info" | "warning" } | null>(null);

  const showToast = (message: string, type: "success" | "error" | "info" | "warning" = "info") => {
    setToast({ message, type });
  };

  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 4000);
      return () => clearTimeout(timer);
    }
  }, [toast]);
  
  const handleMinimize = () => {
    if (typeof window !== "undefined" && (window as any).pywebview?.api?.minimize_window) {
      (window as any).pywebview.api.minimize_window();
    }
  };

  const handleClose = () => {
    if (typeof window !== "undefined" && (window as any).pywebview?.api?.close_window) {
      (window as any).pywebview.api.close_window();
    }
  };
  
  // --- Core States ---
  const [stats, setStats] = useState<any>({
    total_hours: 0.0,
    streak: 0,
    avg_focus_score: 0,
    sessions_count: 0,
    weekly_data: [0, 0, 0, 0, 0, 0, 0],
    subject_distribution: {},
    hourly_productivity: Array(24).fill(0),
    achievements: [],
    recent_sessions: []
  });
  const [goals, setGoals] = useState<Goal[]>([]);
  const [settings, setSettings] = useState<AppSettings>({
    hotkey_solve: "ctrl+shift+k",
    capture_mode: "region",
    mode: "combined",
    opacity: 240,
    online_model: "gpt-4o",
    very_strict_allowed_apps: [],
    strict_allowed_apps: ["Spotify.exe", "Acrobat.exe", "SumatraPDF.exe", "explorer.exe"],
    moderate_allowed_apps: ["chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "Spotify.exe"],
    moderate_allowed_websites: ["youtube.com", "physicswallah.com", "unacademy.com", "notion.so"]
  });

  // --- Focus Session States ---
  const [sessionActive, setSessionActive] = useState<boolean>(false);
  const [sessionPaused, setSessionPaused] = useState<boolean>(false);
  const sessionPausedRef = useRef<boolean>(false);
  const [showExitConfirm, setShowExitConfirm] = useState<boolean>(false);
  const [sessionGoal, setSessionGoal] = useState<string>("");
  const [sessionSubject, setSessionSubject] = useState<string>("Physics");
  const [sessionDuration, setSessionDuration] = useState<number>(25);
  const [sessionMode, setSessionMode] = useState<string>("light");
  const [chosenCodingApp, setChosenCodingApp] = useState<string>("Code.exe");
  const [customCodingAppText, setCustomCodingAppText] = useState<string>("");
  const [pdfUrl, setPdfUrl] = useState<string>("");
  const [customFeatures, setCustomFeatures] = useState({
    keyboard_lock: false,
    touchpad_lock: false,
    app_sweeper: false,
    foreground_guard: false,
    fullscreen: false,
    capture_protection: true,
  });

  useEffect(() => {
    sessionPausedRef.current = sessionPaused;
  }, [sessionPaused]);

  // --- Coding Sandbox States ---
  const [enableCodingSandbox, setEnableCodingSandbox] = useState<boolean>(false);
  const [sandboxCode, setSandboxCode] = useState<string>("# Write your Python code here\nprint('Hello FocusFlow!')\n");
  const [sandboxLang, setSandboxLang] = useState<string>("python");
  const [sandboxOutput, setSandboxOutput] = useState<string>("Console ready...\n");
  const [sandboxRunning, setSandboxRunning] = useState<boolean>(false);

  const isFeatureLocked = (featureId: string) => {
    if (sessionMode === "very_strict") return true;
    if (sessionMode === "strict") return true;
    if (sessionMode === "moderate") {
      return featureId === "keyboard_lock" || featureId === "foreground_guard";
    }
    return false;
  };

  useEffect(() => {
    if (sessionMode === "very_strict") {
      setCustomFeatures({
        keyboard_lock: true,
        touchpad_lock: true,
        app_sweeper: true,
        foreground_guard: true,
        fullscreen: true,
        capture_protection: true,
      });
    } else if (sessionMode === "strict") {
      setCustomFeatures({
        keyboard_lock: true,
        touchpad_lock: true,
        app_sweeper: true,
        foreground_guard: true,
        fullscreen: false,
        capture_protection: true,
      });
    } else if (sessionMode === "moderate") {
      setCustomFeatures({
        keyboard_lock: true,
        touchpad_lock: false,
        app_sweeper: false,
        foreground_guard: true,
        fullscreen: false,
        capture_protection: true,
      });
    } else {
      setCustomFeatures({
        keyboard_lock: false,
        touchpad_lock: false,
        app_sweeper: false,
        foreground_guard: false,
        fullscreen: false,
        capture_protection: false,
      });
    }
  }, [sessionMode]);
  const [timeLeft, setTimeLeft] = useState<number>(0);
  const [targetTime, setTargetTime] = useState<number>(0);
  const [exitHoldProgress, setExitHoldProgress] = useState<number>(0);
  const [showExitWarning, setShowExitWarning] = useState<boolean>(false);
  const [sessionTab, setSessionTab] = useState<string>("timer");
  const [newAppInput, setNewAppInput] = useState<string>("");
  const [newSiteInput, setNewSiteInput] = useState<string>("");

  // --- Quotes for Very Strict Mode ---
  const quotes = [
    "Focus is a muscle. Keep building it.",
    "Concentrate all your thoughts upon the work at hand.",
    "Your future self will thank you for this session.",
    "Deep work is the superpower of the 21st century.",
    "Revision is the difference between an average score and a top rank.",
    "Be here now. Focus on the next step.",
    "No distractions, just growth.",
    "One page, one formula, one problem at a time."
  ];
  const [currentQuoteIdx, setCurrentQuoteIdx] = useState<number>(0);

  useEffect(() => {
    if (sessionActive && sessionMode === "very_strict") {
      const interval = setInterval(() => {
        setCurrentQuoteIdx((prev) => (prev + 1) % quotes.length);
      }, 15000); // 15 seconds
      return () => clearInterval(interval);
    }
  }, [sessionActive, sessionMode]);

  // Disable multi-touch gestures (zoom/pinch/multi-finger scrolls) in WebView under Strict modes
  useEffect(() => {
    if (sessionActive && (sessionMode === "strict" || sessionMode === "very_strict")) {
      const preventGestures = (e: TouchEvent) => {
        if (e.touches.length > 1) {
          e.preventDefault();
        }
      };
      
      // Use active listeners to allow preventDefault
      document.addEventListener("touchstart", preventGestures, { passive: false });
      document.addEventListener("touchmove", preventGestures, { passive: false });
      
      return () => {
        document.removeEventListener("touchstart", preventGestures);
        document.removeEventListener("touchmove", preventGestures);
      };
    }
  }, [sessionActive, sessionMode]);

  // --- Study AI Assistant States ---
  const [aiTool, setAiTool] = useState<string>("doubt_solver");
  const [aiInput, setAiInput] = useState<string>("Explain the photo-electric effect and state Einstein's equation.");
  const [aiChat, setAiChat] = useState<Array<{ role: string; text: string }>>([
    { role: "assistant", text: "Hello! I am your Study AI assistant. Select a tool or ask me a doubt. You can also capture your screen to solve an exam question!" }
  ]);
  const [aiLoading, setAiLoading] = useState<boolean>(false);

  // --- Lofi & Ambient sound States ---
  const [ambientRain, setAmbientRain] = useState<boolean>(false);
  const [ambientNoise, setAmbientNoise] = useState<boolean>(false);
  const [lofiMusic, setLofiMusic] = useState<boolean>(false);
  const [spotifyPlaying, setSpotifyPlaying] = useState<boolean>(false);

  // --- Goal Input ---
  const [newGoalText, setNewGoalText] = useState<string>("");

  // --- Refs for Ambient sound elements ---
  const rainAudioRef = useRef<HTMLAudioElement | null>(null);
  const noiseAudioRef = useRef<HTMLAudioElement | null>(null);
  const lofiAudioRef = useRef<HTMLAudioElement | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const exitHoldRef = useRef<NodeJS.Timeout | null>(null);

  // --- Detect Webview Bridge ---
  useEffect(() => {
    let initialized = false;
    let timer1: NodeJS.Timeout;
    let timer2: NodeJS.Timeout;
    let timer3: NodeJS.Timeout;
    let fallbackTimer: NodeJS.Timeout;

    const checkBridge = () => {
      if (initialized) return;
      if (typeof window !== "undefined" && (window as any).pywebview && (window as any).pywebview.api) {
        initialized = true;
        setIsWebviewReady(true);
        loadDataFromPython();
        
        // Clear all timers immediately to prevent duplicate runs
        clearTimeout(timer1);
        clearTimeout(timer2);
        clearTimeout(timer3);
        clearTimeout(fallbackTimer);
      }
    };
    
    // Check multiple times to handle async initialization
    timer1 = setTimeout(checkBridge, 100);
    timer2 = setTimeout(checkBridge, 500);
    timer3 = setTimeout(checkBridge, 1500);

    fallbackTimer = setTimeout(() => {
      if (!initialized) {
        // Fallback for regular web browsers
        loadMockData();
      }
    }, 2000);

    // Set up global callback for OCR Screen Capture responses
    (window as any).setOcrResult = (text: string) => {
      setAiInput((prev) => prev ? `${prev}\n\n${text}` : text);
      setActiveTab("ai");
      setAiChat((prev) => [...prev, { role: "system", text: "Successfully captured screen region and processed OCR." }]);
    };
    
    // Set up alert fallback
    (window as any).showBlockedAlert = (appName: string) => {
      showToast(`Access Blocked: "${appName}" is restricted in this Focus Mode!`, "error");
    };

    // Set up PDF loader inside WebView
    (window as any).loadPdfInApp = (path: string) => {
      setPdfUrl(path);
      setSessionTab("pdf");
      showToast("PDF loaded inside application viewport!", "success");
    };

    // Set up native stop callback
    (window as any).stopSessionFromPython = (status: string) => {
      if (timerRef.current) clearInterval(timerRef.current);
      setSessionActive(false);
      
      if (status === "interrupted") {
        showToast("Focus session aborted! Score penalty applied.", "error");
      } else if (status === "partially_completed") {
        showToast("Focus session ended early as partially completed.", "warning");
      } else {
        showToast("Focus session completed successfully!", "success");
      }
      
      loadDataFromPython();
      setActiveTab("desktop");
      resetSessionInputs();
      setPdfUrl(""); // clear PDF on session end
    };

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
      clearTimeout(fallbackTimer);
      if (timerRef.current) clearInterval(timerRef.current);
      delete (window as any).stopSessionFromPython;
      delete (window as any).loadPdfInApp;
    };
  }, []);

  // --- Audio Effects Hooks ---
  useEffect(() => {
    if (ambientRain) {
      if (!rainAudioRef.current) {
        rainAudioRef.current = new Audio("https://assets.mixkit.co/active_storage/sfx/2433/2433-84.wav");
        rainAudioRef.current.loop = true;
      }
      rainAudioRef.current.play().catch(() => {});
    } else {
      if (rainAudioRef.current) rainAudioRef.current.pause();
    }
  }, [ambientRain]);

  useEffect(() => {
    if (ambientNoise) {
      if (!noiseAudioRef.current) {
        noiseAudioRef.current = new Audio("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3");
        noiseAudioRef.current.loop = true;
      }
      noiseAudioRef.current.play().catch(() => {});
    } else {
      if (noiseAudioRef.current) noiseAudioRef.current.pause();
    }
  }, [ambientNoise]);

  useEffect(() => {
    if (lofiMusic) {
      if (!lofiAudioRef.current) {
        lofiAudioRef.current = new Audio("https://play.streamafrica.net/lofiradio");
      }
      lofiAudioRef.current.play().catch(() => {});
    } else {
      if (lofiAudioRef.current) lofiAudioRef.current.pause();
    }
  }, [lofiMusic]);

  // --- Track AI Panel Visibility to start/stop offline LLM server ---
  useEffect(() => {
    const isAiVisible = sessionActive ? (sessionTab === "ai") : (activeTab === "ai");
    if (typeof window !== "undefined" && (window as any).pywebview?.api?.on_ai_panel_visibility_changed) {
      (window as any).pywebview.api.on_ai_panel_visibility_changed(isAiVisible);
    }
  }, [activeTab, sessionTab, sessionActive]);

  // --- Load API Data ---
  const loadDataFromPython = async () => {
    if (typeof window === "undefined" || !(window as any).pywebview?.api) return;
    const api = (window as any).pywebview.api;
    try {
      const pStats = await api.get_stats();
      if (pStats) setStats(pStats);
      
      const pGoals = await api.get_daily_goals();
      if (pGoals) setGoals(pGoals);
      
      const pSettings = await api.get_settings();
      if (pSettings) setSettings(pSettings);

      const activeSession = await api.get_active_session();
      if (activeSession) {
        // Crash Recovery: Resume session!
        setSessionActive(true);
        setSessionGoal(activeSession.goal);
        setSessionSubject(activeSession.subject);
        setSessionMode(activeSession.mode);
        setSessionDuration(activeSession.target_duration_mins);
        if (activeSession.custom_features?.coding_sandbox) {
          setEnableCodingSandbox(true);
        }
        
        // Calculate remaining seconds
        const start = new Date(activeSession.start_time).getTime();
        const now = Date.now();
        const elapsedSeconds = Math.floor((now - start) / 1000);
        const totalSeconds = activeSession.target_duration_mins * 60;
        const left = Math.max(0, totalSeconds - elapsedSeconds);
        
        setTimeLeft(left);
        setTargetTime(totalSeconds);
        setActiveTab("session");
        startTimer();
      }
    } catch (e: any) {
      console.error("Error loading data from Python API: ", e);
    }
  };

  const loadMockData = () => {
    setStats({
      total_hours: 14.5,
      streak: 3,
      avg_focus_score: 88,
      sessions_count: 12,
      weekly_data: [1.2, 2.5, 0.0, 3.1, 2.0, 4.2, 1.5],
      subject_distribution: {
        "Physics": 360,
        "Maths": 240,
        "Chemistry": 180,
        "Computer Science": 90
      },
      hourly_productivity: [0,0,0,0,0,0,10,25,40,30,0,0,15,45,60,10,0,0,20,50,30,10,0,0],
      achievements: [
        { id: "first_step", title: "First Step", description: "Complete your first focus session", icon: "Zap", unlocked: true },
        { id: "deep_diver", title: "Deep Diver", description: "Complete a 60+ minute session in Strict", icon: "Shield", unlocked: true },
        { id: "unstoppable", title: "Unstoppable", description: "Reach a 3-day focus streak", icon: "Flame", unlocked: true },
        { id: "academic_weapon", title: "Academic Weapon", description: "Study for 10+ hours", icon: "BookOpen", unlocked: true },
        { id: "early_bird", title: "Early Bird", description: "Study before 8:00 AM", icon: "Clock", unlocked: false },
        { id: "night_owl", title: "Night Owl", description: "Study after 10:00 PM", icon: "Moon", unlocked: false }
      ],
      recent_sessions: [
        { id: "1", timestamp: "2026-06-12 18:30:00", goal: "Solve 20 Electromagnetism Questions", subject: "Physics", duration_mins: 45, target_duration_mins: 45, mode: "strict", status: "completed", focus_score: 95, is_interrupted: false },
        { id: "2", timestamp: "2026-06-12 14:00:00", goal: "Read Alcohol Phenol Ether Notes", subject: "Chemistry", duration_mins: 30, target_duration_mins: 30, mode: "moderate", status: "completed", focus_score: 90, is_interrupted: false },
        { id: "3", timestamp: "2026-06-11 19:15:00", goal: "Solve Calculus Integration Sheet", subject: "Maths", duration_mins: 60, target_duration_mins: 60, mode: "very_strict", status: "completed", focus_score: 100, is_interrupted: false }
      ]
    });
    setGoals([
      { id: "1", text: "Complete Physics Chapter 3 Formulas", completed: true, date: "2026-06-13" },
      { id: "2", text: "Revise Inorganic Reactions", completed: false, date: "2026-06-13" },
      { id: "3", text: "Solve 15 Limits problems", completed: false, date: "2026-06-13" }
    ]);
  };

  // --- Session Control Handlers ---
  const handleStartSession = async () => {
    if (!sessionGoal.trim()) {
      showToast("Please enter a study goal for this session!", "warning");
      return;
    }

    const totalSeconds = sessionDuration * 60;
    setTimeLeft(totalSeconds);
    setTargetTime(totalSeconds);
    setSessionActive(true);
    setSessionPaused(false);
    setActiveTab("session");
    
    if (isWebviewReady) {
      const api = (window as any).pywebview.api;
      const activeCodingApp = chosenCodingApp === "custom" ? customCodingAppText.trim() : chosenCodingApp;
      const featuresToSend = {
        ...customFeatures,
        coding_sandbox: enableCodingSandbox,
        chosen_coding_app: activeCodingApp
      };
      await api.start_focus_session(sessionGoal, sessionSubject, sessionDuration, sessionMode, featuresToSend);
    }
    
    startTimer();
  };

  const handleLangChange = (lang: string) => {
    setSandboxLang(lang);
    if (lang === "python") {
      setSandboxCode("# Write your Python code here\nprint('Hello FocusFlow!')\n");
    } else if (lang === "javascript") {
      setSandboxCode("// Write your JavaScript code here\nconsole.log('Hello FocusFlow!');\n");
    } else if (lang === "html") {
      setSandboxCode("<!-- Write your HTML/CSS code here -->\n<h1>Hello FocusFlow!</h1>\n<p>HTML preview will be rendered below.</p>\n");
    }
  };

  const handleSaveScript = () => {
    try {
      const ext = sandboxLang === "python" ? "py" : sandboxLang === "javascript" ? "js" : "html";
      const blob = new Blob([sandboxCode], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `workspace.${ext}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      showToast(`Saved script successfully!`, "success");
    } catch (e: any) {
      showToast(`Failed to save script: ${e.message}`, "error");
    }
  };

  const handleRunSandboxCode = async () => {
    setSandboxRunning(true);
    setSandboxOutput("Executing code...\n");

    if (sandboxLang === "javascript") {
      let output = "";
      const originalLog = console.log;
      console.log = (...args) => {
        output += args.map(arg => typeof arg === 'object' ? JSON.stringify(arg) : arg).join(" ") + "\n";
      };
      
      try {
        const fn = new Function(sandboxCode);
        fn();
        setSandboxOutput(output || "Code executed successfully with no output.\n");
      } catch (err: any) {
        setSandboxOutput(output + `Execution Error: ${err.message}\n`);
      } finally {
        console.log = originalLog;
        setSandboxRunning(false);
      }
    } else if (sandboxLang === "python") {
      try {
        if (typeof window !== "undefined" && (window as any).pywebview?.api?.run_code) {
          const api = (window as any).pywebview.api;
          const res = await api.run_code("python", sandboxCode);
          if (res.exit_code === 0) {
            setSandboxOutput(res.stdout || "Code executed successfully with no output.\n");
          } else {
            let out = "";
            if (res.stdout) out += res.stdout;
            if (res.stderr) out += (out ? "\n" : "") + `Error:\n${res.stderr}`;
            setSandboxOutput(out || "Execution failed with non-zero exit code.\n");
          }
        } else {
          setSandboxOutput("Python execution not available: WebView API bridge missing.\n");
        }
      } catch (err: any) {
        setSandboxOutput(`Execution failed: ${err.message}\n`);
      } finally {
        setSandboxRunning(false);
      }
    } else if (sandboxLang === "html") {
      setSandboxOutput("HTML Preview loaded.\n");
      setSandboxRunning(false);
    }
  };

  const startTimer = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = setInterval(() => {
      if (sessionPausedRef.current) return;
      setTimeLeft((prev) => prev - 1);
    }, 1000);
  };

  const handleStopSession = async (explicitStatus?: string) => {
    const isSuccess = timeLeft <= 0;
    
    if (!isSuccess && !explicitStatus) {
      setSessionPaused(true);
      setShowExitConfirm(true);
      return;
    }

    if (timerRef.current) clearInterval(timerRef.current);
    setSessionActive(false);
    setShowExitConfirm(false);
    setSessionPaused(false);

    const elapsedSecs = targetTime - timeLeft;
    const elapsedMins = Math.max(1, Math.ceil(elapsedSecs / 60));
    const targetMins = Math.ceil(targetTime / 60);

    let status = explicitStatus || "completed";

    if (isWebviewReady) {
      const api = (window as any).pywebview.api;
      await api.stop_focus_session(status);
      loadDataFromPython();
    } else {
      const newSess: Session = {
        id: Date.now().toString(),
        timestamp: new Date().toISOString().replace("T", " ").substring(0, 19),
        goal: sessionGoal,
        subject: sessionSubject,
        duration_mins: elapsedMins,
        target_duration_mins: targetMins,
        mode: sessionMode,
        status: status,
        focus_score: status === "completed" ? 95 : status === "partially_completed" ? 60 : 0,
        is_interrupted: status === "interrupted"
      };
      setStats((prev: any) => ({
        ...prev,
        sessions_count: prev.sessions_count + 1,
        total_hours: Number((prev.total_hours + newSess.duration_mins / 60).toFixed(1)),
        recent_sessions: [newSess, ...prev.recent_sessions]
      }));
    }

    showToast(`Session ended. Status: ${status.replace("_", " ")}`, status === "completed" ? "success" : "warning");
    setActiveTab("desktop");
    resetSessionInputs();
    setPdfUrl("");
  };

  const handleCancelExit = () => {
    setShowExitConfirm(false);
    setSessionPaused(false);
    startTimer();
  };

  const handleExtendSession = () => {
    setTimeLeft((prev) => prev + 15 * 60);
    setTargetTime((prev) => prev + 15 * 60);
  };

  const handleBrowseModel = async () => {
    if (typeof window !== "undefined" && (window as any).pywebview?.api?.open_model_selector) {
      const path = await (window as any).pywebview.api.open_model_selector();
      if (path) {
        const newSettings = { ...settings, llm_model_path: path };
        setSettings(newSettings);
        if (isWebviewReady) {
          (window as any).pywebview.api.save_settings(newSettings);
        }
        showToast(`Integrated custom model: ${path.split('\\').pop()}`, "success");
      }
    }
  };

  const handleAddApp = () => {
    if (!newAppInput.trim()) return;
    const updated = [...(settings.moderate_allowed_apps || []), newAppInput.trim()];
    const newSettings = { ...settings, moderate_allowed_apps: updated };
    setSettings(newSettings);
    if (isWebviewReady) {
      (window as any).pywebview.api.save_settings(newSettings);
    }
    setNewAppInput("");
  };

  const handleDeleteApp = (app: string) => {
    const updated = (settings.moderate_allowed_apps || []).filter((a) => a !== app);
    const newSettings = { ...settings, moderate_allowed_apps: updated };
    setSettings(newSettings);
    if (isWebviewReady) {
      (window as any).pywebview.api.save_settings(newSettings);
    }
  };

  const handleAddSite = () => {
    if (!newSiteInput.trim()) return;
    const updated = [...(settings.moderate_allowed_websites || []), newSiteInput.trim()];
    const newSettings = { ...settings, moderate_allowed_websites: updated };
    setSettings(newSettings);
    if (isWebviewReady) {
      (window as any).pywebview.api.save_settings(newSettings);
    }
    setNewSiteInput("");
  };

  const handleDeleteSite = (site: string) => {
    const updated = (settings.moderate_allowed_websites || []).filter((s) => s !== site);
    const newSettings = { ...settings, moderate_allowed_websites: updated };
    setSettings(newSettings);
    if (isWebviewReady) {
      (window as any).pywebview.api.save_settings(newSettings);
    }
  };

  const resetSessionInputs = () => {
    setSessionGoal("");
    setTimeLeft(0);
    setTargetTime(0);
    setExitHoldProgress(0);
    setShowExitWarning(false);
  };

  // --- Exit Button Holding Progress ---
  const handleExitMouseDown = () => {
    if (sessionMode === "light") {
      handleStopSession();
      return;
    }
    
    setShowExitWarning(true);
    setExitHoldProgress(0);
    
    let current = 0;
    exitHoldRef.current = setInterval(() => {
      current += 2;
      setExitHoldProgress(current);
      if (current >= 100) {
        clearInterval(exitHoldRef.current!);
        handleStopSession();
      }
    }, 200); // 100% in 10 seconds (50 intervals of 200ms)
  };

  const handleExitMouseUp = () => {
    if (exitHoldRef.current) clearInterval(exitHoldRef.current);
    setExitHoldProgress(0);
    setShowExitWarning(false);
  };

  // --- Goals Interaction ---
  const handleAddGoal = async () => {
    if (!newGoalText.trim()) return;
    if (isWebviewReady) {
      const api = (window as any).pywebview.api;
      const created = await api.add_daily_goal(newGoalText);
      setGoals((prev) => [...prev, created]);
    } else {
      const newGoal: Goal = {
        id: Date.now().toString(),
        text: newGoalText,
        completed: false,
        date: new Date().toISOString().split("T")[0]
      };
      setGoals((prev) => [...prev, newGoal]);
    }
    setNewGoalText("");
  };

  const handleToggleGoal = async (id: string) => {
    if (isWebviewReady) {
      const api = (window as any).pywebview.api;
      await api.toggle_daily_goal(id);
      loadDataFromPython();
    } else {
      setGoals((prev) =>
        prev.map((g) => (g.id === id ? { ...g, completed: !g.completed } : g))
      );
    }
  };

  const handleDeleteGoal = async (id: string) => {
    if (isWebviewReady) {
      const api = (window as any).pywebview.api;
      await api.delete_daily_goal(id);
      loadDataFromPython();
    } else {
      setGoals((prev) => prev.filter((g) => g.id !== id));
    }
  };

  // --- AI Queries ---
  const handleQueryAI = async () => {
    if (!aiInput.trim()) return;
    setAiLoading(true);
    setAiChat((prev) => [...prev, { role: "user", text: aiInput }]);
    
    const currentInput = aiInput;
    setAiInput("");

    if (isWebviewReady) {
      const api = (window as any).pywebview.api;
      const answer = await api.query_ai_assistant(currentInput, aiTool, null);
      setAiChat((prev) => [...prev, { role: "assistant", text: answer }]);
    } else {
      // Mock Response
      setTimeout(() => {
        setAiChat((prev) => [
          ...prev,
          {
            role: "assistant",
            text: `### Study AI Response (${aiTool})\n\nThis is a mock response. In desktop mode, this query is processed by the local **Phi-3 GGUF** model or online **GPT-4o API**.\n\nHere is some detailed information related to your query: "${currentInput}".\n\n1. **Core Concept**: Formula variables are mapped locally.\n2. **Breakdown**: Maintain structure and optimize.\n\nKeep focusing on your study streak!`
          }
        ]);
        setAiLoading(false);
      }, 1000);
      return;
    }
    setAiLoading(false);
  };

  const handleTriggerScreenCapture = async () => {
    if (isWebviewReady) {
      setAiChat((prev) => [...prev, { role: "system", text: "Minimizing dashboard window to capture screen region... Please click and drag over the question." }]);
      const api = (window as any).pywebview.api;
      await api.trigger_ocr_capture();
    } else {
      showToast("Screen Capture is only available in the desktop application mode!", "error");
    }
  };

  // --- Media Keys controls ---
  const handleSpotifyControl = async (action: string) => {
    if (action === "play_pause") setSpotifyPlaying(!spotifyPlaying);
    if (isWebviewReady) {
      const api = (window as any).pywebview.api;
      await api.spotify_action(action);
    } else {
      console.log(`Mock Spotify command: ${action}`);
    }
  };

  const handlePDFOpen = async () => {
    if (isWebviewReady) {
      const api = (window as any).pywebview.api;
      await api.open_pdf_selector();
    } else {
      showToast("File explorer access is only available in the desktop app!", "error");
    }
  };

  const handleExplorerOpen = async () => {
    if (isWebviewReady) {
      const api = (window as any).pywebview.api;
      await api.open_file_explorer();
    } else {
      showToast("File explorer is only available in desktop mode!", "error");
    }
  };

  // --- Timer Helpers ---
  const formatTime = (secs: number) => {
    const absSecs = Math.abs(secs);
    const m = Math.floor(absSecs / 60);
    const s = absSecs % 60;
    const timeStr = `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
    return secs < 0 ? `+${timeStr}` : timeStr;
  };

  // --- Render Functions ---
  const getSubjectColor = (subj: string) => {
    const colors: Record<string, string> = {
      Physics: "bg-blue-600 border-blue-500",
      Maths: "bg-purple-600 border-purple-500",
      Chemistry: "bg-amber-600 border-amber-500",
      "Computer Science": "bg-emerald-600 border-emerald-500",
      "General Study": "bg-slate-600 border-slate-500"
    };
    return colors[subj] || "bg-zinc-600 border-zinc-500";
  };

  if (sessionActive) {
    return (
      <div className="flex h-screen w-screen bg-black text-[#f5f5f7] overflow-hidden select-none font-sans antialiased">
        {/* Immersive Focus Sidebar - Hidden in Very Strict Mode (Unless Coding Sandbox is enabled) */}
        {(sessionMode !== "very_strict" || enableCodingSandbox) && (
          <div className="w-16 bg-[#0f0f15] border-r border-zinc-900/60 flex flex-col justify-between items-center py-6 z-20">
            <div className="space-y-6 flex flex-col items-center w-full">
              {/* Minimal Logo indicator */}
              <div className="relative flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-[#0077ff] to-[#7b2ff7] shadow-lg shadow-blue-500/20">
                <Compass className="w-4 h-4 text-white animate-pulse" />
              </div>
              
              {/* Nav tabs */}
              <div className="flex flex-col space-y-4 pt-6 w-full items-center">
                <button
                  onClick={() => setSessionTab("timer")}
                  className={`p-2 rounded-lg transition-colors ${
                    sessionTab === "timer"
                      ? "bg-zinc-900 text-white border border-zinc-800"
                      : "text-zinc-500 hover:text-zinc-300"
                  }`}
                  title="Focus Timer"
                >
                  <Clock className="w-5 h-5" />
                </button>
                
                {sessionMode !== "very_strict" && (
                  <>
                    <button
                      onClick={() => setSessionTab("ai")}
                      className={`p-2 rounded-lg transition-colors ${
                        sessionTab === "ai"
                          ? "bg-zinc-900 text-white border border-zinc-800"
                          : "text-zinc-500 hover:text-zinc-300"
                      }`}
                      title="Study AI Assistant"
                    >
                      <Sparkles className="w-5 h-5" />
                    </button>
                    <button
                      onClick={() => setSessionTab("tools")}
                      className={`p-2 rounded-lg transition-colors ${
                        sessionTab === "tools"
                          ? "bg-zinc-900 text-white border border-zinc-800"
                          : "text-zinc-500 hover:text-zinc-300"
                      }`}
                      title="Student Tools"
                    >
                      <BookOpen className="w-5 h-5" />
                    </button>
                    {pdfUrl && (
                      <button
                        onClick={() => setSessionTab("pdf")}
                        className={`p-2 rounded-lg transition-colors ${
                          sessionTab === "pdf"
                            ? "bg-zinc-900 text-white border border-zinc-800"
                            : "text-zinc-500 hover:text-zinc-300"
                        }`}
                        title="Active Study PDF"
                      >
                        <FileText className="w-5 h-5" />
                      </button>
                    )}
                  </>
                )}

                {enableCodingSandbox && (
                  <button
                    onClick={() => setSessionTab("sandbox")}
                    className={`p-2 rounded-lg transition-colors ${
                      sessionTab === "sandbox"
                        ? "bg-zinc-900 text-white border border-zinc-800"
                        : "text-zinc-500 hover:text-zinc-300"
                    }`}
                    title="Coding Sandbox"
                  >
                    <Code className="w-5 h-5" />
                  </button>
                )}
              </div>
            </div>
            
            {/* Bottom indicator */}
            <div className="flex flex-col items-center space-y-3">
              <span className="capitalize px-1.5 py-0.5 rounded bg-zinc-950 font-mono text-[8px] text-zinc-450 border border-zinc-900">
                {sessionMode === "very_strict" ? "Very Strict (Code)" : sessionMode.replace("_", " ")}
              </span>
              <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div>
            </div>
          </div>
        )}

        {/* Immersive Workspace */}
        <div className="flex-1 flex flex-col bg-black overflow-y-auto relative z-10">
          
          {/* Custom Window Header for dragging (only window controls in lighter modes) */}
          <div className="h-10 bg-[#0f0f15]/50 border-b border-zinc-950 flex items-center justify-between px-6 select-none cursor-default">
            <div className="text-[10px] text-zinc-500 font-mono flex items-center space-x-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#7b2ff7] animate-pulse"></span>
              <span>FOCUS SESSION ACTIVE — {sessionSubject.toUpperCase()}</span>
            </div>
            {/* Minimize/Close hidden in strict locks */}
            <div className="flex items-center space-x-4">
              {isWebviewReady && sessionMode === "light" && (
                <>
                  <button onClick={handleMinimize} className="text-zinc-500 hover:text-zinc-300 text-xs px-2">─</button>
                  <button onClick={handleClose} className="text-zinc-500 hover:text-red-500 text-xs px-2">✕</button>
                </>
              )}
            </div>
          </div>

        {/* Corner Hover Timer */}
        {(sessionTab !== "timer" || sessionMode === "very_strict") && (
          <div className="absolute top-12 right-6 z-50 group cursor-pointer select-none">
            {sessionMode === "very_strict" ? (
              // Very Strict Mode: red dot "Hover for Timer"
              <div className="relative">
                {/* Hover state */}
                <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-200 bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 flex items-center space-x-2 shadow-lg">
                  <Clock className="w-3.5 h-3.5 text-red-500" />
                  <span className="font-mono text-xs text-white font-bold">{formatTime(timeLeft)} left</span>
                </div>
                {/* Default state */}
                <div className="absolute top-0 right-0 group-hover:opacity-0 transition-opacity duration-200 flex items-center space-x-1.5 px-3 py-1.5 bg-zinc-950 border border-zinc-900 rounded-lg shadow-md pointer-events-none">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"></span>
                  <span className="text-[9px] text-zinc-400 font-mono tracking-wider uppercase">Hover for Timer</span>
                </div>
              </div>
            ) : (
              // Other Modes: blue clock "View Time"
              <div className="relative">
                {/* Hover state */}
                <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-200 bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 flex items-center space-x-2 shadow-lg">
                  <Clock className="w-3.5 h-3.5 text-blue-500" />
                  <span className="font-mono text-xs text-white font-bold">{formatTime(timeLeft)}</span>
                </div>
                {/* Default state */}
                <div className="absolute top-0 right-0 group-hover:opacity-0 transition-opacity duration-200 flex items-center space-x-1.5 px-3 py-1.5 bg-zinc-950 border border-zinc-900 rounded-lg shadow-md pointer-events-none">
                  <Clock className="w-3.5 h-3.5 text-blue-500/80 animate-pulse" />
                  <span className="text-[9px] text-zinc-400 font-mono tracking-wider uppercase">View Time</span>
                </div>
              </div>
            )}
          </div>
        )}

          {/* Tab 1: Focus Timer */}
          {sessionTab === "timer" && (
            <div className="flex-1 p-8 overflow-y-auto max-w-4xl w-full mx-auto flex flex-col items-center justify-center space-y-8 relative">
              
              {/* breathing focus indicator glow */}
              <div className="relative flex items-center justify-center w-72 h-72">
                <div className="absolute inset-0 rounded-full bg-gradient-to-r from-blue-600/10 to-purple-600/10 blur-3xl animate-pulse"></div>
                
                {/* SVG circular progress ring */}
                <svg className="w-64 h-64 transform -rotate-90">
                  <circle
                    cx="128"
                    cy="128"
                    r="116"
                    className="stroke-zinc-900 fill-transparent"
                    strokeWidth="8"
                  />
                  <motion.circle
                    cx="128"
                    cy="128"
                    r="116"
                    className={`fill-transparent transition-all duration-1000 ${
                      sessionMode === "very_strict" 
                        ? "stroke-red-500" 
                        : sessionMode === "strict" 
                          ? "stroke-amber-500" 
                          : "stroke-blue-500"
                    }`}
                    strokeWidth="8"
                    strokeDasharray={2 * Math.PI * 116}
                    animate={{
                      strokeDashoffset: 2 * Math.PI * 116 * (1 - Math.max(0, Math.min(1, timeLeft / targetTime)))
                    }}
                  />
                </svg>

                {/* Timer text / quotes switcher */}
                {sessionMode === "very_strict" ? (
                  <div className="absolute flex flex-col items-center justify-center text-center px-6 space-y-2">
                    <Shield className="w-9 h-9 text-red-500/80 animate-pulse" />
                    <span className="text-[10px] font-mono tracking-widest text-zinc-500 uppercase">{sessionSubject}</span>
                    <AnimatePresence mode="wait">
                      <motion.p
                        key={currentQuoteIdx}
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -5 }}
                        transition={{ duration: 0.5 }}
                        className="text-[11px] text-zinc-350 italic max-w-[190px] leading-relaxed font-light"
                      >
                        "{quotes[currentQuoteIdx]}"
                      </motion.p>
                    </AnimatePresence>
                  </div>
                ) : (
                  <div className="absolute flex flex-col items-center justify-center text-center space-y-1">
                    <span className="text-[10px] font-mono tracking-widest text-zinc-500 uppercase">{sessionSubject}</span>
                    <h1 className="text-5xl font-black font-mono tracking-tighter text-white">{formatTime(timeLeft)}</h1>
                    <span className={`px-2 py-0.5 text-[9px] rounded font-mono uppercase ${
                      sessionMode === "strict" 
                        ? "bg-amber-950/40 text-amber-400 border border-amber-500/40" 
                        : sessionMode === "moderate"
                          ? "bg-blue-950/40 text-blue-400 border border-blue-500/40"
                          : "bg-zinc-900 text-zinc-405 border border-zinc-800"
                    }`}>{sessionMode.replace("_", " ")}</span>
                  </div>
                )}
              </div>

              {/* Goal Title */}
              <div className="text-center space-y-1 max-w-md">
                <span className="text-[10px] text-zinc-500 font-mono uppercase tracking-widest">Active Study Goal</span>
                <p className="text-lg font-medium text-zinc-250">"{sessionGoal}"</p>
              </div>

              {/* Media & Ambient controls (Only if not Very Strict) */}
              {sessionMode !== "very_strict" && (
                <div className="w-full max-w-xl glass-panel p-4 rounded-xl border border-zinc-900 grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Lofi sound console */}
                  <div className="space-y-3">
                    <span className="text-[10px] font-mono text-zinc-500 block uppercase tracking-wider">Lofi Ambient Synthesizer</span>
                    <div className="grid grid-cols-3 gap-2">
                      <button
                        onClick={() => setAmbientRain(!ambientRain)}
                        className={`p-2 rounded text-center text-xs border transition-all ${
                          ambientRain ? "bg-blue-950/30 border-blue-500 text-blue-400" : "bg-zinc-950 border-zinc-900 text-zinc-500"
                         }`}
                       >
                         🌧️ Rain
                       </button>
                       <button
                         onClick={() => setAmbientNoise(!ambientNoise)}
                         className={`p-2 rounded text-center text-xs border transition-all ${
                           ambientNoise ? "bg-amber-950/30 border-amber-500 text-amber-400" : "bg-zinc-950 border-zinc-900 text-zinc-500"
                         }`}
                       >
                         ☕ Cafe
                       </button>
                       <button
                         onClick={() => setLofiMusic(!lofiMusic)}
                         className={`p-2 rounded text-center text-xs border transition-all ${
                           lofiMusic ? "bg-purple-950/30 border-purple-500 text-purple-400" : "bg-zinc-950 border-zinc-900 text-zinc-500"
                         }`}
                       >
                         🎵 Radio
                       </button>
                     </div>
                   </div>

                   {/* Spotify & Tool Controls */}
                   <div className="space-y-3 border-t md:border-t-0 md:border-l border-zinc-900 pt-3 md:pt-0 md:pl-4">
                     <span className="text-[10px] font-mono text-zinc-500 block uppercase tracking-wider">Workspace Controls</span>
                     <div className="flex items-center space-x-2">
                       {/* Spotify controller */}
                       <div className="flex items-center space-x-1 p-1 rounded bg-zinc-950 border border-zinc-900">
                         <button onClick={() => handleSpotifyControl("prev")} className="p-1.5 text-zinc-500 hover:text-white" title="Prev Track">
                           <SkipForward className="w-3.5 h-3.5 rotate-180" />
                         </button>
                         <button onClick={() => handleSpotifyControl("play_pause")} className="p-1.5 text-zinc-500 hover:text-white" title="Play/Pause">
                           {spotifyPlaying ? <Pause className="w-3.5 h-3.5 text-green-500 fill-green-500" /> : <Play className="w-3.5 h-3.5 fill-zinc-500" />}
                         </button>
                         <button onClick={() => handleSpotifyControl("next")} className="p-1.5 text-zinc-500 hover:text-white" title="Next Track">
                           <SkipForward className="w-3.5 h-3.5" />
                         </button>
                       </div>
                       
                       {/* File / PDF access */}
                        {(sessionMode === "strict" || sessionMode === "moderate" || sessionMode === "light") && (
                          <button 
                            onClick={handlePDFOpen} 
                            className="px-2.5 py-2 rounded bg-zinc-950 border border-zinc-900 text-xs text-zinc-400 hover:text-white flex items-center space-x-1.5"
                            title="Open Study PDF"
                          >
                            <FileText className="w-3.5 h-3.5" />
                            <span>PDF</span>
                          </button>
                        )}
                        {sessionMode === "strict" && (
                          <button 
                            onClick={handleExplorerOpen}
                            className="px-2.5 py-2 rounded bg-zinc-950 border border-zinc-900 text-xs text-zinc-400 hover:text-white flex items-center space-x-1.5"
                            title="Open File Explorer"
                          >
                            <Folder className="w-3.5 h-3.5" />
                            <span>Explorer</span>
                          </button>
                        )}
                     </div>
                   </div>
                 </div>
               )}

              {/* Exit Console */}
              <div className="flex items-center space-x-4">
                  <button
                    onClick={handleExtendSession}
                    className="px-4 py-2.5 rounded-lg border border-zinc-800 bg-zinc-950 hover:bg-zinc-900 text-xs text-zinc-300 font-mono transition-all active:scale-95 flex items-center space-x-1.5"
                    title="Extend Session +15 Mins"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>+15 Min</span>
                  </button>

                <div className="flex flex-col items-center space-y-2">
                  {timeLeft <= 0 ? (
                    <button
                      onClick={() => handleStopSession()}
                      className="px-6 py-2.5 rounded-lg border border-emerald-500/30 bg-emerald-950/10 hover:bg-emerald-950/30 text-xs text-emerald-400 font-bold transition-all active:scale-95 flex items-center space-x-1.5 shadow-lg shadow-emerald-500/5"
                    >
                      <Check className="w-4 h-4" />
                      <span>Finish Session & Log Stats</span>
                    </button>
                  ) : (
                    sessionMode !== "very_strict" && (
                      <>
                        <button
                          onMouseDown={handleExitMouseDown}
                          onMouseUp={handleExitMouseUp}
                          onMouseLeave={handleExitMouseUp}
                          onTouchStart={handleExitMouseDown}
                          onTouchEnd={handleExitMouseUp}
                          className="px-6 py-2.5 rounded-lg border border-red-500/20 bg-red-950/5 text-xs text-[#ef4444] font-semibold relative overflow-hidden transition-all hover:bg-red-950/20 active:scale-95"
                        >
                          <div className="absolute top-0 bottom-0 left-0 bg-red-500/10 transition-all" style={{ width: `${exitHoldProgress}%` }}></div>
                          <span className="relative z-10 flex items-center space-x-1">
                            <AlertTriangle className="w-3.5 h-3.5 text-red-500" />
                            <span>{sessionMode === "light" ? "Exit Session" : "Hold Click to Emergency Exit (10s)"}</span>
                          </span>
                        </button>
                        {showExitWarning && sessionMode !== "light" && (
                          <span className="text-[10px] text-red-400 font-mono animate-pulse">Emergency exit will mark your session interrupted and penalize score!</span>
                        )}
                      </>
                    )
                  )}
                </div>
              </div>
            </div>
           )}

           {/* Tab 2: AI Doubts Solver */}
           {sessionTab === "ai" && sessionMode !== "very_strict" && (
             <div className="flex-1 p-8 overflow-y-auto max-w-5xl w-full mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6 h-[72vh]">
               {/* Left sidebar: tools selection */}
               <div className="glass-panel p-6 rounded-xl border border-zinc-900 flex flex-col space-y-4 col-span-1 border-zinc-800">
                 <div>
                   <h3 className="text-sm font-semibold tracking-wider text-zinc-400">STUDY AI OPTIONS</h3>
                   <p className="text-zinc-650 text-[11px] mt-0.5">Pick a specific doubt solver utility.</p>
                 </div>
                 
                 <div className="space-y-1.5 overflow-y-auto pr-1">
                   {[
                     { id: "doubt_solver", label: "Solve Doubt", desc: "Step-by-step problem solver" },
                     { id: "concept_explainer", label: "Explain Concept", desc: "Simplified details & analogies" },
                     { id: "summarizer", label: "Summarize Topic", desc: "Structured core review notes" },
                     { id: "flashcards", label: "Generate Flashcards", desc: "Q&A high-yield flashcards" },
                     { id: "notes_generator", label: "Revision Notes", desc: "Hierarchy and outline creator" },
                     { id: "quiz_maker", label: "Create Quiz", desc: "3-question MCQ with key" },
                     { id: "formula_explainer", label: "Explain Formula", desc: "Formula variable breakdown" },
                     { id: "study_planner", label: "Study Plan", desc: "Revision schedule planner" }
                   ].map((tool) => (
                     <button
                       key={tool.id}
                       onClick={() => setAiTool(tool.id)}
                       className={`w-full text-left p-3 rounded-lg border text-xs transition-all ${
                         aiTool === tool.id
                           ? "bg-purple-950/20 border-purple-500 text-purple-400 font-semibold shadow-inner"
                           : "bg-zinc-950 border-zinc-900 text-zinc-400 hover:border-zinc-800"
                       }`}
                     >
                       <div className="font-semibold">{tool.label}</div>
                       <div className="text-[10px] opacity-75 font-normal mt-0.5">{tool.desc}</div>
                     </button>
                   ))}
                 </div>
               </div>

               {/* Right panel: chat and input */}
               <div className="glass-panel p-6 rounded-xl border border-zinc-900 flex flex-col col-span-2 h-full border-zinc-800">
                 <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2 select-text">
                   {aiChat.map((msg, idx) => (
                     <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                       <div className={`max-w-[85%] rounded-xl p-3.5 text-xs line-clamp-none ${
                         msg.role === "user"
                           ? "bg-zinc-900 text-white font-medium rounded-tr-none border border-zinc-800"
                           : msg.role === "system"
                             ? "bg-zinc-950 text-amber-400 font-mono text-[10px] border border-amber-900/20"
                             : "bg-purple-950/10 text-zinc-300 rounded-tl-none border border-purple-900/10 leading-relaxed font-sans"
                       }`}>
                         <div className="space-y-1.5 whitespace-pre-wrap">{msg.text}</div>
                       </div>
                     </div>
                   ))}
                   {aiLoading && (
                     <div className="flex justify-start">
                       <div className="bg-purple-950/10 text-purple-400 rounded-xl rounded-tl-none p-3.5 text-xs border border-purple-900/10 flex items-center space-x-2">
                         <div className="flex space-x-1">
                           <span className="w-1.5 h-1.5 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></span>
                           <span className="w-1.5 h-1.5 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></span>
                           <span className="w-1.5 h-1.5 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></span>
                         </div>
                         <span className="font-mono text-[10px]">Study AI thinking...</span>
                       </div>
                     </div>
                   )}
                 </div>

                 {/* Input Bar */}
                 <div className="flex space-x-2 pt-2 border-t border-zinc-950">
                   <button
                     onClick={handleTriggerScreenCapture}
                     className="px-3 rounded-lg bg-zinc-950 hover:bg-zinc-900 border border-zinc-900 hover:border-zinc-800 text-zinc-400 hover:text-white flex items-center justify-center space-x-1.5"
                     title="Capture selected area on your monitor"
                   >
                     <Monitor className="w-4.5 h-4.5" />
                     <span className="text-[10px] hidden md:inline">CAPTURE SCREEN</span>
                   </button>
                   <textarea
                     placeholder="Enter doubt query or paste question here..."
                     value={aiInput}
                     onChange={(e) => setAiInput(e.target.value)}
                     onKeyDown={(e) => {
                       if (e.key === "Enter" && !e.shiftKey) {
                         e.preventDefault();
                         handleQueryAI();
                       }
                     }}
                     className="flex-1 bg-zinc-950 border border-zinc-900 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-zinc-800 resize-none h-10 min-h-10 max-h-24"
                   />
                   <button
                     onClick={handleQueryAI}
                     disabled={aiLoading}
                     className="px-4 bg-purple-600 hover:bg-purple-500 text-white rounded-lg font-semibold text-xs flex items-center justify-center"
                   >
                     Send
                   </button>
                 </div>
               </div>
             </div>
           )}

           {/* Tab 3: Student Tools Embed */}
           {sessionTab === "tools" && sessionMode !== "very_strict" && (
             <div className="flex-1 p-8 overflow-y-auto max-w-6xl w-full mx-auto h-[75vh] flex flex-col">
               <div className="glass-panel rounded-xl border border-zinc-900 overflow-hidden flex flex-col flex-1 border-zinc-800">
                 <div className="bg-[#0f0f15]/50 border-b border-zinc-950 px-4 py-2 flex items-center justify-between text-xs text-zinc-500 border-zinc-950">
                   <div className="flex items-center space-x-2">
                     <BookOpen className="w-3.5 h-3.5 text-blue-500" />
                     <span className="font-mono">https://student-tools-seven.vercel.app/</span>
                   </div>
                   <a href="https://student-tools-seven.vercel.app/" target="_blank" className="hover:text-white">Open External ↗</a>
                 </div>
                 <iframe
                   src="https://student-tools-seven.vercel.app/"
                   className="w-full flex-1 border-none bg-black"
                   title="Student Tools Workspace"
                 />
               </div>
             </div>
           )}

           {/* Tab 4: In-App PDF Viewer */}
           {sessionTab === "pdf" && sessionMode !== "very_strict" && (
             <div className="flex-1 p-8 overflow-hidden max-w-6xl w-full mx-auto h-[75vh] flex flex-col">
               <div className="glass-panel rounded-xl border border-zinc-900 overflow-hidden flex flex-col flex-1 border-zinc-800">
                 <div className="bg-[#0f0f15]/50 border-b border-zinc-950 px-4 py-2.5 flex items-center justify-between text-xs text-zinc-500 border-zinc-950">
                   <div className="flex items-center space-x-2">
                     <FileText className="w-3.5 h-3.5 text-blue-500" />
                     <span className="font-mono text-zinc-300">In-App Study PDF Viewer</span>
                   </div>
                   <div className="flex items-center space-x-2">
                     <button 
                       onClick={() => setSessionTab("timer")}
                       className="px-3 py-1 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 rounded text-[10px] text-zinc-300 transition-colors"
                     >
                       Minimize to Timer
                     </button>
                     <button 
                       onClick={() => {
                         setPdfUrl("");
                         setSessionTab("timer");
                       }}
                       className="px-3 py-1 bg-red-950/20 hover:bg-red-950/40 border border-red-900/30 rounded text-[10px] text-red-400 transition-colors"
                     >
                       Close Document
                     </button>
                   </div>
                 </div>
                 <iframe
                   src={pdfUrl}
                   className="w-full flex-1 border-none bg-zinc-950"
                   title="In-App Study PDF Viewer"
                 />
               </div>
             </div>
           )}

           {/* Tab 5: Coding Sandbox */}
           {sessionTab === "sandbox" && (
             <div className="flex-1 p-6 overflow-hidden max-w-6xl w-full mx-auto h-[80vh] flex flex-col space-y-4">
               <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-4 overflow-hidden">
                 
                 {/* Left Column: Code Editor */}
                 <div className="glass-panel p-4 rounded-xl border border-zinc-900 flex flex-col overflow-hidden border-zinc-800 bg-[#07070b]/60">
                   <div className="flex items-center justify-between pb-3 border-b border-zinc-900 mb-3">
                     <div className="flex items-center space-x-2">
                       <Code className="w-4 h-4 text-blue-500 animate-pulse" />
                       <span className="text-xs font-bold font-mono text-zinc-300">workspace.{(sandboxLang === "python" ? "py" : sandboxLang === "javascript" ? "js" : "html")}</span>
                     </div>
                     <div className="flex items-center space-x-1.5 bg-zinc-950 p-1 rounded border border-zinc-900">
                       {[
                         { id: "python", label: "Python 3" },
                         { id: "javascript", label: "JavaScript" },
                         { id: "html", label: "HTML/CSS" }
                       ].map((lang) => (
                         <button
                           key={lang.id}
                           onClick={() => handleLangChange(lang.id)}
                           className={`px-2 py-1 rounded text-[10px] font-semibold transition-all ${
                             sandboxLang === lang.id
                               ? "bg-zinc-850 text-white font-bold"
                               : "text-zinc-500 hover:text-zinc-300"
                           }`}
                         >
                           {lang.label}
                         </button>
                       ))}
                     </div>
                   </div>
                   
                   <div className="flex-1 flex overflow-hidden relative rounded-lg border border-zinc-950 bg-black/40">
                     {/* Simulated Line Numbers */}
                     <div className="w-10 bg-zinc-950/80 border-r border-zinc-900 py-3 flex flex-col items-center select-none text-[10px] font-mono text-zinc-600 leading-relaxed">
                       {Array.from({ length: Math.max(15, sandboxCode.split("\n").length) }).map((_, i) => (
                         <div key={i} className="h-5 flex items-center justify-end pr-1.5 w-full">{i + 1}</div>
                       ))}
                     </div>
                     {/* Editor Textarea */}
                     <textarea
                       value={sandboxCode}
                       onChange={(e) => setSandboxCode(e.target.value)}
                       spellCheck={false}
                       autoCapitalize="none"
                       autoComplete="off"
                       autoCorrect="off"
                       className="flex-1 p-3 bg-transparent text-xs font-mono text-zinc-200 focus:outline-none resize-none leading-relaxed overflow-y-auto whitespace-pre tab-size-4"
                       style={{ tabSize: 4 }}
                     />
                   </div>
                 </div>

                 {/* Right Column: Execution Output */}
                 <div className="glass-panel p-4 rounded-xl border border-zinc-900 flex flex-col overflow-hidden border-zinc-800 bg-[#07070b]/60">
                   <div className="flex items-center justify-between pb-3 border-b border-zinc-900 mb-3">
                     <div className="flex items-center space-x-2">
                       <Terminal className="w-4 h-4 text-emerald-500" />
                       <span className="text-xs font-bold font-mono text-zinc-300">execution_terminal</span>
                     </div>
                     <div className="flex items-center space-x-2">
                       <button
                         onClick={handleSaveScript}
                         className="px-2.5 py-1.5 rounded bg-zinc-950 hover:bg-zinc-900 border border-zinc-900 text-[10px] text-zinc-400 hover:text-white flex items-center space-x-1"
                         title="Save script to file"
                       >
                         <span>Save Script</span>
                       </button>
                       <button
                         onClick={() => setSandboxOutput("Console ready...\n")}
                         className="px-2.5 py-1.5 rounded bg-zinc-950 hover:bg-zinc-900 border border-zinc-900 text-[10px] text-zinc-500 hover:text-zinc-300"
                       >
                         Clear
                       </button>
                       <button
                         onClick={handleRunSandboxCode}
                         disabled={sandboxRunning}
                         className={`px-3 py-1.5 rounded text-[10px] font-bold text-white flex items-center space-x-1.5 ${
                           sandboxRunning 
                             ? "bg-blue-850 cursor-not-allowed opacity-50" 
                             : "bg-blue-600 hover:bg-blue-500 shadow-md shadow-blue-500/10 active:scale-95"
                         }`}
                       >
                         {sandboxRunning ? (
                           <>
                             <span className="w-2 h-2 rounded-full bg-white animate-ping"></span>
                             <span>Running...</span>
                           </>
                         ) : (
                           <>
                             <span>Run Code</span>
                           </>
                         )}
                       </button>
                     </div>
                   </div>

                   {/* Output Console / Preview */}
                   <div className="flex-1 flex flex-col space-y-3 overflow-hidden">
                     {sandboxLang === "html" ? (
                       <div className="flex-1 flex flex-col space-y-2 overflow-hidden">
                         <span className="text-[9px] font-mono text-zinc-500 uppercase tracking-wider">Live HTML Render View</span>
                         <div className="flex-1 bg-white rounded-lg overflow-hidden border border-zinc-900">
                           <iframe
                             srcDoc={sandboxCode}
                             className="w-full h-full bg-white"
                             sandbox="allow-scripts"
                             title="HTML Live Sandbox Preview"
                           />
                         </div>
                       </div>
                     ) : (
                       <div className="flex-1 bg-black p-4 rounded-lg border border-zinc-950 font-mono text-xs text-emerald-450 overflow-y-auto whitespace-pre-wrap select-text leading-relaxed scrollbar-thin">
                         {sandboxOutput}
                       </div>
                     )}
                   </div>
                 </div>

               </div>
             </div>
           )}
         </div>
       </div>
    );
  }

  return (
    <div className="relative w-screen h-screen bg-black text-[#f5f5f7] overflow-hidden select-none font-sans antialiased">
      {/* Glowing Space Background */}
      <div className="absolute inset-0 bg-black overflow-hidden pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[-10%] w-[60%] h-[60%] rounded-full bg-blue-900/10 blur-[130px] animate-pulse" style={{ animationDuration: '10s' }}></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[60%] h-[60%] rounded-full bg-purple-900/10 blur-[130px] animate-pulse" style={{ animationDuration: '12s' }}></div>
        <div className="absolute top-[30%] left-[40%] w-[40%] h-[40%] rounded-full bg-zinc-900/5 blur-[150px]"></div>
      </div>

      {/* Top Menu Bar */}
      <div className="absolute top-0 left-0 right-0 h-8 bg-zinc-950 border-b border-zinc-900/50 flex items-center justify-between px-4 z-45 text-xs font-medium text-zinc-400 select-none">
        <div className="flex items-center space-x-4">
          <span className="font-bold text-white flex items-center space-x-1.5 cursor-default">
            <Compass className="w-3.5 h-3.5 text-blue-500 animate-spin" style={{ animationDuration: '20s' }} />
            <span>FocusFlow OS</span>
          </span>
          <span className="text-[10px] text-zinc-500 cursor-default">File</span>
          <span className="text-[10px] text-zinc-500 cursor-default">Edit</span>
          <span className="text-[10px] text-zinc-500 cursor-default">View</span>
          <span className="text-[10px] text-zinc-500 cursor-default">Go</span>
          <span className="text-[10px] text-zinc-500 cursor-default">Help</span>
        </div>
        <div className="flex items-center space-x-4 font-mono text-[10px] text-zinc-500">
          <span className="flex items-center space-x-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>{isWebviewReady ? "DESKTOP RUNTIME" : "BROWSER MOCK"}</span>
          </span>
          <span>Session: {sessionActive ? "ON" : "OFF"}</span>
        </div>
      </div>

      {/* Main Desktop Grid Workspace */}
      <div className="absolute inset-0 pt-10 pb-24 px-8 grid grid-cols-12 gap-6 z-10 overflow-hidden">
        {/* Left Side: App Shortcuts Grid */}
        <div className="col-span-3 flex flex-col space-y-4 pt-4">
          {[
            { id: "session_setup", label: "Focus Timer.app", icon: Clock, color: "from-blue-600 to-indigo-700 shadow-blue-500/20" },
            { id: "ai", label: "AI Assistant.app", icon: Sparkles, color: "from-purple-600 to-fuchsia-700 shadow-purple-500/20" },
            { id: "student_tools", label: "Student Tools.app", icon: BookOpen, color: "from-emerald-600 to-teal-700 shadow-emerald-500/20" },
            { id: "history", label: "Analytics.app", icon: BarChart2, color: "from-amber-600 to-orange-700 shadow-amber-500/20" },
            { id: "settings", label: "Settings.app", icon: Settings, color: "from-zinc-600 to-slate-700 shadow-zinc-650/20" }
          ].map((app) => {
            const Icon = app.icon;
            return (
              <button
                key={app.id}
                onClick={() => setActiveTab(app.id)}
                className="group flex flex-col items-center justify-center w-24 h-24 rounded-2xl hover:bg-white/5 border border-transparent hover:border-white/10 transition-all duration-300 pointer-events-auto"
              >
                <div className={`w-12 h-12 rounded-2xl bg-gradient-to-br ${app.color} shadow-lg flex items-center justify-center text-white transform group-hover:scale-105 transition-transform duration-300`}>
                  <Icon className="w-5.5 h-5.5" />
                </div>
                <span className="mt-2 text-[10px] font-medium text-zinc-400 group-hover:text-white font-mono truncate max-w-full px-1">{app.label}</span>
              </button>
            );
          })}
        </div>

        {/* Center/Right Side: Desktop Widgets */}
        <div className="col-span-9 grid grid-cols-2 gap-6 pt-4 h-full overflow-y-auto pr-2 pb-8 pointer-events-auto">
          {/* Widget 1: Focus Metrics Dashboard */}
          <div className="glass-panel p-6 rounded-2xl border border-zinc-800/40 bg-zinc-950 space-y-4 h-fit border-zinc-900/60">
            <div className="flex items-center justify-between border-b border-zinc-900/40 pb-3">
              <h3 className="text-[10px] font-bold tracking-wider text-zinc-500 uppercase font-mono">Focus Dashboard Metrics</h3>
              <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"></span>
            </div>
            
            <div className="grid grid-cols-3 gap-3">
              <div className="p-3 bg-zinc-950/70 border border-zinc-900/50 rounded-xl text-center space-y-1">
                <span className="text-[9px] text-zinc-500 font-mono block uppercase">Focus Score</span>
                <span className="text-lg font-black text-white">{stats.avg_focus_score}%</span>
              </div>
              <div className="p-3 bg-zinc-950/70 border border-zinc-900/50 rounded-xl text-center space-y-1">
                <span className="text-[9px] text-zinc-500 font-mono block uppercase">Hours Studied</span>
                <span className="text-lg font-black text-white">{stats.total_hours}h</span>
              </div>
              <div className="p-3 bg-zinc-950/70 border border-zinc-900/50 rounded-xl text-center space-y-1">
                <span className="text-[9px] text-zinc-500 font-mono block uppercase">Tasks Done</span>
                <span className="text-lg font-black text-white">{stats.tasks_completed}</span>
              </div>
            </div>

            <div className="space-y-3 pt-1">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-zinc-400 font-medium font-sans">Active Target Score</span>
                <span className="text-[10px] text-zinc-400 font-bold font-mono">85%</span>
              </div>
              <div className="w-full bg-zinc-950 rounded-full h-1.5 overflow-hidden border border-zinc-900/40">
                <div className="bg-gradient-to-r from-blue-500 to-purple-600 h-1.5 rounded-full" style={{ width: `${Math.min(100, Math.max(0, stats.avg_focus_score))}%` }}></div>
              </div>
              
              {/* mini visual spark chart for last 7 days */}
              <div className="pt-2 border-t border-zinc-900/30 flex items-center justify-between">
                <span className="text-[9px] text-zinc-550 font-mono uppercase">7-Day Study Trend</span>
                <div className="flex items-end space-x-1.5 h-6 select-none pointer-events-none">
                  {Array.from({ length: 7 }).map((_, idx) => {
                    const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
                    const heightPercent = 20 + (idx * 12) % 75; // dynamic mock visual trend
                    return (
                      <div key={idx} className="flex-1 flex flex-col items-center h-full justify-end group">
                        <div className="w-full bg-zinc-900/40 rounded-t-sm h-8 relative flex items-end overflow-hidden border border-zinc-900/20">
                          <div className="w-full bg-gradient-to-t from-purple-600/70 to-blue-500/80 rounded-t-sm" style={{ height: `${heightPercent}%` }}></div>
                        </div>
                        <span className="text-[8px] text-zinc-600 font-mono mt-1">{days[idx].substring(0, 1)}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>

          {/* Widget 2: Today's Focus Goals */}
          <div className="glass-panel p-6 rounded-2xl border border-zinc-800/40 bg-zinc-950 flex flex-col justify-between space-y-4 h-fit border-zinc-900/60 max-h-[320px]">
            <div className="flex items-center justify-between border-b border-zinc-900/40 pb-3">
              <h3 className="text-[10px] font-bold tracking-wider text-zinc-500 uppercase font-mono">Today's Focus Goals</h3>
              <Plus className="w-3.5 h-3.5 text-zinc-400 hover:text-white cursor-pointer" onClick={handleAddGoal} />
            </div>

            <div className="space-y-1.5 overflow-y-auto max-h-[160px] pr-1 scrollbar-none select-none">
              {goals.length === 0 ? (
                <p className="text-zinc-650 text-xs py-4 text-center italic">No focus tasks active for today.</p>
              ) : (
                goals.map((g) => (
                  <div key={g.id} className="flex items-center justify-between p-2 rounded bg-zinc-950/60 border border-zinc-900/40">
                    <button 
                      onClick={() => handleToggleGoal(g.id)}
                      className="flex items-center space-x-2.5 text-left flex-1"
                    >
                      <div className={`w-3.5 h-3.5 rounded border flex items-center justify-center transition-colors ${
                        g.completed ? "bg-blue-600 border-blue-500 text-white" : "border-zinc-850"
                      }`}>
                        {g.completed && <Check className="w-2.5 h-2.5" />}
                      </div>
                      <span className={`text-[11px] ${g.completed ? "line-through text-zinc-600" : "text-zinc-350"}`}>{g.text}</span>
                    </button>
                    <button 
                      onClick={() => handleDeleteGoal(g.id)}
                      className="text-zinc-700 hover:text-red-400 p-0.5 transition-colors"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))
              )}
            </div>

            <div className="flex space-x-2 pt-2 border-t border-zinc-900/30">
              <input
                type="text"
                placeholder="New focus task..."
                value={newGoalText}
                onChange={(e) => setNewGoalText(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAddGoal()}
                className="flex-1 bg-zinc-950 border border-zinc-900 rounded-lg px-3 py-1.5 text-[11px] text-[#f5f5f7] focus:outline-none focus:border-zinc-800"
              />
              <button 
                onClick={handleAddGoal}
                className="px-3 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-805 border border-zinc-850 text-white text-[11px] font-semibold"
              >
                Add
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Floating macOS style Centered Window for Active Apps */}
      {activeTab !== "desktop" && activeTab !== "session" && (
        <div className="absolute inset-0 bg-black/80 z-30 flex items-center justify-center p-8 pointer-events-auto">
          <motion.div
            initial={{ scale: 0.97, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="w-full max-w-5xl h-[84vh] glass-panel rounded-2xl border border-zinc-800/80 bg-zinc-950 shadow-2xl shadow-black/95 flex flex-col overflow-hidden border-zinc-900"
          >
            {/* Window Header */}
            <div className="h-11 bg-zinc-950/60 border-b border-zinc-900/60 flex items-center justify-between px-4 select-none relative z-20">
              {/* Traffic Light Buttons */}
              <div className="flex items-center space-x-2 w-20">
                <button
                  onClick={() => setActiveTab("desktop")}
                  className="w-3.5 h-3.5 rounded-full bg-red-500 hover:bg-red-600 flex items-center justify-center text-[7px] text-red-950 font-bold transition-colors"
                  title="Close App"
                >
                  ✕
                </button>
                <button
                  onClick={() => setActiveTab("desktop")}
                  className="w-3.5 h-3.5 rounded-full bg-yellow-500 hover:bg-yellow-600 flex items-center justify-center text-[7px] text-yellow-950 font-bold transition-colors"
                  title="Minimize App"
                >
                  ─
                </button>
                <div className="w-3.5 h-3.5 rounded-full bg-green-500 opacity-60 cursor-not-allowed"></div>
              </div>

              {/* Title */}
              <span className="text-xs font-semibold text-zinc-300 font-mono uppercase tracking-wide">
                {activeTab === "session_setup" 
                  ? "Focus Timer Setup" 
                  : activeTab === "ai" 
                    ? "Study AI Solver" 
                    : activeTab === "student_tools" 
                      ? "Student Standalone Browser" 
                      : activeTab === "history" 
                        ? "Academic Analytics" 
                        : "Console Configuration"}
              </span>

              {/* Status */}
              <div className="w-20 flex justify-end text-[9px] text-zinc-500 font-mono tracking-widest">
                ACTIVE
              </div>
            </div>

            {/* Window Body Container */}
            <div className="flex-1 overflow-y-auto p-6 relative bg-zinc-950/30 scrollbar-thin">
          {activeTab === "session_setup" && (
            <div className="max-w-2xl mx-auto glass-panel p-8 rounded-xl border border-zinc-900 space-y-6">
              <div>
                <h1 className="text-2xl font-bold tracking-tight">Configure Deep Focus</h1>
                <p className="text-zinc-500 text-xs mt-1">Calibrate your study session environment before locking distractions.</p>
              </div>

              <div className="space-y-4">
                {/* Subject & Goal */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="col-span-1">
                    <label className="text-[10px] uppercase font-mono tracking-widest text-zinc-500 block mb-1">Subject</label>
                    <select
                      value={sessionSubject}
                      onChange={(e) => setSessionSubject(e.target.value)}
                      className="w-full bg-zinc-950 border border-zinc-900 rounded-lg p-2.5 text-sm focus:outline-none focus:border-zinc-800"
                    >
                      <option value="Physics">Physics</option>
                      <option value="Maths">Maths</option>
                      <option value="Chemistry">Chemistry</option>
                      <option value="Computer Science">Computer Science</option>
                      <option value="General Study">General Study</option>
                    </select>
                  </div>
                  <div className="col-span-2">
                    <label className="text-[10px] uppercase font-mono tracking-widest text-zinc-500 block mb-1">Session Target Goal</label>
                    <input
                      type="text"
                      placeholder="e.g. Finish Electrostatics Revision"
                      value={sessionGoal}
                      onChange={(e) => setSessionGoal(e.target.value)}
                      className="w-full bg-zinc-950 border border-zinc-900 rounded-lg p-2.5 text-sm focus:outline-none focus:border-zinc-800"
                    />
                  </div>
                </div>

                {/* Computer Science Coding Option */}
                {sessionSubject === "Computer Science" && (sessionMode === "strict" || sessionMode === "very_strict") && (
                  <motion.div 
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-4 rounded-lg bg-zinc-950 border border-zinc-900 flex items-start space-x-3 transition-all"
                  >
                    <input
                      type="checkbox"
                      id="enable_coding_sandbox"
                      checked={enableCodingSandbox}
                      onChange={(e) => setEnableCodingSandbox(e.target.checked)}
                      className="mt-1 h-4 w-4 rounded border-zinc-800 bg-zinc-950 text-blue-600 focus:ring-blue-600 focus:ring-offset-zinc-950 focus:ring-1 cursor-pointer"
                    />
                    <div className="flex flex-col">
                      <label htmlFor="enable_coding_sandbox" className="text-xs font-semibold text-white cursor-pointer">
                        Enable Built-in Coding Sandbox?
                      </label>
                      <p className="text-zinc-550 text-[10px] mt-0.5 leading-relaxed">
                        Since you are in {sessionMode === "strict" ? "Strict" : "Very Strict"} mode studying Computer Science, checking this will add a secure interactive IDE tab to write, compile, and run code within FocusFlow without opening any blocked external software.
                      </p>
                    </div>
                  </motion.div>
                )}

                {/* Computer Science Allowed Coding Application (Moderate Mode) */}
                {sessionSubject === "Computer Science" && sessionMode === "moderate" && (
                  <motion.div 
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-4 rounded-lg bg-zinc-950 border border-zinc-900 space-y-3 transition-all"
                  >
                    <div className="flex flex-col">
                      <label className="text-xs font-semibold text-white">
                        Allowed Coding Application (Moderate Mode)
                      </label>
                      <p className="text-zinc-550 text-[10px] mt-0.5 leading-relaxed">
                        Select which coding application you want to whitelist for this session. It will bypass foreground blocking checks.
                      </p>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <select
                        value={chosenCodingApp}
                        onChange={(e) => setChosenCodingApp(e.target.value)}
                        className="bg-zinc-950 border border-zinc-900 rounded-lg p-2 text-xs focus:outline-none focus:border-zinc-800 text-white"
                      >
                        <option value="Code.exe">VS Code (Code.exe)</option>
                        <option value="pycharm64.exe">PyCharm (pycharm64.exe)</option>
                        <option value="idle.exe">Python IDLE (idle.exe)</option>
                        <option value="notepad++.exe">Notepad++ (notepad++.exe)</option>
                        <option value="custom">Custom (Type below)...</option>
                      </select>
                      {chosenCodingApp === "custom" && (
                        <input
                          type="text"
                          placeholder="e.g. eclipse.exe"
                          value={customCodingAppText}
                          onChange={(e) => setCustomCodingAppText(e.target.value)}
                          className="bg-zinc-950 border border-zinc-900 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-zinc-800"
                        />
                      )}
                    </div>
                  </motion.div>
                )}

                {/* Duration & Mode */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="col-span-1">
                    <label className="text-[10px] uppercase font-mono tracking-widest text-zinc-500 block mb-1">Duration (Mins)</label>
                    <input
                      type="number"
                      min="5"
                      max="240"
                      value={sessionDuration}
                      onChange={(e) => setSessionDuration(Number(e.target.value))}
                      className="w-full bg-zinc-950 border border-zinc-900 rounded-lg p-2.5 text-sm focus:outline-none focus:border-zinc-800"
                    />
                  </div>
                  <div className="col-span-2">
                    <label className="text-[10px] uppercase font-mono tracking-widest text-zinc-500 block mb-1">Focus Guard Level</label>
                    <div className="grid grid-cols-4 gap-2">
                      {[
                        { id: "light", label: "Light", color: "border-zinc-800 hover:border-zinc-600" },
                        { id: "moderate", label: "Moderate", color: "border-zinc-800 hover:border-blue-900/50" },
                        { id: "strict", label: "Strict", color: "border-zinc-800 hover:border-amber-900/50" },
                        { id: "very_strict", label: "Very Strict", color: "border-zinc-800 hover:border-red-900/50" }
                      ].map((m) => (
                        <button
                          key={m.id}
                          onClick={() => setSessionMode(m.id)}
                          type="button"
                          className={`p-2.5 text-xs rounded-lg border transition-all text-center ${
                            sessionMode === m.id
                              ? m.id === "very_strict"
                                ? "bg-red-950/20 border-red-500 text-red-400 font-semibold"
                                : m.id === "strict"
                                  ? "bg-amber-950/20 border-amber-500 text-amber-400 font-semibold"
                                  : m.id === "moderate"
                                    ? "bg-blue-950/20 border-blue-500 text-blue-400 font-semibold"
                                    : "bg-zinc-800 border-zinc-700 text-white font-semibold"
                              : `bg-zinc-950 text-zinc-400 ${m.color}`
                          }`}
                        >
                          {m.label}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Focus Level Description warning */}
                <div className="p-4 rounded-lg bg-zinc-950 border border-zinc-900 text-xs text-zinc-400 space-y-1">
                  {sessionMode === "light" && (
                    <>
                      <p className="font-semibold text-white">Light Mode: Pomodoro Only</p>
                      <p>No window blocking or keyboard locking. Simple time tracking, study reminders, and AI tutor access.</p>
                    </>
                  )}
                  {sessionMode === "moderate" && (
                    <>
                      <p className="font-semibold text-blue-400">Moderate Mode: Controlled Whitelist</p>
                      <p>Allows access only to educational domains and whitelisted apps (e.g. YouTube, PW, Unacademy). All other apps/tabs are minimized.</p>
                    </>
                  )}
                  {sessionMode === "strict" && (
                    <>
                      <p className="font-semibold text-amber-400">Strict Mode: Limited Study Tools</p>
                      <p>Blocks Alt+Tab/Win key, locks desktop. Allows Spotify, File Explorer, local PDFs, and embeds Student Tools + AI doubt solver.</p>
                    </>
                  )}
                  {sessionMode === "very_strict" && (
                    <>
                      <p className="font-semibold text-red-500 flex items-center space-x-1">
                        <Shield className="w-3.5 h-3.5 text-red-500" />
                        <span>Very Strict Mode: Absolute Focus Cage</span>
                      </p>
                      <p>Complete fullscreen lockout. Keyboard combinations blocked. Zero external processes. Study AI and student tools disabled.</p>
                    </>
                  )}
                </div>

                {/* Custom Features Checklist */}
                <div className="p-4 rounded-lg bg-zinc-950 border border-zinc-900 space-y-3">
                  <span className="text-[10px] uppercase font-mono tracking-widest text-zinc-500 block">
                    Workspace Security Controls
                  </span>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {[
                      { id: "keyboard_lock", label: "Keyboard Lock", desc: "Block Win, Alt+Tab, Alt+F4" },
                      { id: "touchpad_lock", label: "Touchpad Lock", desc: "Disable multi-finger gestures" },
                      { id: "app_sweeper", label: "App Sweeper", desc: "Close unauthorized background apps" },
                      { id: "foreground_guard", label: "Foreground Guard", desc: "Minimize non-study windows" },
                      { id: "fullscreen", label: "Force Fullscreen", desc: "Prevent switching tabs" },
                      { id: "capture_protection", label: "Capture Protection", desc: "Prevent screenshot leaks" }
                    ].map((f) => {
                      const isLocked = isFeatureLocked(f.id);
                      return (
                        <label
                          key={f.id}
                          className={`flex items-start space-x-2.5 p-2 rounded-lg border transition-all cursor-pointer select-none ${
                            isLocked 
                              ? "bg-zinc-905/40 border-zinc-950 opacity-50 cursor-not-allowed" 
                              : "bg-zinc-950 border-zinc-900 hover:border-zinc-800"
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={customFeatures[f.id as keyof typeof customFeatures]}
                            disabled={isLocked}
                            onChange={(e) => {
                              if (!isLocked) {
                                setCustomFeatures((prev) => ({
                                  ...prev,
                                  [f.id]: e.target.checked
                                }));
                              }
                            }}
                            className="mt-0.5 h-3.5 w-3.5 rounded border-zinc-800 bg-zinc-950 text-blue-600 focus:ring-blue-600 focus:ring-offset-zinc-950 focus:ring-1"
                          />
                          <div className="flex flex-col">
                            <span className="text-[11px] font-medium text-zinc-200">{f.label}</span>
                            <span className="text-[9px] text-zinc-500 leading-relaxed mt-0.5">{f.desc}</span>
                          </div>
                        </label>
                      );
                    })}
                  </div>
                </div>

                {/* Launch Button */}
                <button
                  onClick={handleStartSession}
                  className="w-full py-3 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-semibold text-sm tracking-wider shadow-lg flex items-center justify-center space-x-2"
                >
                  <Play className="w-4.5 h-4.5 fill-white" />
                  <span>INITIALIZE WORKSPACE</span>
                </button>
              </div>
            </div>
          )}

          {/* --- SCREEN: FOCUS SESSION RUNNING --- */}
          {activeTab === "session" && (
            <div className="max-w-4xl mx-auto flex flex-col items-center justify-center min-h-[70vh] space-y-8 relative">
              
              {/* Corner Hover Timer for Very Strict Mode */}
              {sessionMode === "very_strict" && (
                <div className="absolute top-0 right-0 z-20 group cursor-pointer">
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-zinc-900 border border-zinc-905 rounded-lg px-3 py-1.5 flex items-center space-x-2">
                    <Clock className="w-3.5 h-3.5 text-zinc-400" />
                    <span className="font-mono text-xs text-white font-bold">{formatTime(timeLeft)} left</span>
                  </div>
                  <div className="group-hover:hidden flex items-center space-x-1.5 px-3 py-1.5 bg-zinc-900 rounded-lg border border-zinc-800">
                    <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"></span>
                    <span className="text-[10px] text-zinc-500 font-mono tracking-wider">HOVER FOR TIMER</span>
                  </div>
                </div>
              )}
              
              {/* breathing focus indicator glow */}
              <div className="relative flex items-center justify-center w-72 h-72">
                <div className="absolute inset-0 rounded-full bg-gradient-to-r from-blue-600/10 to-purple-600/10 blur-3xl animate-pulse"></div>
                
                {/* SVG circular progress ring */}
                <svg className="w-64 h-64 transform -rotate-90">
                  <circle
                    cx="128"
                    cy="128"
                    r="116"
                    className="stroke-zinc-900 fill-transparent"
                    strokeWidth="8"
                  />
                  <motion.circle
                    cx="128"
                    cy="128"
                    r="116"
                    className={`fill-transparent transition-all duration-1000 ${
                      sessionMode === "very_strict" 
                        ? "stroke-red-500" 
                        : sessionMode === "strict" 
                          ? "stroke-amber-500" 
                          : "stroke-blue-500"
                    }`}
                    strokeWidth="8"
                    strokeDasharray={2 * Math.PI * 116}
                    animate={{
                      strokeDashoffset: 2 * Math.PI * 116 * (1 - timeLeft / targetTime)
                    }}
                  />
                </svg>

                {/* Timer text / quotes switcher */}
                {sessionMode === "very_strict" ? (
                  <div className="absolute flex flex-col items-center justify-center text-center px-6 space-y-2">
                    <Shield className="w-9 h-9 text-red-500/80 animate-pulse" />
                    <span className="text-[10px] font-mono tracking-widest text-zinc-500 uppercase">{sessionSubject}</span>
                    <AnimatePresence mode="wait">
                      <motion.p
                        key={currentQuoteIdx}
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -5 }}
                        transition={{ duration: 0.5 }}
                        className="text-[11px] text-zinc-400 italic max-w-[190px] leading-relaxed"
                      >
                        "{quotes[currentQuoteIdx]}"
                      </motion.p>
                    </AnimatePresence>
                  </div>
                ) : (
                  <div className="absolute flex flex-col items-center justify-center text-center space-y-1">
                    <span className="text-[10px] font-mono tracking-widest text-zinc-500 uppercase">{sessionSubject}</span>
                    <h1 className="text-5xl font-black font-mono tracking-tighter text-white">{formatTime(timeLeft)}</h1>
                    <span className={`px-2 py-0.5 text-[9px] rounded font-mono uppercase ${
                      sessionMode === "strict" 
                        ? "bg-amber-950/40 text-amber-400 border border-amber-500/40" 
                        : "bg-blue-950/40 text-blue-400 border border-blue-800/40"
                    }`}>{sessionMode.replace("_", " ")}</span>
                  </div>
                )}
              </div>

              {/* Goal Title */}
              <div className="text-center space-y-1 max-w-md">
                <span className="text-[10px] text-zinc-500 font-mono uppercase tracking-widest">Active Study Goal</span>
                <p className="text-lg font-medium text-zinc-200">"{sessionGoal}"</p>
              </div>

              {/* Media Deck & Control Console */}
              <div className="w-full max-w-xl glass-panel p-4 rounded-xl border border-zinc-900 grid grid-cols-1 md:grid-cols-2 gap-4">
                
                {/* Lofi sound console */}
                <div className="space-y-3">
                  <span className="text-[10px] font-mono text-zinc-500 block uppercase tracking-wider">Lofi Ambient Synthesizer</span>
                  <div className="grid grid-cols-3 gap-2">
                    <button
                      onClick={() => setAmbientRain(!ambientRain)}
                      className={`p-2 rounded text-center text-xs border transition-all ${
                        ambientRain ? "bg-blue-950/30 border-blue-500 text-blue-400" : "bg-zinc-950 border-zinc-900 text-zinc-500"
                      }`}
                    >
                      🌧️ Rain
                    </button>
                    <button
                      onClick={() => setAmbientNoise(!ambientNoise)}
                      className={`p-2 rounded text-center text-xs border transition-all ${
                        ambientNoise ? "bg-amber-950/30 border-amber-500 text-amber-400" : "bg-zinc-950 border-zinc-900 text-zinc-500"
                      }`}
                    >
                      ☕ Cafe
                    </button>
                    <button
                      onClick={() => setLofiMusic(!lofiMusic)}
                      className={`p-2 rounded text-center text-xs border transition-all ${
                        lofiMusic ? "bg-purple-950/30 border-purple-500 text-purple-400" : "bg-zinc-950 border-zinc-900 text-zinc-500"
                      }`}
                    >
                      🎵 Radio
                    </button>
                  </div>
                </div>

                {/* Spotify & Tool Controls */}
                <div className="space-y-3 border-t md:border-t-0 md:border-l border-zinc-900 pt-3 md:pt-0 md:pl-4">
                  <span className="text-[10px] font-mono text-zinc-500 block uppercase tracking-wider">Workspace Controls</span>
                  <div className="flex items-center space-x-2">
                    {/* Spotify controller */}
                    {sessionMode !== "very_strict" && (
                      <div className="flex items-center space-x-1 p-1 rounded bg-zinc-950 border border-zinc-900">
                        <button onClick={() => handleSpotifyControl("prev")} className="p-1.5 text-zinc-500 hover:text-white" title="Prev Track">
                          <SkipForward className="w-3.5 h-3.5 rotate-180" />
                        </button>
                        <button onClick={() => handleSpotifyControl("play_pause")} className="p-1.5 text-zinc-500 hover:text-white" title="Play/Pause">
                          {spotifyPlaying ? <Pause className="w-3.5 h-3.5 text-green-500 fill-green-500" /> : <Play className="w-3.5 h-3.5 fill-zinc-500" />}
                        </button>
                        <button onClick={() => handleSpotifyControl("next")} className="p-1.5 text-zinc-500 hover:text-white" title="Next Track">
                          <SkipForward className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    )}
                    
                    {/* File / PDF access */}
                    {(sessionMode === "strict" || sessionMode === "moderate" || sessionMode === "light") && (
                      <button 
                        onClick={handlePDFOpen} 
                        className="px-2.5 py-2 rounded bg-zinc-950 border border-zinc-900 text-xs text-zinc-400 hover:text-white flex items-center space-x-1.5"
                        title="Open Study PDF"
                      >
                        <FileText className="w-3.5 h-3.5" />
                        <span>PDF</span>
                      </button>
                    )}
                    {sessionMode === "strict" && (
                      <button 
                        onClick={handleExplorerOpen}
                        className="px-2.5 py-2 rounded bg-zinc-950 border border-zinc-900 text-xs text-zinc-400 hover:text-white flex items-center space-x-1.5"
                        title="Open File Explorer"
                      >
                        <Folder className="w-3.5 h-3.5" />
                        <span>Explorer</span>
                      </button>
                    )}
                  </div>
                </div>

              </div>

              {/* Danger Zone: Emergency Exit Button */}
              <div className="flex flex-col items-center space-y-2">
                {timeLeft <= 0 ? (
                  <button
                    onClick={() => handleStopSession()}
                    className="px-6 py-2.5 rounded-lg border border-emerald-500/30 bg-emerald-950/10 hover:bg-emerald-950/30 text-xs text-emerald-400 font-bold transition-all active:scale-95 flex items-center space-x-1.5 shadow-lg shadow-emerald-500/5"
                  >
                    <Check className="w-4 h-4" />
                    <span>Finish Session & Log Stats</span>
                  </button>
                ) : (
                  sessionMode !== "very_strict" && (
                    <>
                      <button
                        onMouseDown={handleExitMouseDown}
                        onMouseUp={handleExitMouseUp}
                        onMouseLeave={handleExitMouseUp}
                        onTouchStart={handleExitMouseDown}
                        onTouchEnd={handleExitMouseUp}
                        className="px-6 py-2.5 rounded-lg border border-red-500/20 bg-red-950/5 text-xs text-red-500 font-semibold relative overflow-hidden transition-all hover:bg-red-950/20 active:scale-95"
                      >
                        <div className="absolute top-0 bottom-0 left-0 bg-red-500/10 transition-all" style={{ width: `${exitHoldProgress}%` }}></div>
                        <span className="relative z-10 flex items-center space-x-1">
                          <AlertTriangle className="w-3.5 h-3.5 text-red-500" />
                          <span>{sessionMode === "light" ? "Exit Session" : "Hold Click to Emergency Exit (10s)"}</span>
                        </span>
                      </button>
                      {showExitWarning && sessionMode !== "light" && (
                        <span className="text-[10px] text-red-400 font-mono animate-pulse">Emergency exit will mark your session interrupted and penalize score!</span>
                      )}
                    </>
                  )
                )}
              </div>
            </div>
          )}

          {/* --- SCREEN: AI ASSISTANT --- */}
          {activeTab === "ai" && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[72vh]">
              
              {/* Left sidebar: tools selection */}
              <div className="glass-panel p-6 rounded-xl border border-zinc-900 flex flex-col space-y-4 col-span-1">
                <div>
                  <h3 className="text-sm font-semibold tracking-wider text-zinc-400">STUDY AI OPTIONS</h3>
                  <p className="text-zinc-600 text-[11px] mt-0.5">Pick a specific doubt solver utility.</p>
                </div>
                
                <div className="space-y-1.5 overflow-y-auto pr-1">
                  {[
                    { id: "doubt_solver", label: "Solve Doubt", desc: "Step-by-step problem solver" },
                    { id: "concept_explainer", label: "Explain Concept", desc: "Simplified details & analogies" },
                    { id: "summarizer", label: "Summarize Topic", desc: "Structured core review notes" },
                    { id: "flashcards", label: "Generate Flashcards", desc: "Q&A high-yield flashcards" },
                    { id: "notes_generator", label: "Revision Notes", desc: "Hierarchy and outline creator" },
                    { id: "quiz_maker", label: "Create Quiz", desc: "3-question MCQ with key" },
                    { id: "formula_explainer", label: "Explain Formula", desc: "Formula variable breakdown" },
                    { id: "study_planner", label: "Study Plan", desc: "Revision schedule planner" }
                  ].map((tool) => (
                    <button
                      key={tool.id}
                      onClick={() => setAiTool(tool.id)}
                      className={`w-full text-left p-3 rounded-lg border text-xs transition-all ${
                        aiTool === tool.id
                          ? "bg-purple-950/20 border-purple-500 text-purple-400 font-semibold shadow-inner"
                          : "bg-zinc-950 border-zinc-900 text-zinc-400 hover:border-zinc-800"
                      }`}
                    >
                      <div className="font-semibold">{tool.label}</div>
                      <div className="text-[10px] opacity-75 font-normal mt-0.5">{tool.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Right panel: chat and input */}
              <div className="glass-panel p-6 rounded-xl border border-zinc-900 flex flex-col col-span-2 h-full">
                
                {/* Messages log */}
                <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2 select-text">
                  {aiChat.map((msg, idx) => (
                    <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                      <div className={`max-w-[85%] rounded-xl p-3.5 text-xs line-clamp-none ${
                        msg.role === "user"
                          ? "bg-zinc-900 text-white font-medium rounded-tr-none border border-zinc-800"
                          : msg.role === "system"
                            ? "bg-zinc-950 text-amber-400 font-mono text-[10px] border border-amber-900/20"
                            : "bg-purple-950/10 text-zinc-300 rounded-tl-none border border-purple-900/10 leading-relaxed font-sans"
                      }`}>
                        {/* Render simple markdown styling for assistant responses */}
                        <div className="space-y-1.5 whitespace-pre-wrap">
                          {msg.text}
                        </div>
                      </div>
                    </div>
                  ))}
                  {aiLoading && (
                    <div className="flex justify-start">
                      <div className="bg-purple-950/10 text-purple-400 rounded-xl rounded-tl-none p-3.5 text-xs border border-purple-900/10 flex items-center space-x-2">
                        <div className="flex space-x-1">
                          <span className="w-1.5 h-1.5 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></span>
                          <span className="w-1.5 h-1.5 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></span>
                          <span className="w-1.5 h-1.5 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></span>
                        </div>
                        <span className="font-mono text-[10px]">Study AI thinking...</span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Input Bar with Screen capture option */}
                <div className="flex space-x-2 pt-2 border-t border-zinc-950">
                  <button
                    onClick={handleTriggerScreenCapture}
                    className="px-3 rounded-lg bg-zinc-950 hover:bg-zinc-900 border border-zinc-900 hover:border-zinc-800 text-zinc-400 hover:text-white flex items-center justify-center space-x-1.5"
                    title="Capture selected area on your monitor"
                  >
                    <Monitor className="w-4.5 h-4.5" />
                    <span className="text-[10px] hidden md:inline">CAPTURE SCREEN</span>
                  </button>
                  
                  <textarea
                    placeholder="Enter doubt query or paste question here..."
                    value={aiInput}
                    onChange={(e) => setAiInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        handleQueryAI();
                      }
                    }}
                    className="flex-1 bg-zinc-950 border border-zinc-900 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-zinc-800 resize-none h-10 min-h-10 max-h-24"
                  />

                  <button
                    onClick={handleQueryAI}
                    disabled={aiLoading}
                    className="px-4 bg-purple-600 hover:bg-purple-500 text-white rounded-lg font-semibold text-xs flex items-center justify-center"
                  >
                    Send
                  </button>
                </div>
              </div>

            </div>
          )}

          {/* --- SCREEN: STUDENT TOOLS STANDALONE BROWSER --- */}
          {activeTab === "student_tools" && (
            <div className="w-full h-full flex flex-col bg-[#0b0b0f] border border-zinc-900 rounded-xl overflow-hidden shadow-2xl">
              {/* Browser Address Bar & Chrome Toolbar */}
              <div className="h-10 bg-zinc-950 border-b border-zinc-900 flex items-center justify-between px-3 select-none">
                <div className="flex items-center space-x-4 flex-1">
                  {/* Left browser controls */}
                  <div className="flex items-center space-x-2 text-zinc-650">
                    <button className="p-1 rounded text-zinc-700 cursor-not-allowed" disabled title="Go Back">◀</button>
                    <button className="p-1 rounded text-zinc-700 cursor-not-allowed" disabled title="Go Forward">▶</button>
                    <button 
                      onClick={() => {
                        const iframe = document.getElementById('student-tools-iframe') as HTMLIFrameElement;
                        if (iframe) iframe.src = iframe.src;
                        showToast("Reloaded browser window", "info");
                      }} 
                      className="p-1 rounded hover:bg-zinc-900 hover:text-zinc-300 transition-colors text-xs font-bold" 
                      title="Reload"
                    >
                      ↺
                    </button>
                  </div>
                  
                  {/* URL Box */}
                  <div className="flex-1 max-w-xl h-7 bg-zinc-900 rounded-md border border-zinc-800/80 flex items-center px-3 space-x-2 text-[10px] text-zinc-550 font-mono">
                    <span className="text-emerald-500 text-xs">🔒</span>
                    <span className="text-zinc-300 truncate">https://student-tools-seven.vercel.app</span>
                    <span className="text-[9px] bg-emerald-950/30 text-emerald-450 border border-emerald-500/20 px-1 rounded scale-90 font-sans">SECURE SANDBOX</span>
                  </div>
                </div>

                <div className="flex items-center space-x-3 text-[10px] text-zinc-550 font-mono">
                  <span className="px-1.5 py-0.5 bg-zinc-900 rounded border border-zinc-805">TAB 1/1</span>
                </div>
              </div>
              
              <iframe
                id="student-tools-iframe"
                src="https://student-tools-seven.vercel.app/"
                className="w-full flex-1 border-none bg-black"
                title="Student Tools Workspace"
              />
            </div>
          )}

          {/* --- SCREEN: DETAILED STATS --- */}
          {activeTab === "history" && (
            <div className="space-y-8">
              <div>
                <h1 className="text-2xl font-bold tracking-tight">Academic Analytics</h1>
                <p className="text-zinc-500 text-xs mt-1">Review your long-term study consistency and achievements.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                
                {/* Subject Distribution Circle Donut */}
                <div className="glass-panel p-6 rounded-xl border border-zinc-900 flex flex-col justify-between space-y-4">
                  <h3 className="text-xs font-semibold tracking-wider text-zinc-400">SUBJECT-WISE MINUTES</h3>
                  
                  {Object.keys(stats.subject_distribution).length === 0 ? (
                    <p className="text-zinc-600 text-xs text-center py-12">Log study sessions to see distribution</p>
                  ) : (
                    <div className="space-y-3">
                      {Object.entries(stats.subject_distribution).map(([subj, mins]: [string, any]) => {
                        const totalMins = Object.values(stats.subject_distribution).reduce((a: any, b: any) => a + b, 0) as number;
                        const percent = totalMins > 0 ? Math.round((mins / totalMins) * 100) : 0;
                        return (
                          <div key={subj} className="space-y-1">
                            <div className="flex justify-between text-xs font-mono">
                              <span className="text-zinc-300">{subj}</span>
                              <span className="text-zinc-500">{Math.round(mins / 60)}h ({percent}%)</span>
                            </div>
                            <div className="w-full h-1.5 bg-zinc-950 rounded-full overflow-hidden border border-zinc-900">
                              <div className={`h-full bg-blue-500`} style={{ width: `${percent}%` }}></div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* Achievements Showcase list */}
                <div className="glass-panel p-6 rounded-xl border border-zinc-900 col-span-2 space-y-4">
                  <h3 className="text-xs font-semibold tracking-wider text-zinc-400">FOCUS ACHIEVEMENTS</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-60 overflow-y-auto">
                    {stats.achievements.length === 0 ? (
                      <p className="text-zinc-600 text-xs text-center py-6 col-span-2">No achievements loaded.</p>
                    ) : (
                      stats.achievements.map((ach: any) => (
                        <div 
                          key={ach.id} 
                          className={`p-3 rounded-lg border flex items-center space-x-3 transition-colors ${
                            ach.unlocked 
                              ? "bg-purple-950/5 border-purple-900/20 text-white" 
                              : "bg-zinc-950/20 border-zinc-950/80 text-zinc-600"
                          }`}
                        >
                          <div className={`w-9 h-9 rounded-lg flex items-center justify-center border ${
                            ach.unlocked 
                              ? "bg-purple-500/10 border-purple-500/20 text-purple-400" 
                              : "bg-zinc-950 border-zinc-900 text-zinc-700"
                          }`}>
                            <Zap className="w-5.5 h-5.5" />
                          </div>
                          <div>
                            <div className="text-xs font-bold flex items-center space-x-1.5">
                              <span>{ach.title}</span>
                              {ach.unlocked && <span className="text-[8px] bg-purple-600 text-white px-1 rounded font-normal font-mono">UNLOCKED</span>}
                            </div>
                            <p className="text-[10px] text-zinc-500 leading-snug mt-0.5">{ach.description}</p>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>

              </div>

              {/* Complete log grid */}
              <div className="glass-panel p-6 rounded-xl border border-zinc-900 space-y-4">
                <h3 className="text-xs font-semibold tracking-wider text-zinc-400">COMPLETE LOGGED HISTORY</h3>
                <div className="overflow-x-auto max-h-64">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-zinc-900 text-zinc-500">
                        <th className="py-2.5">Date</th>
                        <th>Goal Description</th>
                        <th>Subject</th>
                        <th>Duration</th>
                        <th>Mode</th>
                        <th>Focus Score</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-950">
                      {stats.recent_sessions.map((s: any) => (
                        <tr key={s.id} className="hover:bg-zinc-900/10">
                          <td className="py-2.5 text-zinc-500 font-mono">{s.timestamp}</td>
                          <td className="font-medium">{s.goal}</td>
                          <td>
                            <span className={`px-2 py-0.5 rounded text-[10px] font-medium border ${getSubjectColor(s.subject)} text-white`}>
                              {s.subject}
                            </span>
                          </td>
                          <td>{s.duration_mins} mins</td>
                          <td className="capitalize text-zinc-400">{s.mode.replace("_", " ")}</td>
                          <td>
                            <span className={`font-semibold ${s.focus_score >= 80 ? "text-emerald-500" : s.focus_score >= 50 ? "text-amber-500" : "text-red-500"}`}>
                              {s.focus_score}%
                            </span>
                          </td>
                          <td>
                            <span className={`px-1.5 py-0.5 rounded text-[9px] font-mono uppercase ${
                              s.status === "completed" 
                                ? "bg-emerald-950/40 text-emerald-400 border border-emerald-900/40" 
                                : s.status === "partially_completed"
                                  ? "bg-amber-950/40 text-amber-400 border border-amber-900/40"
                                  : "bg-red-950/40 text-red-400 border border-red-900/40"
                            }`}>
                              {s.status.replace("_", " ")}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* --- SCREEN: SETTINGS --- */}
          {activeTab === "settings" && (
            <div className="max-w-2xl mx-auto glass-panel p-8 rounded-xl border border-zinc-900 space-y-6">
              <div>
                <h1 className="text-2xl font-bold tracking-tight">Console Configuration</h1>
                <p className="text-zinc-500 text-xs mt-1">Configure whitelists, themes, global hotkeys, and AI key integrations.</p>
              </div>

              <div className="space-y-6">
                {/* Opacity Settings */}
                <div className="space-y-2">
                  <div className="flex justify-between text-xs font-mono">
                    <span className="text-zinc-400">HUD Transparency</span>
                    <span className="text-white">{settings.opacity} / 255</span>
                  </div>
                  <input
                    type="range"
                    min="100"
                    max="255"
                    value={settings.opacity}
                    onChange={(e) => {
                      const newOpacity = Number(e.target.value);
                      setSettings((prev) => ({ ...prev, opacity: newOpacity }));
                      if (isWebviewReady) {
                        (window as any).pywebview.api.save_settings({ ...settings, opacity: newOpacity });
                      }
                    }}
                    className="w-full accent-purple-500 h-1 bg-zinc-950 rounded border border-zinc-900"
                  />
                </div>

                {/* Hotkeys and AI Model */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-[10px] uppercase font-mono tracking-widest text-zinc-500 block mb-1">OCR SOLVE HOTKEY</label>
                    <input
                      type="text"
                      value={settings.hotkey_solve}
                      disabled
                      className="w-full bg-zinc-950 border border-zinc-900 rounded-lg p-2.5 text-xs text-zinc-400 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] uppercase font-mono tracking-widest text-zinc-500 block mb-1">AI MODEL ENGINE</label>
                    <select
                      value={settings.online_model}
                      onChange={(e) => {
                        const newModel = e.target.value;
                        setSettings((prev) => ({ ...prev, online_model: newModel }));
                        if (isWebviewReady) {
                          (window as any).pywebview.api.save_settings({ ...settings, online_model: newModel });
                        }
                      }}
                      className="w-full bg-zinc-950 border border-zinc-900 rounded-lg p-2.5 text-xs focus:outline-none focus:border-zinc-800"
                    >
                      <option value="gpt-4o">gpt-4o (Online)</option>
                      <option value="gpt-4o-mini">gpt-4o-mini (Online)</option>
                      <option value="offline">Phi-3 (Offline GGUF)</option>
                      <option value="combined">Combined (Auto Hybrid)</option>
                    </select>
                  </div>
                </div>

                {/* Offline Custom Model Manager */}
                <div className="space-y-4 border-t border-zinc-950 pt-4">
                  <h3 className="text-xs font-semibold tracking-wider text-zinc-400 uppercase">Offline AI GGUF Models</h3>
                  <div className="bg-zinc-950 p-4 rounded-xl border border-zinc-900 space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="text-xs font-semibold text-white block">Active Model Path</span>
                        <span className="text-[10px] text-zinc-550 font-mono break-all block mt-0.5">{settings.llm_model_path || "models/Phi-3-mini-4k-instruct-q4.gguf"}</span>
                      </div>
                      <button
                        onClick={handleBrowseModel}
                        className="px-3 py-1.5 rounded bg-zinc-900 hover:bg-zinc-805 border border-zinc-850 text-[10px] text-white font-semibold transition-colors"
                      >
                        Browse GGUF
                      </button>
                    </div>

                    <div className="text-[11px] text-zinc-400 space-y-2 leading-relaxed">
                      <p className="font-semibold text-zinc-300">Download Custom GGUF Models:</p>
                      <ul className="list-disc pl-4 space-y-1">
                        <li>
                          <strong>Phi-3 Mini 3.8B (Default)</strong>: Recommended for 8GB+ RAM. (~2.2 GB)
                          <a href="https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf" target="_blank" className="text-purple-400 hover:text-purple-300 ml-1 underline">Download GGUF</a>
                        </li>
                        <li>
                          <strong>Qwen-2.5 1.5B (Low-Spec)</strong>: Recommended for 4GB-6GB RAM setups. (~900 MB)
                          <a href="https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF" target="_blank" className="text-purple-400 hover:text-purple-300 ml-1 underline">Download GGUF</a>
                        </li>
                        <li>
                          <strong>Llama-3 8B (High-Spec)</strong>: Recommended for 16GB+ RAM setups. (~4.7 GB)
                          <a href="https://huggingface.co/MaziyarPanahi/Meta-Llama-3-8B-Instruct-GGUF" target="_blank" className="text-purple-400 hover:text-purple-300 ml-1 underline">Download GGUF</a>
                        </li>
                      </ul>
                      <p className="text-[10px] text-zinc-500 italic mt-2 font-mono">Tip: You can save models anywhere on your PC and click 'Browse GGUF' to integrate them. No manual copying required!</p>
                    </div>
                  </div>
                </div>

                {/* Whitelisting details info */}
                <div className="space-y-4 border-t border-zinc-950 pt-4">
                  <h3 className="text-xs font-semibold tracking-wider text-zinc-400 uppercase">Interactive Application Whitelists</h3>
                  
                  <div className="space-y-4 text-xs text-zinc-400">
                    <div className="space-y-1">
                      <span className="font-semibold text-white block">Allowed in Strict Mode (System Core)</span>
                      <div className="flex flex-wrap gap-1.5">
                        {settings.strict_allowed_apps?.map((app) => (
                          <span key={app} className="px-2 py-0.5 bg-zinc-950 rounded border border-zinc-900 font-mono text-[10px]">{app}</span>
                        ))}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <span className="font-semibold text-white block">Allowed Applications in Moderate Mode</span>
                      <div className="flex flex-wrap gap-1.5 mb-2">
                        {settings.moderate_allowed_apps?.map((app) => (
                          <span key={app} className="inline-flex items-center space-x-1 px-2 py-0.5 bg-zinc-950 rounded border border-zinc-900 font-mono text-[10px]">
                            <span>{app}</span>
                            <button
                              onClick={() => handleDeleteApp(app)}
                              className="text-zinc-500 hover:text-red-400 font-bold ml-1 transition-colors"
                            >
                              ✕
                            </button>
                          </span>
                        ))}
                        {(!settings.moderate_allowed_apps || settings.moderate_allowed_apps.length === 0) && (
                          <span className="text-zinc-600 italic">No custom apps allowed. Add one below.</span>
                        )}
                      </div>
                      
                      <div className="flex space-x-2">
                        <input
                          type="text"
                          placeholder="e.g. Code.exe, Notion.exe"
                          value={newAppInput}
                          onChange={(e) => setNewAppInput(e.target.value)}
                          onKeyDown={(e) => e.key === "Enter" && handleAddApp()}
                          className="flex-1 bg-zinc-950 border border-zinc-900 rounded-lg px-3 py-1.5 text-xs text-[#f5f5f7] focus:outline-none focus:border-zinc-800"
                        />
                        <button
                          onClick={handleAddApp}
                          className="px-3 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-white font-medium"
                        >
                          Add App
                        </button>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <span className="font-semibold text-white block">Whitelisted Domains in Moderate Mode</span>
                      <div className="flex flex-wrap gap-1.5 mb-2">
                        {settings.moderate_allowed_websites?.map((site) => (
                          <span key={site} className="inline-flex items-center space-x-1 px-2 py-0.5 bg-blue-950/20 text-blue-400 rounded border border-blue-950 font-mono text-[10px]">
                            <span>{site}</span>
                            <button
                              onClick={() => handleDeleteSite(site)}
                              className="text-blue-500 hover:text-red-400 font-bold ml-1 transition-colors"
                            >
                              ✕
                            </button>
                          </span>
                        ))}
                        {(!settings.moderate_allowed_websites || settings.moderate_allowed_websites.length === 0) && (
                          <span className="text-zinc-600 italic">No custom domains whitelisted. Add one below.</span>
                        )}
                      </div>

                      <div className="flex space-x-2">
                        <input
                          type="text"
                          placeholder="e.g. physicswallah.com, unacademy.com"
                          value={newSiteInput}
                          onChange={(e) => setNewSiteInput(e.target.value)}
                          onKeyDown={(e) => e.key === "Enter" && handleAddSite()}
                          className="flex-1 bg-zinc-950 border border-zinc-900 rounded-lg px-3 py-1.5 text-xs text-[#f5f5f7] focus:outline-none focus:border-zinc-800"
                        />
                        <button
                          onClick={handleAddSite}
                          className="px-3 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-white font-medium"
                        >
                          Add Site
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

            </div> {/* Closes Window Body Container */}
          </motion.div>
        </div>
      )}

      {/* macOS-style floating dock at the bottom */}
      <div className="absolute bottom-4 left-0 right-0 z-45 flex justify-center pointer-events-none">
        <div className="glass-panel px-6 py-2.5 rounded-2xl border border-zinc-800/40 bg-zinc-950 shadow-xl flex items-end space-x-4 pointer-events-auto transition-all duration-300 border-zinc-900/60">
          {[
            { id: "session_setup", label: "Focus Timer", icon: Clock, color: "bg-blue-600/30 text-blue-400 border-blue-500/20" },
            { id: "ai", label: "AI Assistant", icon: Sparkles, color: "bg-purple-600/30 text-purple-400 border-purple-500/20" },
            { id: "student_tools", label: "Student Tools", icon: BookOpen, color: "bg-emerald-600/30 text-emerald-450 border-emerald-500/20" },
            { id: "history", label: "Analytics", icon: BarChart2, color: "bg-amber-600/30 text-amber-400 border-amber-500/20" },
            { id: "settings", label: "Settings", icon: Settings, color: "bg-zinc-700/30 text-zinc-400 border-zinc-700/20" }
          ].map((app) => {
            const Icon = app.icon;
            const isActive = activeTab === app.id;
            return (
              <button
                key={app.id}
                onClick={() => setActiveTab(app.id)}
                className="group relative flex flex-col items-center transition-all duration-300"
              >
                {/* Tooltip */}
                <span className="absolute bottom-16 opacity-0 group-hover:opacity-100 transition-opacity bg-zinc-950 border border-zinc-805 text-[10px] text-zinc-300 px-2.5 py-1 rounded-md font-mono pointer-events-none whitespace-nowrap shadow-lg">
                  {app.label}
                </span>
                
                {/* Dock Icon Container */}
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center border transition-all duration-300 transform group-hover:-translate-y-2 group-hover:scale-110 active:scale-95 ${
                  isActive 
                    ? "bg-white/10 text-white border-white/20 shadow-md shadow-white/5"
                    : `bg-zinc-950/80 border-zinc-900/60 text-zinc-450 hover:text-white ${app.color}`
                }`}>
                  <Icon className="w-5.5 h-5.5" />
                </div>
                
                {/* Active Indicator dot */}
                {isActive && (
                  <span className="w-1 h-1 bg-white rounded-full mt-1.5 animate-pulse"></span>
                )}
              </button>
            );
          })}
          
          <div className="h-10 w-[1px] bg-zinc-900/60 mx-2 self-center"></div>
          
          {/* Quick exit shortcut */}
          <button
            onClick={handleClose}
            className="group relative flex flex-col items-center transition-all duration-300 pointer-events-auto"
            title="Quit FocusFlow Application"
          >
            <span className="absolute bottom-16 opacity-0 group-hover:opacity-100 transition-opacity bg-red-950 border border-red-900 text-[10px] text-red-400 px-2.5 py-1 rounded-md font-mono pointer-events-none whitespace-nowrap shadow-lg">
              Quit FocusFlow
            </span>
            <div className="w-12 h-12 rounded-xl bg-red-950/30 border border-red-900/20 text-red-500 hover:text-red-400 flex items-center justify-center transition-all duration-300 transform group-hover:-translate-y-2 group-hover:scale-110 active:scale-95">
              <LogOut className="w-5.5 h-5.5" />
            </div>
          </button>
        </div>
      </div>

      {/* Toast Notification Container */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: -50, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 0.95 }}
            className={`fixed top-12 left-1/2 -translate-x-1/2 z-[100] px-4 py-3 rounded-lg border shadow-xl flex items-center space-x-2.5 font-sans text-xs ${
              toast.type === "success"
                ? "bg-emerald-950 border-emerald-500/30 text-emerald-450"
                : toast.type === "error"
                  ? "bg-red-950 border-red-500/30 text-red-450"
                  : toast.type === "warning"
                    ? "bg-amber-950 border-amber-500/30 text-amber-450"
                    : "bg-zinc-900 border-zinc-800 text-zinc-300"
            }`}
          >
            {toast.type === "success" && <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />}
            {toast.type === "error" && <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0" />}
            {toast.type === "warning" && <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />}
            {toast.type === "info" && <Compass className="w-4 h-4 text-blue-400 flex-shrink-0 animate-spin" />}
            <span>{toast.message}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Early Exit Confirmation Modal */}
      <AnimatePresence>
        {showExitConfirm && (
          <div className="fixed inset-0 bg-black/90 backdrop-blur-md z-[110] flex items-center justify-center p-4">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="w-full max-w-md bg-zinc-950 border border-zinc-900 rounded-2xl p-6 space-y-6 shadow-2xl"
            >
              <div className="space-y-2">
                <h3 className="text-sm font-mono tracking-widest text-red-500 uppercase font-bold">WARNING: Early Exit Attempted</h3>
                <p className="text-zinc-300 text-xs leading-relaxed">
                  You are stopping the focus session before completing your target time. Did you complete your study goal?
                </p>
                <div className="bg-zinc-900/50 border border-zinc-900 p-2.5 rounded-lg text-[10px] text-zinc-500 font-mono italic">
                  "{sessionGoal}"
                </div>
              </div>

              <div className="flex flex-col space-y-2.5">
                <button
                  onClick={() => handleStopSession("completed")}
                  className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold font-sans transition-all active:scale-95 shadow-md shadow-emerald-500/10"
                >
                  Yes, Goal Completed Successfully
                </button>
                <button
                  onClick={() => handleStopSession("partially_completed")}
                  className="w-full py-2 bg-amber-600/10 border border-amber-500/20 text-amber-400 hover:bg-amber-955/20 rounded-lg text-xs font-semibold font-sans transition-all active:scale-95"
                >
                  Partially Completed
                </button>
                <button
                  onClick={() => handleStopSession("interrupted")}
                  className="w-full py-2 bg-red-950/20 border border-red-500/20 text-[#ef4444] hover:bg-red-950/40 rounded-lg text-xs font-semibold font-sans transition-all active:scale-95"
                >
                  No, Aborted (Score Penalty Applied)
                </button>
                <button
                  onClick={handleCancelExit}
                  className="w-full py-2 bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-white rounded-lg text-xs font-medium font-mono transition-all"
                >
                  Cancel & Resume Study
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
