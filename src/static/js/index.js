var ws = new WebSocket("ws://localhost:8000/activity");

ws.onmessage = function(event) {
    var messages = document.getElementById('messages')
    var message = document.createElement('li')
    var content = document.createTextNode(event.data)
    message.appendChild(content)
    messages.appendChild(message)
};

function sendMessage(event) {
    var input = document.getElementById("messageText")
    ws.send(input.value)
    input.value = ''
    event.preventDefault()
};

function addBaseStation(){
    const newBaseStation = document.createElement('span');
    newBaseStation.classList.add('font-awesome-icon','fas','fa-solid','fa-tower-cell');
    newBaseStation.addEventListener('mousedown', startDrag);
    newBaseStation.addEventListener('click', selectDevice);
    document.getElementById('icon-tray').appendChild(newBaseStation);
    return newBaseStation;
}
function addEndUser(){
    const newEndUser = document.createElement('span');
    newEndUser.classList.add('font-awesome-icon','fas','fa-solid','fa-mobile');
    newEndUser.addEventListener('mousedown', startDrag);
    newEndUser.addEventListener('click', selectDevice);
    document.getElementById('icon-tray').appendChild(newEndUser);
    return newEndUser;
}

async function control(action) {
    try {
        const response = await fetch('/control/' + action, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })

        if (!response.ok) {
            console.warn('Network response was not ok ' + response.statusText);
        }
        else {
            const data = await response.json();
            console.log(data);
        }

    } catch (error) {
        console.error(error)
    }
}
