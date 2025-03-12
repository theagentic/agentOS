const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

function detectPythonEnv() {
  return new Promise((resolve, reject) => {
    const pythonScript = path.join(__dirname, 'get_venv.py');
    const python = spawn('python', [pythonScript]);
    
    let data = '';
    
    python.stdout.on('data', (chunk) => {
      data += chunk;
    });
    
    python.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(`Process exited with code ${code}`));
        return;
      }
      
      try {
        const venvInfo = JSON.parse(data);
        process.env.PYTHON_PATH = venvInfo.executable;
        resolve(venvInfo);
      } catch (err) {
        reject(err);
      }
    });
  });
}

// Run the detection
detectPythonEnv()
  .then((info) => {
    console.log('Python environment detected:', info);
    process.exit(0);
  })
  .catch((err) => {
    console.error('Failed to detect Python environment:', err);
    process.exit(1);
  });
