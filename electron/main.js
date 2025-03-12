const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { PythonShell } = require('python-shell');
const log = require('electron-log');
const fetch = (...args) => import('node-fetch').then(({default: fetch}) => fetch(...args));

// Global state
let pythonProcess = null;
let mainWindow = null;
let backendReady = false;

// Configure logging
log.transports.file.level = 'info';
log.info('Starting AgentOS...');

// Add these utility functions
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function checkBackendHealth() {
    try {
        log.info('Checking backend health at http://127.0.0.1:5000/health');
        const response = await fetch('http://127.0.0.1:5000/health', {
            method: 'GET',
            headers: { 'Accept': 'application/json' }
        });
        
        if (response.ok) {
            const data = await response.json();
            log.info(`Health check successful: ${JSON.stringify(data)}`);
            return true;
        }
        log.error(`Health check failed with status: ${response.status}`);
        return false;
    } catch (error) {
        log.error(`Health check error: ${error.message}`);
        return false;
    }
}

async function waitForBackend(attempts = 5) {  // Reduced from 45
    for (let i = 0; i < attempts; i++) {
        try {
            const isHealthy = await checkBackendHealth();
            if (isHealthy) {
                log.info('Backend is ready');
                return true;
            }
            log.info(`Backend not ready (attempt ${i + 1}/${attempts})`);
            
            // Use a longer delay between attempts
            await new Promise(resolve => setTimeout(resolve, 4000));
        } catch (error) {
            log.error(`Health check error: ${error.message}`);
        }
    }
    throw new Error('Backend failed to respond to health check');
}

async function startPythonBackend() {
    try {
        // Check existing backend
        if (await checkBackendHealth()) {
            log.info('Backend already running');
            return true;
        }

        const pythonPath = process.env.VIRTUAL_ENV ? 
            path.join(process.env.VIRTUAL_ENV, 'Scripts', 'python.exe') : 
            'python';

        // Start Python process
        pythonProcess = new PythonShell('bridge.py', {
            mode: 'text',
            pythonPath,
            pythonOptions: ['-u'],
            scriptPath: path.join(__dirname, '..', 'python')
        });

        pythonProcess.on('message', msg => log.info('Python:', msg));
        pythonProcess.on('stderr', err => log.info('Python:', err));
        pythonProcess.on('error', err => log.error('Python Error:', err));

        // Add a longer wait time
        log.info('Waiting for Flask server to initialize (5 seconds)...');
        await new Promise(resolve => setTimeout(resolve, 5000)); // Increased to 5 seconds

        // Now wait for backend to be ready
        return await waitForBackend();
    } catch (error) {
        log.error('Failed to start backend:', error);
        throw error;
    }
}

function createWindow() {
    if (mainWindow) return;

    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        }
    });

    mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));
    
    if (process.env.NODE_ENV === 'development') {
        mainWindow.webContents.openDevTools();
    }

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

// App initialization
app.whenReady().then(async () => {
    try {
        log.info('Starting application...');
        
        // First start the backend
        await startPythonBackend();
        log.info('Backend started successfully');
        
        // Then create the window
        createWindow();
        log.info('Window created successfully');
        
    } catch (error) {
        log.error(`Startup failed: ${error.message}`);
        
        dialog.showErrorBox(
            'AgentOS Startup Error',
            `Failed to start the application: ${error.message}\n\n` +
            'Please check if another process is using port 5000.'
        );
        
        app.quit();
    }
});

// Quit when all windows are closed, except on macOS
app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});

// Clean shutdown
app.on('will-quit', async (event) => {
    if (pythonProcess) {
        event.preventDefault();
        try {
            if (backendReady) {
                await fetch('http://127.0.0.1:5000/shutdown', { method: 'POST' });
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
            pythonProcess.kill();
        } catch (error) {
            log.error('Shutdown error:', error);
        } finally {
            app.exit();
        }
    }
});

// IPC handlers for communication with renderer
ipcMain.handle('send-command', async (event, command) => {
  log.info('Sending command to Python:', command);
  try {
    // In a real implementation, would send via HTTP to the Python bridge
    const response = await fetch('http://127.0.0.1:5000/health', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command })
    }).then(res => res.json());
    
    return response;
  } catch (error) {
    log.error('Error sending command:', error);
    return { error: error.toString() };
  }
});
