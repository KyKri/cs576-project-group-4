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

        updateCanvas();
    }
}

function releaseDrag(event){
    if(draggedIcon){ updateCanvas(); }
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
    
    //API CALL NEEDED: retrieve relevant data about device
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

    //API CALL NEEDED: removing a selected device

    updateCanvas();
}