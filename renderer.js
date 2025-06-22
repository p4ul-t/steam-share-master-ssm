let steamPath = '';

const blockBtn = document.getElementById('block-btn');
const unblockBtn = document.getElementById('unblock-btn');
const selectPathBtn = document.getElementById('select-path-btn');
const pathLabel = document.getElementById('path-label');
const logDisplay = document.getElementById('log-display');

window.electronAPI.getInitialPath().then(path => {
    steamPath = path;
    pathLabel.textContent = `Actual path: ${path}`;
});

blockBtn.addEventListener('click', () => {
    window.electronAPI.blockSteam(steamPath);
});

unblockBtn.addEventListener('click', () => {
    window.electronAPI.unblockSteam(steamPath);
});

selectPathBtn.addEventListener('click', async () => {
    const newPath = await window.electronAPI.selectSteamPath();
    if (newPath) {
        steamPath = newPath;
        pathLabel.textContent = `Actual path: ${newPath}`;
    }
});

window.electronAPI.onCommandLog((message) => {
    const unwantedMessages = [
        "SUCCESS: The process \"steam.exe\" with PID",
        "SUCCESS: The process \"steamwebhelper.exe\" with PID",
        "SUCCESS: The process \"steamservice.exe\" with PID",
        "Ok.",
        "Updated 1 rule(s) on policy",
        "No rules matched the specified criteria." 
    ];


    if (unwantedMessages.some(unwanted => message.includes(unwanted))) {
        return;
    }

    const currentText = logDisplay.innerHTML;
    const newText = currentText + message.replace(/\n/g, '<br>') + '<br>';

    let lines = newText.split('<br>');
    

    if (lines.length > 5) {
        lines = lines.slice(-5);
    }
    
    logDisplay.innerHTML = lines.join('<br>');
    logDisplay.scrollTop = logDisplay.scrollHeight; 
});