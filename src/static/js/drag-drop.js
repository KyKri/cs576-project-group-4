const icons = document.querySelectorAll('.font-awesome-icon');
const canvas = document.getElementById('simulation');

icons.forEach(icon => {
    icon.addEventListener('mousedown', startDrag);
});

draggedIcon = null;
lastSelectedIcon = null;

function startDrag(event){
    event.stopPropagation();
    draggedIcon = this;

    canvas.addEventListener('mousemove', dragMove);
    document.addEventListener('mouseup', releaseDrag);
}

function dragMove(event){
    if(draggedIcon){
        const rect = canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY; //- rect.top;

        draggedIcon.style.position = 'absolute';
        draggedIcon.style.left = `${x}px`;
        draggedIcon.style.top = `${y}px`;
    }
}

function releaseDrag(event){
    draggedIcon = null;
    canvas.removeEventListener('mousemove', dragMove);
}

function selectDevice(event){
    lastSelectedIcon = this;
    $('.font-awesome-icon').removeClass('selected');
    lastSelectedIcon.classList.add('selected');

    deviceType = "placeholder";
    if (lastSelectedIcon.classList.contains('fa-tower-cell')){
        deviceType = "Base Station";
    }
    else if (lastSelectedIcon.classList.contains('fa-mobile')){
        deviceType = "End User";
    }

    //hide default details text
    document.getElementById('details-default').style.display = 'none';
    document.getElementById('details-device').innerHTML = `
    <p>${deviceType}</p>
    <ul>
        <li>IP Address: {{device_selected.ip}}</li>
    </ul>
    <button onclick="event.preventDefault(); removeDevice();">
        Delete
    </button>`;
}

function removeDevice(event){
    lastSelectedIcon.remove();
    document.getElementById('details-device').innerHTML = "";
    document.getElementById('details-default').style.display = 'initial';
}

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

/*
document.addEventListener('DOMContentLoaded', function() {
    const icons = document.querySelectorAll('.font-awesome-icon');
    const canvas = document.getElementById('simulation');

    let draggedIcon = null;

    icons.forEach(icon => {
        icon.addEventListener('mousedown', startDrag);
    });

    canvas.addEventListener('mouseup', endDrag);
    canvas.addEventListener('mousemove', drag);

    function startDrag(event) {
        event.stopPropagation();
        draggedIcon = this;
    }

    function endDrag() {
        draggedIcon = null;
    }

    function drag(event) {
        if (draggedIcon) {
            const rect = canvas.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;

            draggedIcon.style.position = 'absolute';
            draggedIcon.style.left = `${x}px`;
            draggedIcon.style.top = `${y}px`;
        }
    }

    // Example: Create icons on the canvas
    function createIcon(x, y) {
        const icon = document.createElement('span');
        icon.className = 'font-awesome-icon fas fa-camera';
        icon.style.left = `${x}px`;
        icon.style.top = `${y}px`;
        canvas.appendChild(icon);
    }

    // Example: Create icons on the canvas at specific positions
    //createIcon(50, 50);
    //createIcon(150, 150);
});
*/