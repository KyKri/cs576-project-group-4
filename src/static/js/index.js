var packets = new WebSocket("ws://localhost:8000/packet_transfer");
var logCount = 0;
var UEList = [];
var BSList = [];
var checkInterval; //for running asynchronous function that periodically checks for ue link status
var simulationRunning = false;

async function logMessage(message){
    const logBox = document.getElementById('logs');
    const newLog = document.createElement('p');
    newLog.textContent = `${logCount}: ${message}`;
    logBox.appendChild(newLog);
    logBox.scrollTop = logBox.scrollHeight;
    logCount ++;
}

function parsePacketLog(message){
    const regex = /^(.+?) -> (.+?): (\d+) bytes$/;
    const match = message.match(regex);
    if(!match){return;}

    return {
        src: match[1], //source IP
        dst: match[2], //destination IP
        length: Number(match[3]) //packet length in bytes
    }
}

packets.onmessage = function(event) {
    //console.log(event.data);
    logMessage(event.data);
};

function addBaseStation(){
    const newBaseStation = document.createElement('span');
    newBaseStation.classList.add('font-awesome-icon','fas','fa-solid','fa-tower-cell');
    newBaseStation.addEventListener('mousedown', startDrag);
    newBaseStation.addEventListener('click', selectDevice);
    document.getElementById('icon-tray').appendChild(newBaseStation);

    return newBaseStation;
}
function addUserEquipment(){
    const newUserEquipment = document.createElement('span');
    newUserEquipment.classList.add('font-awesome-icon','fas','fa-solid','fa-mobile');
    newUserEquipment.addEventListener('mousedown', startDrag);
    newUserEquipment.addEventListener('click', selectDevice);
    document.getElementById('icon-tray').appendChild(newUserEquipment);

    return newUserEquipment;
}

function extractIDNumber(deviceId){
    const splitId = deviceId.split("_", 2);
    const deviceType = splitId[0];
    const id = parseInt(splitId[1]);
    return { deviceType, id };
}

// Hanlde simulation controls
async function control(action) {
    const form = document.getElementById("configuration");
    const controls = document.getElementById("controls");
    const inputs = form.querySelectorAll("input, select, button");

    //this should only execute on the first instance of clicking 'start'
    if (action === "start" && !simulationRunning){
        await initSimulation();
        simulationRunning = true;
        controls.innerHTML = `
            <button onclick="event.preventDefault(); control()">
                <i class="fas fa-pause"></i> Pause Simulation
            </button>`
        if (!checkInterval){
            checkInterval = setInterval(simulationStatus, 500);
        }
    }
    else{
        try {
            const response = await fetch('/control/pause', {
                method: 'POST'
            });

            if (!response.ok) {
                console.warn('Network response was not ok ' + response.statusText);
            }
            else {
                const data = await response.json();
                console.log(data);
                simulationRunning = !data.paused;
            }
        } catch (error) {console.error(error);}
    }


    if(simulationRunning){
        controls.innerHTML = `
            <button onclick="event.preventDefault(); control()">
                <i class="fas fa-pause"></i> Pause Simulation
            </button>`
        // Prevent changing configuration during running simulation
        inputs.forEach(el => el.disabled = true);
        if (!checkInterval){
            checkInterval = setInterval(simulationStatus, 1000);
        }
    }else{
        controls.innerHTML = `
            <button onclick="event.preventDefault(); control()">
                <i class="fas fa-play"></i> Unpause Simulation
            </button>`
        inputs.forEach(el => el.disabled = false);
        clearInterval(checkInterval);
        checkInterval = null;
    }
}

// Handle simulation configuration
document.getElementById("configuration").addEventListener("submit", async function(event) {
    event.preventDefault();
    const height = parseFloat(document.getElementById("grid-height").value);
    const width = parseFloat(document.getElementById("grid-width").value);
    //const pixelsPerMeter = parseFloat(document.getElementById("grid-ppm").value);
    const networkType = document.getElementById("network-type").value;
    // Rudimentary input sanity checks
    if (isNaN(height) || isNaN(width) || height <= 0 || width <= 0) {
        alert("Please enter valid positive numbers for grid size.");
        return;
    }
    //reconfigure simulation
    try{
        const response = await fetch('/configure', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ 
                height: height, width: width, pixels_per_meter: 1,
                network_type: networkType,
                starting_ip: '10.0.0.1'
            }) //all other values are defaults because they do not affect the configure function
        });
        if (!response.ok) {console.warn('Network response was not ok ' + response.statusText);}
        else {
            const data = await response.json();
            logMessage(data.message);
        }
    } catch (error) {
        console.error(error);
    }

    resizeCanvas(height, width);
});

// Resize canvas based on configuration form
function resizeCanvas(height, width) {
    const canvas = document.getElementById("simulation");

    canvas.width = width;
    canvas.height = height;
    canvas.style.width = width + "px";
    canvas.style.height = height + "px";

    updateCanvas();
}

// Let backend know about simulation configuration
async function initSimulation() {
    try {
        const response = await fetch('/init/simulation', {
            method: 'POST'
        });

        if (!response.ok) {console.warn('Network response was not ok ' + response.statusText);}
        else {
            const data = await response.json();
            console.log(data);
        }

    } catch (error) {
        console.error(error);
    }
}
