const { app, BrowserWindow, ipcMain, dialog, Tray, Menu, nativeImage } = require('electron');
const path = require('path');
const fs = require('fs');
const { exec } = require('child_process');

let mainWindow;
let tray = null;
const steamPathFile = path.join(app.getPath('userData'), 'steam_path.txt');
app.isQuitting = false;

function getSteamPath() {
    if (fs.existsSync(steamPathFile)) {
        return fs.readFileSync(steamPathFile, 'utf-8').trim();
    }
    return "C:\\Program Files (x86)\\Steam\\Steam.exe";
}

function sendLog(message) {
    if (mainWindow) {
        mainWindow.webContents.send('command-log', message);
    }
}

function executeBlockSteam() {
    const steamPath = getSteamPath();
    sendLog('Blocking Steam...');
    const commands = [
        'taskkill /F /IM "steam.exe" /IM "steamwebhelper.exe" /IM "steamservice.exe"',
        `netsh advfirewall firewall add rule name="BlockSteam" dir=out action=block program="${steamPath}" enable=yes`
    ];
    
    exec(commands[0], () => {
        setTimeout(() => {
            exec(commands[1], () => {
                sendLog("Steam blocked.");
                setTimeout(() => relaunchSteam(steamPath), 1000);
            });
        }, 2000);
    });
}

function executeUnblockSteam() {
    const steamPath = getSteamPath();
    sendLog('Unblocking Steam...');
    const command = 'netsh advfirewall firewall set rule name="BlockSteam" new enable=no';
    
    exec(command, () => {
        setTimeout(() => {
            sendLog('Steam unblocked.');
            relaunchSteam(steamPath);
        }, 1000);
    });
}

function relaunchSteam(steamPath) {
    sendLog("Closing and restarting Steam...");
    const killCommand = 'taskkill /F /IM "steam.exe" /IM "steamwebhelper.exe" /IM "steamservice.exe"';
    const startCommand = `start "" "${steamPath}"`;

    exec(killCommand, () => {

        setTimeout(() => {
            exec(startCommand);
        }, 3000);
    });
}

function createTray() {
    const icon = nativeImage.createFromPath(path.join(__dirname, 'assets/SSM-logo-png.ico'));
    tray = new Tray(icon);
    tray.setToolTip('Steam Share Master');

    const contextMenu = Menu.buildFromTemplate([
        {
            label: 'Show SSM',
            click: () => {
                mainWindow.show();
            }
        },
        { type: 'separator' },
        {
            label: 'Block Steam',
            click: () => {
                executeBlockSteam();
            }
        },
        {
            label: 'Unblock Steam',
            click: () => {
                executeUnblockSteam();
            }
        },
        { type: 'separator' },
        {
            label: 'Run at startup',
            type: 'checkbox',
            checked: app.getLoginItemSettings().openAtLogin,
            click: () => {
                const settings = app.getLoginItemSettings();
                app.setLoginItemSettings({
                    openAtLogin: !settings.openAtLogin,
                    path: app.getPath('exe')
                });
            }
        },
        { type: 'separator' },
        {
            label: 'Close',
            click: () => {
                app.isQuitting = true;
                app.quit();
            }
        },
        {
            label: 'Help',
            click: () => {
                const { shell } = require('electron');
                shell.openExternal('https://github.com/p4ul-t/steam-share-master-ssm/blob/main/find-Steam.exe.md');
            }
        },        
    ]);

    tray.setContextMenu(contextMenu);

    tray.on('click', () => {
        mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show();
    });
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 380,
        height: 400,
        resizable: false,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false
        },
        icon: path.join(__dirname, 'assets/SSM-logo-png.ico'),
        title: "Steam Share Master - SSM"
    });

    mainWindow.setMenuBarVisibility(false);
    mainWindow.loadFile('index.html');

    mainWindow.on('close', (event) => {
        if (!app.isQuitting) {
            event.preventDefault();
            mainWindow.hide();
        }
    });
}

app.whenReady().then(() => {
    createWindow();
    createTray();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        } else {
            mainWindow.show();
        }
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
    }
});

ipcMain.handle('get-initial-path', () => {
    return getSteamPath();
});

ipcMain.handle('select-steam-path', async () => {
    const result = await dialog.showOpenDialog(mainWindow, {
        properties: ['openFile'],
        title: 'Sélectionner Steam.exe',
        defaultPath: 'C:\\',
        filters: [{ name: 'Fichiers EXE', extensions: ['exe'] }]
    });

    if (!result.canceled && result.filePaths.length > 0) {
        const newPath = result.filePaths[0];
        fs.writeFileSync(steamPathFile, newPath);
        return newPath;
    }
    return null;
});

ipcMain.on('block-steam', () => {
    executeBlockSteam();
});

ipcMain.on('unblock-steam', () => {
    executeUnblockSteam();
});
