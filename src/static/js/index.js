var ws = new WebSocket("ws://localhost:8000/activity");
var UEList = [];
var BSList = [];

ws.onmessage = function(event) {
    var messages = document.getElementById('messages');
    var message = document.createElement('li');
    var content = document.createTextNode(event.data);
    message.appendChild(content);
    messages.appendChild(message);
};

function sendMessage(event) {
    var input = document.getElementById("messageText");
    ws.send(input.value);
    input.value = '';
    event.preventDefault();
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
    const inputs = form.querySelectorAll("input, select, button");

    // Prevent changing configuration during running simulation
    if (action === "start" || action === "pause") {
        inputs.forEach(el => el.disabled = true);
        console.log(`${action} clicked — form disabled`);
    } else if (action === "stop") {
        inputs.forEach(el => el.disabled = false);
        console.log("stop clicked — form enabled");
    }

    try {
        const response = await fetch('/control/' + action, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            console.warn('Network response was not ok ' + response.statusText);
        }
        else {
            const data = await response.json();
            console.log(data);
        }

    } catch (error) {
        console.error(error);
    }
}

// Handle simulation configuration
document.getElementById("configuration").addEventListener("submit", async function(event) {
    event.preventDefault();
    const height = parseFloat(document.getElementById("grid-height").value);
    const width = parseFloat(document.getElementById("grid-width").value);
    const pixelsPerMeter = parseFloat(document.getElementById("grid-ppm").value);
    const networkType = document.getElementById("network-type").value;
    const startingIP = document.getElementById("starting-ip").value;

    // Rudimentary input sanity checks
    if (isNaN(height) || isNaN(width) || isNaN(pixelsPerMeter) || height <= 0 || width <= 0 || pixelsPerMeter <= 0) {
        alert("Please enter valid positive numbers for grid size.");
        return;
    }

    let startingIPList = startingIP.split(".");
    let startingIPValid = true;
    
    if (startingIPList.length !== 4) {
        startingIPValid = false
    }

    for (let octet of startingIPList) {
        octet = parseInt(octet, 10);

        if (isNaN(octet) || octet > 255 || octet < 0) {
            startingIPValid = false
        }
    }

    if (startingIPValid !== true) {
        alert("Please enter a valid IPv4 address");
        return;
    }

    resizeCanvas(height, width);
    await initSimulation(height, width, pixelsPerMeter, networkType, startingIP);
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
async function initSimulation(height, width, pixelsPerMeter, networkType, startingIP) {
    console.log(height, width, pixelsPerMeter, networkType, startingIP);

    try {
        const response = await fetch('/init/simulation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify ({
                height: height,
                width: width,
                pixels_per_meter: pixelsPerMeter,
                network_type: networkType,
                starting_ip: startingIP,
            })
        });

        if (!response.ok) {
            console.warn('Network response was not ok ' + response.statusText);
        }
        else {
            const data = await response.json();
            console.log(data);
        }

    } catch (error) {
        console.error(error);
    }
}
