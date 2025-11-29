function getCanvasDetails(){
    const canvas = document.getElementById('simulation');
    const rect = canvas.getBoundingClientRect();
    const xOffset = rect.left;
    const yOffset = rect.top;

    return { canvas, xOffset, yOffset };
}

function getElementDetails(element){
    const xElement = element.getBoundingClientRect().x;
    const yElement = element.getBoundingClientRect().y;
    const widthOffset = (element.getBoundingClientRect().width)/2
    const heightOffset = (element.getBoundingClientRect().height)/2 

    return { xElement, yElement, widthOffset, heightOffset };
}

function getElementCoordinates(element){
    const { canvas, xOffset, yOffset } = getCanvasDetails();
    const { xElement, yElement, widthOffset, heightOffset } = getElementDetails(element);
    const x = xElement - xOffset + widthOffset;
    const y = yElement - yOffset + heightOffset;
    return {x, y};
}

function drawCircle(x, y, r){
    const canvas = document.getElementById('simulation');
    const ctx = canvas.getContext("2d");

    //circle
    /*
    ctx.beginPath();
    ctx.arc(x, y, r, 0, 2 * Math.PI);
    ctx.strokeStyle = "white";
    ctx.stroke();
    */

    //gradient
    const gradient = ctx.createRadialGradient(x, y, 0, x, y, r);
    gradient.addColorStop(0, 'rgba(255, 0, 0, 0.3)'); 
    gradient.addColorStop(1, 'rgba(255, 0, 0, 0)');
    ctx.fillStyle = gradient;
    ctx.fillRect(x-r, y-r, 2*r, 2*r);

    return [x, y];
}

function updateCanvas(){
    const { canvas, xOffset, yOffset } = getCanvasDetails();
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    //select only base stations
    baseStationsOnCanvas = $('.font-awesome-icon.fa-tower-cell').filter(function(){
        return $(this).css('position') === 'absolute';
    });
    //select only active end users
    endUsersOnCanvas = $('.font-awesome-icon.fa-mobile.active').filter(function(){
        return $(this).css('position') === 'absolute';
    });

    //draw ranges for all base stations
    baseStationsOnCanvas.each(function(index, element){
        if(element.classList.contains('off')){return true;} //skip base station if it has been toggled off

        const { x, y } = getElementCoordinates(element);
        drawCircle(x, y, 80);
    });

    //draw lines connectiong end users connecting to every associated base station
    endUsersOnCanvas.each(function(i, element){
        const user = getElementCoordinates(element);
        const userId = extractIDNumber(element.id).id;
        const stationId = UEList[userId].bs;
        if(stationId < 0){return true;}
        const station = getElementCoordinates(document.getElementById("BaseStation_" + stationId));
        //console.log("UserEquipment_" + userId, "BaseStation_" + stationId);

        //if distance needs to be checked
        const distance = Math.hypot(user.x - station.x, user.y - station.y);

        ctx.strokeStyle = "red";
        ctx.beginPath();
        ctx.moveTo(user.x, user.y);
        ctx.lineTo(station.x, station.y);
        ctx.stroke();

        //baseStationsOnCanvas.each(function(j, element2){})
    });
}

//load base stations and user equipment on canvas if they already exist (upon window refresh)
/*
window.onload = function(){
    BSList.forEach(function(bs, index){
        console.log(bs);
        let bsElement = addBaseStation();
        const { canvas, xOffset, yOffset } = getCanvasDetails();
        const { xElement, yElement, widthOffset, heightOffset } = getElementDetails(bsElement);
        bsElement.style.left = `${bs.x + xOffset - widthOffset}px`;
        bsElement.style.top = `${bs.y + yOffset - heightOffset}px`;
        bsElement.classList.add('active');
        bsElement.id = "BaseStation_" + bs.id;
    });
}
*/
