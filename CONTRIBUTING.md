# Contributing to FocusFlow 🪐

First off, thank you for considering contributing to FocusFlow! We want to keep this utility robust, highly stealthy, and highly optimized.

---

## 🛠️ Development Guidelines

1. **Coding Style**:
   - Write clean, documented Python code matching PEP 8 formatting.
   - Use type hints wherever applicable.

2. **Windows Compatibility & Evasion**:
   - Never introduce modules or dependencies that spawn console windows on Windows (always run subprocesses with `subprocess.CREATE_NO_WINDOW` flags).
   - Ensure screen-capture guard logic (`guard.py`) is verified using ctypes on Windows 10/11.

3. **Performance Optimization**:
   - Keep Tkinter UI changes on the main loop thread utilizing `root.after(0, callback)` delegates.
   - Avoid creating massive memory bottlenecks so it runs comfortably on low-RAM machines.

---

## 🧪 Testing

Before submitting a pull request, run the integration test suite:
```powershell
python test_system.py
```
Ensure all tests finish with a `SUCCESS` status code and that the OCREngine correctly resolves and processes sample content.

---

## 🚀 Submitting Changes

1. Fork the repository and create your feature branch:
   `git checkout -b feature/amazing-feature`
2. Commit your changes with descriptive messages:
   `git commit -m "Add dynamic API health polling threshold"`
3. Push to your branch:
   `git push origin feature/amazing-feature`
4. Open a Pull Request for review.
