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
    const res = await fetch(`/get/basestation/${id}`, {
        method: 'POST'
    });
    return res.json();
}

async function getUserEquipment(id){
    const res = await fetch(`/get/userequipment/${id}`, {
        method: 'POST'
    });
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