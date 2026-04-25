const { app, BrowserWindow } = require('electron');
const { exec } = require('child_process');
const path = require('path');

let mainWindow;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            nodeIntegration: false
        }
    });

    // ⏳ wait for backend to start
    setTimeout(() => {
        mainWindow.loadURL('http://127.0.0.1:5000');
    }, 3000);
}

app.whenReady().then(() => {

    // 🔥 RUN YOUR EXE
    const backendPath = path.join(__dirname, '../backend/dist/app.exe');

    exec(`"${backendPath}"`, (err) => {
        if (err) console.log("Backend error:", err);
    });

    createWindow();
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
});