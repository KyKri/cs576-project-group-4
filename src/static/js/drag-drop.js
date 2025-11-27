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
        const y = event.clientY - rect.top;

        draggedIcon.style.position = 'absolute';
        draggedIcon.style.left = `${x}px`;
        draggedIcon.style.top = `${y}px`;

        updateCanvas();
    }
}

function releaseDrag(event){
    if(draggedIcon){ 
        //get final coordinates
        const { x, y } = getElementCoordinates(draggedIcon);
        //check if the device being dragged is new or not (i.e. already active)
        if(draggedIcon.classList.contains('active')){
            let { deviceType, id } = extractIDNumber(draggedIcon.id);
            if(deviceType == "BaseStation"){
                onStatus = BSList[id].on; //use current onStatus
                updateBaseStation(id, {x: x, y: y, on: onStatus}).then(result => {
                    console.log(result);
                    BSList[result.base_station.id] = result.base_station;
                }).then(result => {updateCanvas();});
            }
            else if(deviceType == "UserEquipment"){
                //change_ip set to False by default for now
                updateUserEquipment(id, {x: x, y: y, change_ip: false}).then(result => {
                    console.log(result);
                    UEList[result.user_equipment.id] = result.user_equipment;
                }).then(result => {
                    updateCanvas();
                });
            }
        }
        else{
            //save the icon for after asynchronus functions run
            const lastIcon = draggedIcon;
            let id = "";
            
            if(draggedIcon.classList.contains('fa-tower-cell')){
                try {
                    initBaseStation(x, y).then(result => {
                        console.log(result);
                        id = "BaseStation_" + result.base_station.id;
                        lastIcon.id = id;
                        BSList[result.base_station.id] = result.base_station;
                        //once successfully created, set BS to active
                        lastIcon.classList.add('active'); 
                    }).then(result => {updateCanvas();});
                } catch (err) { console.log(err); }
            }
            else if(draggedIcon.classList.contains('fa-mobile')){
                try {
                    initUserEquipment(x, y).then(result => {
                        console.log(result);
                        id = "UserEquipment_" + result.user_equipment.id;
                        lastIcon.id = id;
                        UEList[result.user_equipment.id] = result.user_equipment;
                        //once successfully created, set UE to active
                        lastIcon.classList.add('active');
                    }).then(result => {updateCanvas();});
                } catch (err) { console.log(err); }
            }
        }
    }

    draggedIcon = null;
    canvas.removeEventListener('mousemove', dragMove);
}

function selectDevice(event){
    lastSelectedIcon = this;
    //ignore rest of code if the selected icon isn't active yet
    if(!lastSelectedIcon.classList.contains('active')){return;}

    //toggle selected class
    $('.font-awesome-icon').removeClass('selected');
    lastSelectedIcon.classList.add('selected');

    deviceId = lastSelectedIcon.id;
    const { deviceType, id } = extractIDNumber(deviceId);

    //hide default details text
    document.getElementById('details-default').style.display = 'none';
    
    if(deviceType == "BaseStation"){
        try {
            getBaseStation(id).then(result => {
                //console.log(result);
                BSList[result.base_station.id] = result.base_station;
                document.getElementById('details-device').innerHTML = `
                <p>Base Station ${id}</p>
                <ul>
                    <li>Status: ${result.base_station.on}</li>
                    <li>Link Quality: </li>
                </ul>
                <button onclick="event.preventDefault(); removeDevice();">
                    Delete
                </button>`;
            });
        } catch (err) { console.log(err); }
    }
    else if(deviceType == "UserEquipment"){
        try {
            getUserEquipment(id).then(result => {
                //console.log(result);
                UEList[result.user_equipment.id] = result.user_equipment;
                document.getElementById('details-device').innerHTML = `
                <p>User Equipment ${id}</p>
                <ul>
                    <li>IP Address: ${result.user_equipment.ip}</li>
                    <li>Connected Base Station ID: ${result.user_equipment.bs}</li>
                </ul>
                <button onclick="event.preventDefault(); removeDevice();">
                    Delete
                </button>`;
            });
        } catch (err) { console.log(err); }
    }
}

function removeDevice(event){
    lastSelectedIcon.remove();
    document.getElementById('details-device').innerHTML = "";
    document.getElementById('details-default').style.display = 'initial';

    //API CALL NEEDED: removing a selected device

    updateCanvas();
}