async function initBaseStation(x, y) {
    const res = await fetch('/init/basestation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ x, y })
    });

    if (!res.ok) {
        throw new Error('Failed to create base station: ' + res.statusText);
    }
    return res.json(); // returns the Python dict as JS object
}

async function initUserEquipment(x, y) {
    const res = await fetch('/init/userequipment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ x, y })
    });

    if (!res.ok) {
        throw new Error('Failed to create UE: ' + res.statusText);
    }
    return res.json();
}

async function getBaseStation(id){
    const res = await fetch(`/get/basestation/${id}`, {});
    return res.json();
}

async function getUserEquipment(id){
    const res = await fetch(`/get/userequipment/${id}`, {});
    return res.json();
}

async function updateBaseStation(id, { x, y, on }) {
  const res = await fetch(`/update/basestation/${id}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ x, y, on })
  });
  return res.json();
}

async function updateUserEquipment(id, { x, y, change_ip }) {
  const res = await fetch(`/update/userequipment/${id}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ x, y, change_ip })
  });
  return res.json();
}

async function updateEveryUserEquipment() {
    for (const ue of UEList){
        await getUserEquipment(ue.id).then(result => {
            UEList[result.user_equipment.id] = result.user_equipment;
        });
    }
    return UEList;
}

async function checkUEActivePackets(id){
    const res = await fetch(`/check/userequipment/${id}`, {});
    return res.json();
}

async function getUEBaseStationStatus(id){
    const res = await fetch(`/check/link/${id}`, {});
    return res.json();
}

function simulationStatus(){
    UEList.forEach(function(ue, index){
        checkUEActivePackets(ue.id).then(result => {
            //console.log(result);
            UEList[result.id].up_packets = result.up_packets;
            UEList[result.id].down_packets = result.down_packets;
        }).then(result => {
            updateCanvas();
        });
    });
    
    //exit early if no icon is selected
    if(lastSelectedIcon == null){return;}
    const { deviceType, id } = extractIDNumber(lastSelectedIcon.id);

    if(deviceType == "UserEquipment"){
        const BSid = UEList[id].bs;
        if (BSid >= 0){ //check if UE is connected to a valid base station
            getUEBaseStationStatus(id).then(result => {
                //console.log(result);
                writeLinkDetails(result);
            })
        }
    }
}