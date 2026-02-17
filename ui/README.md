# 🌌 HEIFI Neural Interface: Matrix v3

HEIFI is a high-fidelity, enterprise-grade command center that bridges Large Language Models with infrastructure orchestration. Designed for the "Power Operator," it offers a unified interface for AI reasoning and autonomous SSH workflows.

![HEIFI Interface](https://img.shields.io/badge/HEIFI-Neural_Interface-white?style=for-the-badge&logo=google-gemini)

## 🎨 Design Language & Theming

The **HEIFI Matrix v3** aesthetic is built on a "Premium Industrial" design language, prioritizing high-density information without visual clutter.

### Color Palette
- **Obsidian Backbone**: `#000000` (Pure Black) for maximum contrast and OLED optimization.
- **Neural Accents**: `#1d9bf0` (Grok Blue) for primary interactive elements and active neural links.
- **Semantic Feedback**:
  - `Success`: `#10b981` (Emerald) for successful handshakes and stable links.
  - `Error`: `#ef4444` (Rose Red) for critical faults and security breaches.
- **Typography**: 
  - `Sans`: **Inter** for clean, readable UI labels.
  - `Mono`: **Geist Mono** for code, terminal streams, and low-level logical identifiers.

### Visual Effects
- **Glassmorphism 2.0**: Uses deep `backdrop-blur(45px)` combined with low-opacity backgrounds (`rgba(10, 10, 10, 0.15)`) to create a sense of depth and focus.
- **Ambient Mesh**: A fixed radial gradient system (`radial-gradient`) simulates an ambient glow emanating from the corners of the interface, reducing eye strain in dark environments.
- **Glow-Pulse Feedback**: Interactive cards use a custom `glowPulse` animation that shifts border-color and box-shadow based on system state.

## 🚀 Core Technology Stack

### Intelligence Layer
- **Google Gemini 3 API**: Specifically **Gemini 3 Pro Preview** for its superior tool-calling accuracy and **Gemini 2.5 Flash** for high-speed advisory tasks.
- **Thinking Budget**: Leverages the model's reasoning tokens (up to 32k) for "Deep Mode" architectural planning.
- **Local Neural Bridge**: Native integration for **Ollama** and **LM Studio** via a custom local proxy.

### Orchestration & Communication
- **Real-time Streams**: **Socket.io** handles the low-latency duplex stream between the browser and remote SSH targets.
- **SSH Logic**: Powered by the **ssh2** library on the backend, supporting RSA/Ed25519 keys and password-based auth.
- **Terminal UI**: **Xterm.js** with `FitAddon` and `WebLinksAddon` for a native-feeling TTY experience.

### Frontend Architecture
- **React 19**: Utilizing the latest concurrent rendering features.
- **Tailwind CSS**: Custom configuration extending Grok-style spacing and animations.
- **React Virtuoso**: High-performance virtualization for infinite chat history and agent reasoning logs.
- **Lucide Icons**: Feather-weight vector iconography for clear operational signals.

## 🏗️ Architectural Breakdown

### 1. The Autonomous Loop
When in **Agent Mode**, HEIFI enters a recursive reasoning loop:
1. **Perception**: The model analyzes the user's objective and current file system state.
2. **Planning**: It emits `functionCall` objects (e.g., `list_dir`, `read_file`).
3. **Validation**: The UI presents these actions to the operator (Human-in-the-Loop).
4. **Execution**: The backend executes the command via the established SSH socket.
5. **Synthesis**: The output is fed back into the model to refine the next step.

### 2. Security Enclave
- **Zero-Knowledge Auth**: Credentials (SSH keys/passwords) are held in ephemeral memory and never persisted to a database.
- **RSA-4096 Encryption**: All device-flow links (GitHub/Copilot) use standard OAuth 2.0 security protocols.
- **Termination Purge**: Clicking "Terminate Node" triggers a complete memory sweep of the socket session on the backend.

## 🛠️ Operational Commands

| Command | Description |
| :--- | :--- |
| `npm run dev` | Initialize local neural hub and next.js server. |
| `npm run build` | Compile the matrix for production deployment. |
| `docker-compose up` | Launch the fully containerized HEIFI stack. |

---
*HEIFI: The thin layer between human intent and machine execution.*