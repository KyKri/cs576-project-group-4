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

function drawCircle(ctx, x, y, r){
    //gradient
    const gradient = ctx.createRadialGradient(x, y, 0, x, y, r);
    gradient.addColorStop(0, 'rgba(255, 0, 0, 0.3)'); 
    gradient.addColorStop(1, 'rgba(255, 0, 0, 0)');
    ctx.fillStyle = gradient;
    ctx.fillRect(x-r, y-r, 2*r, 2*r);

    return [x, y];
}

//global variable for animating dashed line offset of UE links
let linkOffset = 0;
let dash = 5;

function drawDoubleLines(ctx, startX, startY, endX, endY, up_packets, down_packets){
    const offset = 2;
    const angle = Math.atan2(endY - startY, endX - startX);

    const offsetX = offset * Math.sin(angle);
    const offsetY = offset * -Math.cos(angle);

    const startXa = startX - offsetX;
    const startYa = startY - offsetY;
    const endXa = endX - offsetX;
    const endYa = endY - offsetY;
    const startXb = startX + offsetX;
    const startYb = startY + offsetY;
    const endXb = endX + offsetX;
    const endYb = endY + offsetY;

    ctx.setLineDash([dash, 2]);
    ctx.lineDashOffset = linkOffset;

    //station to user
    ctx.strokeStyle = "red";
    if(down_packets > 0){ctx.strokeStyle = "white";}
    ctx.beginPath();
    ctx.moveTo(startXa, startYa);
    ctx.lineTo(endXa, endYa);
    ctx.stroke();

    //user to station
    ctx.strokeStyle = "red";
    if(up_packets > 0){ctx.strokeStyle = "white";}
    ctx.beginPath();
    ctx.moveTo(endXb, endYb);
    ctx.lineTo(startXb, startYb);
    ctx.stroke();
}

//function for animating dashed line offset of UE links
function march() {
  linkOffset++;
  if (linkOffset > dash+1) {linkOffset = 0;}
  updateCanvas();
  setTimeout(march, 20);
}
//initiate animation
window.onload = function(){
    march();
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
        drawCircle(ctx, x, y, 80);
    });

    //draw lines connectiong end users connecting to every associated base station
    endUsersOnCanvas.each(function(i, element){
        const user = getElementCoordinates(element);
        const userId = extractIDNumber(element.id).id;
        const stationId = UEList[userId].bs;
        if(stationId < 0){return true;}//no connection is no valid base station id
        const station = getElementCoordinates(document.getElementById("BaseStation_" + stationId));
        //console.log("UserEquipment_" + userId, "BaseStation_" + stationId);

        drawDoubleLines(ctx, user.x, user.y, station.x, station.y, 
            UEList[userId].up_packets, UEList[userId].down_packets);

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
