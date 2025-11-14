var ws = new WebSocket("ws://localhost:8000/activity");

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
    const height = parseInt(document.getElementById("grid-height").value, 10);
    const width = parseInt(document.getElementById("grid-width").value, 10);
    const conversion = parseInt(document.getElementById("grid-conversion").value, 10);
    const networkType = document.getElementById("network-type").value;

    // Rudimentary input sanity checks
    if (isNaN(height) || isNaN(width) || isNaN(conversion) || height <= 0 || width <= 0 || conversion <= 0) {
        alert("Please enter valid positive numbers for grid size.");
        return;
    }

    resizeCanvas(height, width);
    await initSimulation(height, width, conversion, networkType);
});

// Resize canvas based on configuration form
function resizeCanvas(height, width) {
    const canvas = document.getElementById("simulation");

    canvas.width = width;
    canvas.height = height;
    canvas.style.width = width + "px";
    canvas.style.height = height + "px";
}

// Let backend know about simulation configuration
async function initSimulation(height, width, conversion, networkType) {
    console.log(height, width, conversion, networkType);

    try {
        const response = await fetch('/init/simulation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify ({
                height: height,
                width: width,
                conversion: conversion,
                network_type: networkType,
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
