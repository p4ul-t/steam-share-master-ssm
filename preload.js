const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    getInitialPath: () => ipcRenderer.invoke('get-initial-path'),
    selectSteamPath: () => ipcRenderer.invoke('select-steam-path'),
    blockSteam: (path) => ipcRenderer.send('block-steam', path),
    unblockSteam: (path) => ipcRenderer.send('unblock-steam', path),
    onCommandLog: (callback) => ipcRenderer.on('command-log', (event, ...args) => callback(...args))
});